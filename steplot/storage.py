"""Storage for steplot runs — JSON-based."""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import TextIO

from .models import Run, Step, StepStatus


def _serialize(obj):
    """JSON default serializer for values not natively JSON-serializable."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, StepStatus):
        return obj.value
    return str(obj)


def save_run(run: Run, path: str = ".steplot") -> str:
    """Save a Run to a JSON file.

    The target is interpreted as a file path when it has a file suffix (for
    example ``runs/run-1.json``), and as a directory otherwise. In the
    directory case the file is written as ``{run.id}.json`` inside it. Parent
    directories are created as needed.

    Args:
        run: The Run to persist.
        path: Destination file path (with suffix) or directory.

    Returns:
        The absolute path of the file that was written.
    """
    target = Path(path)
    if target.suffix:
        # Treat as an explicit file path (e.g. "runs/run-1.json").
        target.parent.mkdir(parents=True, exist_ok=True)
        file = target
    else:
        # Treat as a directory; write {run.id}.json inside it.
        target.mkdir(parents=True, exist_ok=True)
        file = target / f"{run.id}.json"

    file.write_text(json.dumps(run.to_dict(), default=_serialize, indent=2))
    return str(file)


def load_run(path: str) -> Run:
    """Load a Run from a JSON file path."""
    data = json.loads(Path(path).read_text())
    return Run.from_dict(data)


@contextmanager
def jsonl_log(path: str) -> Iterator[None]:
    """Append each finished Step to ``path`` as JSON Lines, as it completes.

    Unlike ``save_run`` (which writes the whole run once), this persists
    incrementally — one line per finished step, flushed immediately — so a
    long-running process that crashes mid-run still leaves every step that
    completed before the crash on disk.

    Example:
        with run_context("pipeline") as run, jsonl_log("pipeline.jsonl"):
            do_work()
    """
    from .tracker import add_step_listener, remove_step_listener

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    file: TextIO = target.open("a", encoding="utf-8")

    def _on_step(step: Step) -> None:
        file.write(json.dumps(step.to_dict(), default=_serialize))
        file.write("\n")
        file.flush()

    add_step_listener(_on_step)
    try:
        yield
    finally:
        remove_step_listener(_on_step)
        file.close()


def load_jsonl(path: str) -> list[Step]:
    """Load the Steps previously written by ``jsonl_log`` from ``path``."""
    steps = []
    for line in Path(path).read_text().splitlines():
        if line.strip():
            steps.append(Step.from_dict(json.loads(line)))
    return steps
