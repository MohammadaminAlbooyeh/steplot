"""Core tracking logic — @track, run_context/step_context, and log_event."""

from __future__ import annotations

import functools
import inspect
import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from typing import Any

from steplot.models import Event, Run, Step, StepStatus

# Module-level current run and current step, stored in ContextVars for async-safety
_current_run: ContextVar[Run | None] = ContextVar("current_run", default=None)
_current_step: ContextVar[Step | None] = ContextVar("current_step", default=None)

# Logger integration
_logger = logging.getLogger("steplot")


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
    except Exception as exc:  # noqa: BLE001 - always record and re-raise
        step.fail(repr(exc))
        raise
    finally:
        if step.ended_at is None:
            step.succeed()
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
    run = _current_run.get()
    step = _current_step.get()
    _logger.log(level, message)
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
    run, token = _ensure_run()
    step = Step(
        name=name,
        input={"args": list(args), "kwargs": kwargs} if capture_args else None,
    )
    _append_step(step)
    _emit(logging.INFO, f"→ start: {name}")
    try:
        result = fn(*args, **kwargs)
        step.succeed(output=result)
        _emit(logging.INFO, f"✓ done: {name}")
        return result
    except Exception as exc:
        step.fail(repr(exc))
        _emit(logging.ERROR, f"✗ error: {name} — {exc!r}")
        if token is not None:
            _current_run.reset(token)
        raise
    finally:
        step.ended_at = datetime.now()
        if token is not None and step.status == StepStatus.SUCCESS:
            _current_run.reset(token)


async def _run_tracked_async(fn: Callable, name: str, args: tuple, kwargs: dict, capture_args: bool) -> Any:
    run, token = _ensure_run()
    step = Step(
        name=name,
        input={"args": list(args), "kwargs": kwargs} if capture_args else None,
    )
    _append_step(step)
    _emit(logging.INFO, f"→ start: {name}")
    try:
        result = await fn(*args, **kwargs)
        step.succeed(output=result)
        _emit(logging.INFO, f"✓ done: {name}")
        return result
    except Exception as exc:
        step.fail(repr(exc))
        _emit(logging.ERROR, f"✗ error: {name} — {exc!r}")
        if token is not None:
            _current_run.reset(token)
        raise
    finally:
        step.ended_at = datetime.now()
        if token is not None and step.status == StepStatus.SUCCESS:
            _current_run.reset(token)


def _emit(level: int, message: str) -> None:
    """Internal helper to log without raising if no run exists."""
    _logger.log(level, message)
