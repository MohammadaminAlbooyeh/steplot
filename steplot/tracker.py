"""Core tracking logic — @track, run_context/step_context, and log_event."""

from __future__ import annotations

import contextvars
import functools
import inspect
import logging
import traceback as traceback_module
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from steplot.models import Event, Run, Step

# Module-level current run and current step, stored in ContextVars for async-safety
_current_run: ContextVar[Run | None] = ContextVar("current_run", default=None)
_current_step: ContextVar[Step | None] = ContextVar("current_step", default=None)

# Logger integration
_logger = logging.getLogger("steplot")

# Global kill switch — when False, @track/log_event/step_context become no-ops
# that just call through to the wrapped function, with no Step/Event recorded.
_enabled: bool = True

# Captured-value hygiene: cap on repr length and keys/callback for redaction.
_max_repr_len: int | None = None
_redact_keys: set[str] = set()
_redact_fn: Callable[[str, Any], Any] | None = None

# Listeners notified every time a Step finishes (success, failure, or skip).
_step_listeners: list[Callable[[Step], None]] = []


class StepSkipped(Exception):  # noqa: N818 - control-flow signal, not an error
    """Raise inside a tracked step or ``step_context`` to mark it skipped.

    The step is recorded with ``StepStatus.SKIPPED`` and the exception is
    swallowed rather than propagated — this is a deliberate control-flow
    signal (e.g. "cache hit, nothing to do"), not a failure.

    Example:
        @track
        def maybe_fetch(key):
            if cache.has(key):
                raise StepSkipped("cache hit")
            return fetch(key)
    """


def set_enabled(enabled: bool) -> None:
    """Globally enable or disable step tracking.

    When disabled, ``@track`` calls the wrapped function directly (no Step is
    created), ``step_context`` yields a disconnected Step without registering
    it on the run, and ``log_event`` is a no-op. Useful for turning tracking
    off in production without removing decorators.
    """
    global _enabled
    _enabled = enabled


def is_enabled() -> bool:
    """Return whether step tracking is currently enabled."""
    return _enabled


def set_max_repr_len(n: int | None) -> None:
    """Cap the repr() length of captured step input/output.

    When set, any captured argument, kwarg, or return value whose ``repr()``
    exceeds ``n`` characters is replaced with a truncated placeholder string.
    Pass None (the default) to capture values uncapped.
    """
    global _max_repr_len
    _max_repr_len = n


def set_redact_keys(keys: Any) -> None:
    """Replace the set of kwarg names redacted from captured step input.

    Any kwarg whose name is in ``keys`` is replaced with ``"***redacted***"``
    before being stored on the Step. Positional args are not covered, since
    they carry no name to match against.
    """
    global _redact_keys
    _redact_keys = set(keys)


def set_redact_fn(fn: Callable[[str, Any], Any] | None) -> None:
    """Set a callback applied to every captured kwarg before storage.

    ``fn(key, value)`` returns the value to store (return ``value`` unchanged
    to keep it). Runs after ``_redact_keys`` substitution. Pass None to clear.
    """
    global _redact_fn
    _redact_fn = fn


def _redact_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for key, value in kwargs.items():
        if key in _redact_keys:
            value = "***redacted***"
        elif _redact_fn is not None:
            value = _redact_fn(key, value)
        result[key] = value
    return result


def _truncate(value: Any) -> Any:
    if _max_repr_len is None:
        return value
    r = repr(value)
    if len(r) <= _max_repr_len:
        return value
    omitted = len(r) - _max_repr_len
    return f"{r[:_max_repr_len]}... ({omitted} more chars truncated)"


def _capture_input(args: tuple, kwargs: dict) -> dict[str, Any]:
    captured_kwargs = _redact_kwargs(kwargs)
    return {
        "args": [_truncate(a) for a in args],
        "kwargs": {k: _truncate(v) for k, v in captured_kwargs.items()},
    }


def add_step_listener(fn: Callable[[Step], None]) -> None:
    """Register a callback invoked every time a Step finishes.

    Used to build live/streaming views (see ``display.live_run_context``) or
    to append finished steps to a log as they happen. Listener exceptions are
    swallowed so a broken listener never breaks tracking.
    """
    _step_listeners.append(fn)


