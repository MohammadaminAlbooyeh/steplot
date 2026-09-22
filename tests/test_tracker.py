"""Tests for steplot tracker."""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

import pytest
from steplot import (
    display_run,
    get_current_run,
    get_current_step,
    load_run,
    log_event,
    run_context,
    save_run,
    step_context,
    track,
)
from steplot.models import Run, Step, StepStatus
from steplot.storage import _serialize
from steplot.tracker import _current_run, _current_step


@pytest.fixture(autouse=True)
def _reset_state():
    _current_run.set(None)
    _current_step.set(None)
    yield
    _current_run.set(None)
    _current_step.set(None)


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
        assert run.steps[0].error is not None
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
        run = Run(name="my-run")
        run.add_step("step1").succeed(output="ok")
        step2 = run.add_step("step2")
        step2.fail("an error")
        run.finish()

        display_run(run)
        out = capsys.readouterr().out
        assert "Run: my-run" in out
        assert "step1" in out
        assert "step2" in out
        assert "error: an error" in out
        assert "╔══" in out
        assert "╚" in out

    def test_display_nested_and_events(self, capsys):
        run = Run(name="pipeline")
        run.finish()
        root = run.add_step("process")
        root.add_child("validate").succeed()
        root.add_event(logging.INFO, "validated ok", n=3)

        display_run(run)
        out = capsys.readouterr().out
        assert "process" in out
        assert "validate" in out
        # The event message should be rendered beneath the step.
        assert "validated ok" in out

    def test_display_run_with_summary(self, capsys):
        run = Run(name="my-run")
        run.add_step("step1").succeed(output="ok")
        run.add_step("step2").fail("an error")
        run.finish()

        display_run(run, show_summary=True)
        out = capsys.readouterr().out
        assert "Σ 2 steps" in out
        assert "✓1" in out
        assert "✗1" in out
        assert "slowest:" in out

    def test_display_run_without_summary_by_default(self, capsys):
        run = Run(name="my-run")
        run.add_step("step1").succeed()
        run.finish()

        display_run(run)
        out = capsys.readouterr().out
        assert "Σ" not in out


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


class TestModelHierarchy:
    def test_step_children_and_events(self):
        s = Step(name="root")
        child = s.add_child("child")
        assert child.name == "child"
        assert s.children == [child]
        event = s.add_event(logging.INFO, "hello", n=1)
        assert s.events == [event]
        assert event.data == {"n": 1}
        assert event.message == "hello"

    def test_run_events(self):
        r = Run()
        event = r.add_event(logging.INFO, "run event", key="value")
        assert r.events == [event]
        assert event.data == {"key": "value"}

    def test_step_roundtrip_nested(self):
        s = Step(name="root")
        s.add_child("child").succeed(output="works")
        s.add_event(logging.INFO, "evt", x=1)
        restored = Step.from_dict(s.to_dict())
        assert restored.id == s.id
        assert restored.name == "root"
        assert restored.children[0].name == "child"
        assert restored.children[0].output == "works"
        assert restored.events[0].message == "evt"
        assert restored.events[0].data == {"x": 1}


class TestRunContext:
    def test_creates_and_finishes_run(self):
        with run_context("my-agent", agent="demo") as run:
            assert get_current_run() is run
            run.add_step("step1").succeed()
            assert run.ended_at is None
        assert run.ended_at is not None
        assert run.name == "my-agent"
        assert run.metadata == {"agent": "demo"}
        # After the context exits nothing should remain current at the top level.
        assert get_current_run() is None

    def test_records_tracked_steps(self):
        @track
        def work():
            return 1

        with run_context("agent") as run:
            assert work() == 1

        assert len(run.steps) == 1
        assert run.steps[0].name == "work"
        assert run.steps[0].status == StepStatus.SUCCESS

    def test_run_context_survives_exception(self):
        with pytest.raises(RuntimeError), run_context("agent"):
            raise RuntimeError("boom")
        # Even on failure the run is finished and cleaned up.


