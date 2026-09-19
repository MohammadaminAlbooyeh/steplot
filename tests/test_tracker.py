"""Tests for steplot tracker."""

import asyncio
import json
import logging
from datetime import datetime

import pytest

from steplot import track, display_run, save_run, load_run, get_current_run
from steplot.models import Run, Step, StepStatus
from steplot.tracker import _current_run
from steplot.storage import _serialize


@pytest.fixture(autouse=True)
def _reset_state():
    _current_run.set(None)
    yield
    _current_run.set(None)


class TestStepStatus:
    def test_values(self):
        assert StepStatus.RUNNING.value == "running"
        assert StepStatus.SUCCESS.value == "success"
        assert StepStatus.FAILED.value == "failed"

    def test_str(self):
        assert str(StepStatus.RUNNING) == "running"


class TestStep:
    def test_defaults(self):
        s = Step(name="test")
        assert s.status == StepStatus.RUNNING
        assert s.input is None
        assert s.output is None
        assert s.error is None
        assert s.ended_at is None

    def test_duration_while_running(self):
        s = Step(name="test")
        assert s.duration is None

    def test_duration_after_finish(self):
        s = Step(name="test")
        s.finish()
        assert s.duration is not None
        assert s.duration >= 0.0

    def test_succeed(self):
        s = Step(name="test")
        s.succeed(output="ok")
        assert s.status == StepStatus.SUCCESS
        assert s.output == "ok"
        assert s.ended_at is not None

    def test_fail(self):
        s = Step(name="test")
        s.fail("boom")
        assert s.status == StepStatus.FAILED
        assert s.error == "boom"

    def test_to_dict(self):
        s = Step(name="test")
        s.succeed(output=42)
        d = s.to_dict()
        assert d["name"] == "test"
        assert d["status"] == "success"
        assert d["output"] == 42


class TestRun:
    def test_defaults(self):
        r = Run()
        assert r.steps == []
        assert r.ended_at is None

    def test_add_step(self):
        r = Run()
        s = r.add_step("step1")
        assert len(r.steps) == 1
        assert s.name == "step1"

    def test_finish(self):
        r = Run()
        assert r.ended_at is None
        r.finish()
        assert r.ended_at is not None


class TestTracker:
    def test_track_sync_success(self):
        @track
        def compute():
            return 99

        run = Run()
        token = _current_run.set(run)
        try:
            assert compute() == 99
        finally:
            _current_run.reset(token)

        assert len(run.steps) == 1
        assert run.steps[0].name == "compute"
        assert run.steps[0].status == StepStatus.SUCCESS
        assert run.steps[0].output == 99
        assert run.steps[0].ended_at is not None

    def test_track_sync_failure(self):
        @track
        def failing():
            raise ValueError("boom")

        run = Run()
        token = _current_run.set(run)
        try:
            with pytest.raises(ValueError):
                failing()
        finally:
            _current_run.reset(token)

        assert run.steps[0].status == StepStatus.FAILED
        assert "ValueError" in run.steps[0].error

    def test_track_custom_name(self):
        @track(step_name="custom-name")
        def f():
            return "ok"

        run = Run()
        token = _current_run.set(run)
        try:
            f()
        finally:
            _current_run.reset(token)

        assert run.steps[0].name == "custom-name"

    def test_track_async_success(self):
        @track
        async def fetch():
            await asyncio.sleep(0.01)
            return {"data": 1}

        run = Run()
        token = _current_run.set(run)
        try:
            result = asyncio.run(fetch())
        finally:
            _current_run.reset(token)

        assert result == {"data": 1}
        assert run.steps[0].status == StepStatus.SUCCESS
        assert run.steps[0].output == {"data": 1}

    def test_track_async_failure(self):
        @track
        async def failing():
            await asyncio.sleep(0.01)
            raise RuntimeError("async boom")

        run = Run()
        token = _current_run.set(run)
        try:
            with pytest.raises(RuntimeError):
                asyncio.run(failing())
        finally:
            _current_run.reset(token)

        assert run.steps[0].status == StepStatus.FAILED

    def test_track_auto_creates_run(self):
        @track
        def standalone():
            return 42

        assert _current_run.get() is None
        result = standalone()

        assert result == 42
        # The run was auto-created and cleaned up after success
        assert _current_run.get() is None

    def test_get_current_run(self):
        assert get_current_run() is None
        run = Run()
        token = _current_run.set(run)
        try:
            assert get_current_run() is run
        finally:
            _current_run.reset(token)
        assert get_current_run() is None


class TestDisplay:
    def test_display_run(self, capsys):
        run = Run()
        run.add_step("step1").succeed(output="ok")
        run.add_step("step2").fail("error")
        run.finish()

        display_run(run)
        out = capsys.readouterr().out
        assert "Run ID:" in out
        assert "step1" in out
        assert "step2" in out
        assert "error" in out


class TestStorage:
    def test_save_and_load(self, tmp_path):
        run = Run()
        run.add_step("step1").succeed(output="ok")
        run.add_step("step2").fail("boom")
        run.finish()

        save_run(run, str(tmp_path))
        files = list(tmp_path.glob("*.json"))
        assert len(files) == 1

        loaded = load_run(str(files[0]))
        assert loaded.id == run.id
        assert len(loaded.steps) == 2
        assert loaded.steps[0].name == "step1"
        assert loaded.steps[0].status == StepStatus.SUCCESS
        assert loaded.steps[1].status == StepStatus.FAILED

    def test_serialize_datetime(self):
        result = _serialize(datetime(2025, 1, 1, 12, 0, 0))
        assert isinstance(result, str)
        assert "2025" in result

    def test_serialize_step_status(self):
        assert _serialize(StepStatus.SUCCESS) == "success"
        assert _serialize(StepStatus.FAILED) == "failed"

    def test_save_creates_directory(self, tmp_path):
        run = Run()
        run.add_step("s").succeed()
        target = tmp_path / "nested" / "dir"
        save_run(run, str(target))
        assert (target / f"{run.id}.json").exists()

    def test_load_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_run(str(tmp_path / "nope.json"))

    def test_roundtrip_json(self, tmp_path):
        run = Run()
        run.add_step("s").succeed(output={"key": "value"})
        run.finish()

        save_run(run, str(tmp_path))
        file = tmp_path / f"{run.id}.json"
        data = json.loads(file.read_text())
        assert data["id"] == run.id
        assert data["steps"][0]["output"] == {"key": "value"}