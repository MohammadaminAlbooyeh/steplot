"""Storage for steplot runs — JSON-based."""

import json
from pathlib import Path
from datetime import datetime

from .models import Run, StepStatus


def _serialize(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, StepStatus):
        return obj.value
    return str(obj)


def save_run(run: Run, path: str = ".steplot") -> None:
    """Save a Run to a JSON file under the given directory.

    Args:
        run: The Run to persist.
        path: Directory to save into (created if missing).
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    file = dir_path / f"{run.id}.json"
    data = {
        "id": run.id,
        "started_at": run.started_at,
        "steps": [
            {
                "name": s.name,
                "status": s.status,
                "input": s.input,
                "output": s.output,
                "error": s.error,
                "duration": s.duration,
            }
            for s in run.steps
        ],
    }
    file.write_text(json.dumps(data, default=_serialize, indent=2))


def load_run(path: str) -> Run:
    """Load a Run from a JSON file path."""
    data = json.loads(Path(path).read_text())
    from .models import Step

    steps = []
    for s in data.get("steps", []):
        steps.append(
            Step(
                name=s["name"],
                status=StepStatus(s["status"]),
                input=s.get("input"),
                output=s.get("output"),
                error=s.get("error"),
            )
        )
    return Run(
        id=data.get("id"),
        started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else datetime.now(),
        steps=steps,
    )