class TestStepContext:
    def test_nested_hierarchy(self):
        with run_context("pipeline") as run:
            with step_context("a"):
                with step_context("a1"):
                    pass
                with step_context("a2"):
                    pass
            with step_context("b"):
                pass

        assert [s.name for s in run.steps] == ["a", "b"]
        assert [c.name for c in run.steps[0].children] == ["a1", "a2"]
        assert get_current_step() is None

    def test_step_finished_after_exit(self):
        with run_context("pipeline"):
            with step_context("a"):
                a = get_current_step()
                assert a is not None
                assert a.ended_at is None
            assert a is not None
            assert a.ended_at is not None
            assert a.status == StepStatus.SUCCESS

    def test_exception_marks_step_failed(self):
        with run_context("pipeline") as run:
            with pytest.raises(ValueError), step_context("bad"):
                raise ValueError("nope")
            assert run.steps[0].status == StepStatus.FAILED
            assert run.steps[0].error is not None
            assert "ValueError" in run.steps[0].error
            # Context must be cleaned up so later steps are not nested.
            with step_context("good"):
                pass
        assert run.steps[1].name == "good"

    def test_tracked_function_nests_under_step(self):
        @track
        def inner():
            return "in"

        with run_context("agent") as run, step_context("outer"):
            inner()

        assert len(run.steps) == 1
        assert run.steps[0].name == "outer"
        assert run.steps[0].children[0].name == "inner"


class TestLogEvent:
    def test_without_run_returns_none(self):
        assert log_event(logging.INFO, "nowhere") is None

    def test_attaches_to_run(self):
        with run_context("agent") as run:
            event = log_event(logging.INFO, "fetching", url="/x")
        assert event is not None
        assert event.message == "fetching"
        assert event.data == {"url": "/x"}
        assert run.events == [event]

    def test_attaches_to_current_step(self):
        with run_context("agent") as run, step_context("fetch"):
            event = log_event(logging.INFO, "item", item_id=42)
        assert run.events == []
        assert run.steps[0].events == [event]
        assert event is not None
        assert event.data == {"item_id": 42}


class TestCaptureArgs:
    def test_capture_args_false(self):
        @track(capture_args=False)
        def hidden(x, y):
            return x + y

        run = Run()
        token = _current_run.set(run)
        try:
            assert hidden(1, 2) == 3
        finally:
            _current_run.reset(token)
        assert run.steps[0].input is None

    def test_capture_args_default_true(self):
        @track
        def visible(x, y):
            return x + y

        run = Run()
        token = _current_run.set(run)
        try:
            visible(1, 2)
        finally:
            _current_run.reset(token)
        assert run.steps[0].input == {"args": [1, 2], "kwargs": {}}

    def test_capture_args_false_async(self):
        @track(capture_args=False)
        async def hidden(x):
            return x

        run = Run()
        token = _current_run.set(run)
        try:
            asyncio.run(hidden(1))
        finally:
            _current_run.reset(token)
        assert run.steps[0].input is None


class TestSerializationFidelity:
    def test_full_roundtrip(self, tmp_path):
        run = Run(name="full-run")
        run.metadata = {"agent": "demo", "seed": 7}
        s1 = run.add_step("build")
        s1.add_child("compile").succeed()
        s1.succeed(output="ok")
        s1.add_event(logging.INFO, "built", n=1)
        run.add_step("test").fail("bad")
        run.finish()

        path = tmp_path / "full.json"
        save_run(run, str(path))
        loaded = load_run(str(path))

        assert loaded.id == run.id
        assert loaded.name == run.name
        assert loaded.metadata == run.metadata
        assert loaded.started_at == run.started_at
        assert loaded.ended_at == run.ended_at
        assert len(loaded.steps) == 2
        assert loaded.steps[0].id == s1.id
        assert loaded.steps[0].status == StepStatus.SUCCESS
        assert loaded.steps[0].children[0].name == "compile"
        assert loaded.steps[0].events[0].message == "built"
        assert loaded.steps[1].status == StepStatus.FAILED
        assert loaded.steps[1].error == "bad"

    def test_save_file_path_roundtrip(self, tmp_path):
        run = Run(name="file-run")
        run.add_step("s").succeed()
        run.finish()

        target = tmp_path / "runs" / "run-1.json"
        written = save_run(run, str(target))
        assert Path(written).exists()

        loaded = load_run(str(target))
        assert loaded.id == run.id
        assert loaded.name == "file-run"