def remove_step_listener(fn: Callable[[Step], None]) -> None:
    """Unregister a callback previously passed to ``add_step_listener``."""
    if fn in _step_listeners:
        _step_listeners.remove(fn)


def _notify_step_finished(step: Step) -> None:
    for fn in list(_step_listeners):
        try:
            fn(step)
        except Exception:  # noqa: BLE001 - a listener must never break tracking
            _logger.exception("steplot: step listener raised")


def with_current_context(fn: Callable) -> Callable:
    """Wrap ``fn`` so it runs with the current run/step context propagated.

    ``ContextVar``s (used to track the active run/step) don't cross raw
    ``threading.Thread`` boundaries on their own — a function started via
    ``threading.Thread(target=fn)`` sees no active run even if one is active
    on the calling thread. Wrap the target with this helper to carry the
    calling thread's context into the new thread.

    Example:
        with run_context("pipeline") as run:
            t = threading.Thread(target=with_current_context(worker))
            t.start()
            t.join()
    """
    ctx = contextvars.copy_context()

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return ctx.run(fn, *args, **kwargs)

    return wrapper


def get_current_run() -> Run | None:
    """Return the active Run, or None if no run is active."""
    return _current_run.get()


def get_current_step() -> Step | None:
    """Return the active Step, or None if no step context is active."""
    return _current_step.get()


def reset() -> None:
    """Reset the global tracking state (useful between tests or runs)."""
    _current_run.set(None)
    _current_step.set(None)


@contextmanager
def run_context(name: str = "run", **metadata: Any) -> Iterator[Run]:
    """Context manager that creates and finishes a Run.

    The run is exposed via the ``run`` returned by the context; it is also made
    the current run so that ``@track`` and ``log_event`` calls inside the block
    are recorded on it.

    Args:
        name: Human-readable name for the run.
        **metadata: Arbitrary key/value metadata attached to the run.

    Example:
        with run_context("my-agent", agent="research") as run:
            do_work()
        display_run(run)
    """
    previous_run = _current_run.get()
    previous_step = _current_step.get()
    run = Run(name=name, metadata=metadata)
    run_token = _current_run.set(run)
    step_token = _current_step.set(None)
    try:
        yield run
    finally:
        run.finish()
        _current_run.reset(run_token)
        _current_run.set(previous_run)
        _current_step.reset(step_token)
        _current_step.set(previous_step)


@contextmanager
def step_context(name: str) -> Iterator[Step]:
    """Context manager that creates and finishes a Step, nesting automatically.

    When used inside another step (either via ``@track`` or a parent
    ``step_context``), the new step becomes a child of the current step.

    Args:
        name: Human-readable name for the step.

    Example:
        with run_context("pipeline") as run:
            with step_context("fetch"):
                ...
            with step_context("process"):
                with step_context("validate"):
                    ...
    """
    if not _enabled:
        yield Step(name=name)
        return

    run, run_token = _ensure_run()
    step = Step(name=name)

    parent = _current_step.get()
    if parent is not None:
        parent.children.append(step)
    else:
        run.steps.append(step)

    previous_step = _current_step.get()
    step_token = _current_step.set(step)
    try:
        yield step
    except StepSkipped as exc:
        step.skip(str(exc) or None)
    except Exception as exc:  # noqa: BLE001 - always record and re-raise
        step.fail(repr(exc), traceback=traceback_module.format_exc())
        raise
    finally:
        if step.ended_at is None:
            step.succeed()
        _notify_step_finished(step)
        _current_step.reset(step_token)
        _current_step.set(previous_step)
        if run_token is not None:
            run.finish()
            _current_run.reset(run_token)


