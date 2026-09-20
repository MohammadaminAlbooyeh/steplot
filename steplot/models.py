"""Data models for steplot — Event, Step, Run, and supporting types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class StepStatus(Enum):
    """Lifecycle status of a Step."""

    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

    def __str__(self) -> str:
        return self.value


@dataclass
class Event:
    """A structured event emitted into a Step or Run.

    Attributes:
        level: Logging level (see Python's ``logging`` module).
        message: Human-readable message for the event.
        data: Arbitrary structured key/value payload attached to the event.
        timestamp: Wall-clock time the event was emitted.
        id: Stable identifier for the event.
    """

    level: int
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: uuid4().hex)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "level": self.level,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Event:
        return cls(
            id=data.get("id", uuid4().hex),
            level=data.get("level", 20),
            message=data["message"],
            data=data.get("data", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(),
        )


@dataclass
class Step:
    """A named, timed unit of work within a Run.

    Steps form a tree: each step may contain nested ``children`` steps as well as
    structured ``events``.

    Attributes:
        name: Human-readable step name (often the function name).
        status: Current lifecycle status.
        input: Optional input value passed to the step.
        output: Optional output value produced by the step.
        error: Error message if the step failed.
        started_at: Wall-clock time the step started.
        ended_at: Wall-clock time the step finished (None while running).
        children: Nested child steps.
        events: Structured events emitted while the step ran.
    """

    name: str
    status: StepStatus = StepStatus.RUNNING
    input: Any = None
    output: Any = None
    error: str | None = None
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: datetime | None = None
    id: str = field(default_factory=lambda: uuid4().hex)
    children: list[Step] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)

    @property
    def duration(self) -> float | None:
        """Duration in seconds, or None while still running."""
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()

    def finish(self, status: StepStatus | None = None, **kwargs: Any) -> None:
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

    def add_child(self, name: str, **kwargs: Any) -> Step:
        """Create and register a nested child step."""
        child = Step(name=name, **kwargs)
        self.children.append(child)
        return child

    def add_event(self, level: int, message: str, **data: Any) -> Event:
        """Record a structured event on this step."""
        event = Event(level=level, message=message, data=data)
        self.events.append(event)
        return event

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
            "children": [c.to_dict() for c in self.children],
            "events": [e.to_dict() for e in self.events],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Step:
        return cls(
            id=data.get("id", uuid4().hex),
            name=data["name"],
            status=StepStatus(data.get("status", StepStatus.RUNNING.value)),
            input=data.get("input"),
            output=data.get("output"),
            error=data.get("error"),
            started_at=datetime.fromisoformat(data["started_at"])
            if data.get("started_at")
            else datetime.now(),
            ended_at=datetime.fromisoformat(data["ended_at"]) if data.get("ended_at") else None,
            children=[Step.from_dict(c) for c in data.get("children", [])],
            events=[Event.from_dict(e) for e in data.get("events", [])],
        )


@dataclass
class Run:
    """Top-level container for a tracked execution."""

    id: str = field(default_factory=lambda: uuid4().hex)
    name: str = "run"
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: datetime | None = None
    steps: list[Step] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)

    @property
    def duration(self) -> float | None:
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()

    def add_step(self, name: str, **kwargs: Any) -> Step:
        step = Step(name=name, **kwargs)
        self.steps.append(step)
        return step

    def add_event(self, level: int, message: str, **data: Any) -> Event:
        """Record a run-level structured event (not attached to any step)."""
        event = Event(level=level, message=message, data=data)
        self.events.append(event)
        return event

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
            "events": [e.to_dict() for e in self.events],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Run:
        return cls(
            id=data.get("id", uuid4().hex),
            name=data.get("name", "run"),
            started_at=datetime.fromisoformat(data["started_at"])
            if data.get("started_at")
            else datetime.now(),
            ended_at=datetime.fromisoformat(data["ended_at"]) if data.get("ended_at") else None,
            steps=[Step.from_dict(s) for s in data.get("steps", [])],
            metadata=data.get("metadata", {}),
            events=[Event.from_dict(e) for e in data.get("events", [])],
        )
