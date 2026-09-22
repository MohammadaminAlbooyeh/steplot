"""Terminal display for steplot runs — renders the run tree to stdout."""

from __future__ import annotations

from .models import Event, Run, Step, StepStatus


def _status_annotation(step: Step) -> str:
    """Return a short status suffix for a step when it isn't a clean success."""
    if step.status == StepStatus.FAILED:
        return "  ✗"
    if step.status == StepStatus.RUNNING:
        return "  ..."
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
        f"  total={summary['total_duration']:.2f}s"
    )
    if summary["slowest_step"] is not None:
        name, duration = summary["slowest_step"]
        lines.append(f"  slowest: {name}  [{duration:.2f}s]")


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
