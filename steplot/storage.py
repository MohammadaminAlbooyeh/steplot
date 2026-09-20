"""Storage for steplot runs — JSON-based."""

import json
from datetime import datetime
from pathlib import Path

from .models import Run, StepStatus


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
