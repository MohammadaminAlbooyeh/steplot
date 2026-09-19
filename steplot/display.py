"""Terminal display for steplot runs."""

from .models import Run, StepStatus

ICONS = {
    StepStatus.SUCCESS: "✓",
    StepStatus.FAILED: "✗",
    StepStatus.RUNNING: "...",
}


def display_run(run: Run) -> None:
    """Pretty-print a Run to the terminal."""
    print(f"\nRun ID: {run.id}\n")
    for i, step in enumerate(run.steps, 1):
        icon = ICONS.get(step.status, "?")
        duration = f"({step.duration:.2f}s)" if step.duration else ""
        print(f"  Step {i}: {step.name} {icon} {duration}")
        if step.error:
            print(f"    Error: {step.error}")
            print(f"    Input: {step.input}")
    print()