"""Data models for steplot — Step, Run, and supporting types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class StepStatus(Enum):
    """Lifecycle status of a Step."""

    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

    def __str__(self) -> str:
        return self.value


@dataclass
class Step:
    """A named, timed unit of work within a Run.

    Attributes:
        name: Human-readable step name (often the function name).
        status: Current lifecycle status.
        input: Optional input value passed to the step.
        output: Optional output value produced by the step.
        error: Error message if the step failed.
        started_at: Wall-clock time the step started.
        ended_at: Wall-clock time the step finished (None while running).
    """

    name: str
    status: StepStatus = StepStatus.RUNNING
    input: Any = None
    output: Any = None
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    id: str = field(default_factory=lambda: uuid4().hex)

    @property
    def duration(self) -> Optional[float]:
        """Duration in seconds, or None while still running."""
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()

    def finish(self, status: Optional[StepStatus] = None, **kwargs: Any) -> None:
        """Mark the step as finished with the given status and optional fields."""
        if self.ended_at is None:
            self.ended_at = datetime.now()
        if status is not None:
            self.status = status
        for key, value in kwargs.items():
            setattr(self, key, value)

    def succeed(self, output: Any = None) -> None:
        self.finish(status=StepStatus.SUCCESS, output=output)

    def fail(self, error: str) -> None:
        self.finish(status=StepStatus.FAILED, error=error)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "input": self.input,
            "output": self.output,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Step":
        return cls(
            id=data.get("id", uuid4().hex),
            name=data["name"],
            status=StepStatus(data.get("status", StepStatus.RUNNING.value)),
            input=data.get("input"),
            output=data.get("output"),
            error=data.get("error"),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else datetime.now(),
            ended_at=datetime.fromisoformat(data["ended_at"]) if data.get("ended_at") else None,
        )


@dataclass
class Run:
    """Top-level container for a tracked execution."""

    id: str = field(default_factory=lambda: uuid4().hex)
    name: str = "run"
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    steps: list[Step] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[float]:
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()

    def add_step(self, name: str, **kwargs: Any) -> Step:
        step = Step(name=name, **kwargs)
        self.steps.append(step)
        return step

    def finish(self) -> None:
        if self.ended_at is None:
            self.ended_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "steps": [s.to_dict() for s in self.steps],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Run":
        return cls(
            id=data.get("id", uuid4().hex),
            name=data.get("name", "run"),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else datetime.now(),
            ended_at=datetime.fromisoformat(data["ended_at"]) if data.get("ended_at") else None,
            steps=[Step.from_dict(s) for s in data.get("steps", [])],
            metadata=data.get("metadata", {}),
        )