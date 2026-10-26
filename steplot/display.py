"""Terminal display for steplot runs — renders the run tree to stdout."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from .models import Event, Run, Step, StepStatus


def _status_annotation(step: Step) -> str:
    """Return a short status suffix for a step when it isn't a clean success."""
    if step.status == StepStatus.FAILED:
        return "  ✗"
    if step.status == StepStatus.RUNNING:
        return "  ..."
    if step.status == StepStatus.SKIPPED:
        return "  ⤼"
    return ""


def _format_duration(seconds: float | None) -> str:
    return f"[{seconds:.2f}s]" if seconds is not None else ""


def _render_step(step: Step, prefix: str, is_last: bool, lines: list[str]) -> None:
    """Recursively append a step and its events/children to ``lines``."""
    branch = "└─ " if is_last else "├─ "
    line = f"{prefix}{branch}{step.name}  {_format_duration(step.duration)}{_status_annotation(step)}"
    lines.append(line)

    # Continuation prefix for events and children beneath this branch.
    child_prefix = prefix + ("   " if is_last else "│  ")

    for event in step.events:
        _render_event(event, child_prefix, lines)

    for i, child in enumerate(step.children):
        _render_step(child, child_prefix, i == len(step.children) - 1, lines)

    if step.error:
        lines.append(f"{child_prefix}  error: {step.error}")
    if step.traceback:
        for tb_line in step.traceback.rstrip().splitlines():
            lines.append(f"{child_prefix}  {tb_line}")
    if step.skip_reason:
        lines.append(f"{child_prefix}  skipped: {step.skip_reason}")


def _render_event(event: Event, prefix: str, lines: list[str]) -> None:
    lines.append(f"{prefix}  • {event.message}")


def _render_summary(run: Run, lines: list[str]) -> None:
    """Append a summary footer (step counts, total/slowest duration) to ``lines``."""
    summary = run.summary()
    lines.append("")
    lines.append(
        f"  Σ {summary['total_steps']} steps"
        f"  ✓{summary['success']}"
        f"  ✗{summary['failed']}"
        f"  …{summary['running']}"
        f"  ⤼{summary['skipped']}"
        f"  total={summary['total_duration']:.2f}s"
    )
    if summary["slowest_step"] is not None:
        name, duration = summary["slowest_step"]
        lines.append(f"  slowest: {name}  [{duration:.2f}s]")
    if summary["total_cost"] is not None or summary["total_tokens"] is not None:
        parts = []
        if summary["total_cost"] is not None:
            parts.append(f"cost=${summary['total_cost']:.4f}")
        if summary["total_tokens"] is not None:
            parts.append(f"tokens={summary['total_tokens']}")
        lines.append("  " + "  ".join(parts))


def display_run(run: Run, show_summary: bool = False) -> None:
    """Pretty-print a Run tree to stdout.

    Renders the run name, total duration, and each step (including nested
    children and structured events) as a boxed tree.

    Args:
        run: The Run to render.
        show_summary: When True, append a summary footer with step counts,
            total duration, and the slowest step (see ``Run.summary()``).
    """
    title = f"Run: {run.name}"
    duration = _format_duration(run.duration)
    if duration:
        title += f"  {duration}"

    lines: list[str] = []

    for i, step in enumerate(run.steps):
        _render_step(step, "  ", i == len(run.steps) - 1, lines)

    for event in run.events:
        lines.append(f"  • {event.message}")

    if show_summary:
        _render_summary(run, lines)

    top = f"╔══ {title} ═══"
    width = max([len(line) for line in lines] + [len(top) - 2])
    bottom = "╚" + "═" * width + "╝"

    print(top)
    print("║")
    for line in lines:
        print(f"║{line}")
    print(bottom)


def _status_glyph(step: Step) -> str:
    return {
        StepStatus.SUCCESS: "✓",
        StepStatus.FAILED: "✗",
        StepStatus.RUNNING: "…",
        StepStatus.SKIPPED: "⤼",
    }.get(step.status, "?")


@contextmanager
def live_run_context(name: str = "run", **metadata: Any) -> Iterator[Run]:
    """Like ``run_context``, but prints each step to stdout as it finishes.

    Use this instead of ``run_context`` + a final ``display_run`` call when
    watching a long-running agent interactively — each step is printed the
    moment it completes rather than only once the whole run is done.

    Example:
        with live_run_context("agent") as run:
            research("transformers")
            summarize(...)
    """
    from .tracker import add_step_listener, remove_step_listener, run_context

    def _on_step(step: Step) -> None:
        duration = _format_duration(step.duration)
        print(f"  {_status_glyph(step)} {step.name}  {duration}")

    print(f"▶ run: {name}")
    with run_context(name, **metadata) as run:
        add_step_listener(_on_step)
        try:
            yield run
        finally:
            remove_step_listener(_on_step)
    duration = _format_duration(run.duration)
    print(f"■ run finished  {duration}")