class TestDocumentedExamples:
    def test_readme_imports(self):
        import steplot
        from steplot import (  # noqa: F401
            display_run,
            load_run,
            log_event,
            run_context,
            save_run,
            step_context,
            track,
        )

        for name in [
            "track",
            "run_context",
            "step_context",
            "log_event",
            "display_run",
            "save_run",
            "load_run",
        ]:
            assert name in steplot.__all__

    def test_quickstart(self, capsys):
        @track
        def research(topic: str) -> str:
            return f"papers about {topic}"

        @track
        def summarize(papers: str) -> str:
            return papers.upper()

        with run_context("my-agent") as run:
            papers = research("transformers")
            summary = summarize(papers)

        assert run.name == "my-agent"
        assert summary == "PAPERS ABOUT TRANSFORMERS"
        assert [s.name for s in run.steps] == ["research", "summarize"]

        display_run(run)
        out = capsys.readouterr().out
        assert "Run: my-agent" in out

    def test_nested_documented_example(self):
        with run_context("pipeline") as run:
            with step_context("fetch"):
                pass
            with step_context("process"), step_context("validate"), step_context("score"):
                pass

        assert [s.name for s in run.steps] == ["fetch", "process"]
        assert run.steps[1].children[0].name == "validate"
        assert run.steps[1].children[0].children[0].name == "score"
        assert get_current_run() is None


class TestAsyncParallel:
    """asyncio.gather runs each coroutine as a Task with its own copy of the
    current context, so ContextVar mutations inside one task must not leak
    into sibling tasks. These tests pin that behavior down.
    """

    def test_parallel_track_calls_create_independent_steps(self):
        @track
        async def work(n: int) -> int:
            await asyncio.sleep(0.03 - n * 0.005)
            return n

        async def main():
            with run_context("parallel") as run:
                results = await asyncio.gather(work(1), work(2), work(3))
            return run, results

        run, results = asyncio.run(main())

        assert results == [1, 2, 3]
        assert [s.name for s in run.steps] == ["work", "work", "work"]
        assert {s.output for s in run.steps} == {1, 2, 3}
        assert all(s.status == StepStatus.SUCCESS for s in run.steps)

    def test_parallel_step_context_nesting_does_not_cross_contaminate(self):
        @track
        async def leaf(n: int) -> int:
            await asyncio.sleep(0.01)
            return n

        async def branch(n: int) -> None:
            with step_context(f"branch-{n}"):
                await asyncio.sleep(0.02 - n * 0.005)
                await leaf(n)

        async def main():
            with run_context("parallel-nested") as run:
                await asyncio.gather(branch(1), branch(2), branch(3))
            return run

        run = asyncio.run(main())

        assert {s.name for s in run.steps} == {"branch-1", "branch-2", "branch-3"}
        for step in run.steps:
            # Each branch's leaf must nest under its own branch, never a sibling's.
            assert [c.name for c in step.children] == ["leaf"]
            assert step.status == StepStatus.SUCCESS

    def test_parallel_failure_does_not_affect_siblings(self):
        @track
        async def maybe_fail(n: int) -> int:
            await asyncio.sleep(0.01)
            if n == 2:
                raise ValueError("boom")
            return n

        async def main():
            with run_context("parallel-failure") as run:
                results = await asyncio.gather(
                    maybe_fail(1), maybe_fail(2), maybe_fail(3), return_exceptions=True
                )
            return run, results

        run, results = asyncio.run(main())

        assert isinstance(results[1], ValueError)
        by_output = {s.output: s.status for s in run.steps if s.status == StepStatus.SUCCESS}
        assert by_output == {1: StepStatus.SUCCESS, 3: StepStatus.SUCCESS}
        failed = [s for s in run.steps if s.status == StepStatus.FAILED]
        assert len(failed) == 1
