"""Core tracking logic — the @track decorator and current-run context."""

from __future__ import annotations

import functools
import inspect
import logging
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Callable, Optional

from steplot.models import Run, Step, StepStatus

# Module-level current run, stored in a ContextVar for async-safety
_current_run: ContextVar[Optional[Run]] = ContextVar("current_run", default=None)

# Logger integration
_logger = logging.getLogger("steplot")


def get_current_run() -> Optional[Run]:
    """Return the active Run, or None if no run is active."""
    return _current_run.get()


def reset() -> None:
    """Reset the global tracking state (useful between tests or runs)."""
    _current_run.set(None)


@contextmanager
def run_context(name: str = "run", **metadata: Any):
    """Context manager that creates and finishes a Run.

    The finished run remains the "current" run so callers can display or
    persist it after the context exits. Use ``reset()`` to clear it.
    """
    previous_run = _current_run.get()
    run = Run(name=name, metadata=metadata)
    token = _current_run.set(run)
    try:
        yield run
    finally:
        run.finish()
        _current_run.reset(token)
        _current_run.set(previous_run)


def track(func: Optional[Callable] = None, *, step_name: Optional[str] = None) -> Callable:
    """Decorator that wraps a function in a Step and records its execution.

    Works with both sync and async functions.

    Args:
        step_name: Override the step name (defaults to the function's __name__).

    Usage:
        @track
        def my_step():
            ...

        @track(step_name="custom")
        async def another_step(x, y):
            ...
    """

    def decorator(fn: Callable) -> Callable:
        name = step_name or fn.__name__

        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await _run_tracked_async(fn, name, args, kwargs)

            return async_wrapper

        @functools.wraps(fn)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            return _run_tracked_sync(fn, name, args, kwargs)

        return sync_wrapper

    if func is not None and callable(func):
        # Used as @track without arguments
        return decorator(func)
    return decorator


def _ensure_run() -> tuple[Run, Optional[Any]]:
    """Return the current run, creating one if needed.

    Returns (run, token) where token is non-None if a run was created here.
    """
    run = _current_run.get()
    if run is None:
        run = Run()
        token = _current_run.set(run)
        return run, token
    return run, None


def _run_tracked_sync(fn: Callable, name: str, args: tuple, kwargs: dict) -> Any:
    run, token = _ensure_run()
    step = Step(
        name=name,
        input={"args": list(args), "kwargs": kwargs},
    )
    run.steps.append(step)
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


async def _run_tracked_async(fn: Callable, name: str, args: tuple, kwargs: dict) -> Any:
    run, token = _ensure_run()
    step = Step(
        name=name,
        input={"args": list(args), "kwargs": kwargs},
    )
    run.steps.append(step)
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