def log_event(level: int, message: str, **data: Any) -> Event | None:
    """Emit a structured event into the current step.

    If a step context is active the event is stored on that step; otherwise it
    is stored on the current run. When no run exists at all the event is only
    passed through to the ``steplot`` logger.

    Example:
        import logging
        log_event(logging.INFO, "processing item", item_id=42)

    Returns:
        The created :class:`~steplot.models.Event`, or None if no run existed.
    """
    _logger.log(level, message)
    if not _enabled:
        return None
    run = _current_run.get()
    step = _current_step.get()
    if step is not None:
        return step.add_event(level, message, **data)
    if run is not None:
        return run.add_event(level, message, **data)
    return None


def track(
    func: Callable | None = None,
    *,
    step_name: str | None = None,
    capture_args: bool = True,
) -> Callable:
    """Decorator that wraps a function in a Step and records its execution.

    Works with both sync and async functions.

    Args:
        step_name: Override the step name (defaults to the function's __name__).
        capture_args: When True (default), record the positional and keyword
            arguments as the step's input. Set to False to skip capturing.

    Usage:
        @track
        def my_step():
            ...

        @track(step_name="custom")
        async def another_step(x, y):
            ...

        @track(capture_args=False)
        def secret_step(x):
            ...
    """

    def decorator(fn: Callable) -> Callable:
        name = step_name or fn.__name__

        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await _run_tracked_async(fn, name, args, kwargs, capture_args)

            return async_wrapper

        @functools.wraps(fn)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            return _run_tracked_sync(fn, name, args, kwargs, capture_args)

        return sync_wrapper

    if func is not None and callable(func):
        # Used as @track without arguments
        return decorator(func)
    return decorator


def _ensure_run() -> tuple[Run, Any | None]:
    """Return the current run, creating one if needed.

    Returns (run, token) where token is non-None if a run was created here.
    """
    run = _current_run.get()
    if run is None:
        run = Run()
        token = _current_run.set(run)
        return run, token
    return run, None


def _append_step(step: Step) -> None:
    """Attach a step to the current run, nesting it under the active step if any."""
    parent = _current_step.get()
    if parent is not None:
        parent.children.append(step)
    else:
        run = _current_run.get()
        if run is not None:
            run.steps.append(step)


def _run_tracked_sync(fn: Callable, name: str, args: tuple, kwargs: dict, capture_args: bool) -> Any:
    if not _enabled:
        return fn(*args, **kwargs)

    run, token = _ensure_run()
    step = Step(
        name=name,
        input=_capture_input(args, kwargs) if capture_args else None,
    )
    _append_step(step)
    _emit(logging.INFO, f"→ start: {name}")
    try:
        result = fn(*args, **kwargs)
        step.succeed(output=_truncate(result))
        _emit(logging.INFO, f"✓ done: {name}")
        return result
    except StepSkipped as exc:
        step.skip(str(exc) or None)
        _emit(logging.INFO, f"⤼ skipped: {name}")
        return None
    except Exception as exc:
        step.fail(repr(exc), traceback=traceback_module.format_exc())
        _emit(logging.ERROR, f"✗ error: {name} — {exc!r}")
        raise
    finally:
        _notify_step_finished(step)
        if token is not None:
            run.finish()
            _current_run.reset(token)


async def _run_tracked_async(fn: Callable, name: str, args: tuple, kwargs: dict, capture_args: bool) -> Any:
    if not _enabled:
        return await fn(*args, **kwargs)

    run, token = _ensure_run()
    step = Step(
        name=name,
        input=_capture_input(args, kwargs) if capture_args else None,
    )
    _append_step(step)
    _emit(logging.INFO, f"→ start: {name}")
    try:
        result = await fn(*args, **kwargs)
        step.succeed(output=_truncate(result))
        _emit(logging.INFO, f"✓ done: {name}")
        return result
    except StepSkipped as exc:
        step.skip(str(exc) or None)
        _emit(logging.INFO, f"⤼ skipped: {name}")
        return None
    except Exception as exc:
        step.fail(repr(exc), traceback=traceback_module.format_exc())
        _emit(logging.ERROR, f"✗ error: {name} — {exc!r}")
        raise
    finally:
        _notify_step_finished(step)
        if token is not None:
            run.finish()
            _current_run.reset(token)


def _emit(level: int, message: str) -> None:
    """Internal helper to log without raising if no run exists."""
    _logger.log(level, message)
