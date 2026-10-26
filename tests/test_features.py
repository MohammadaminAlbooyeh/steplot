"""Tests for capture hygiene (truncation/redaction), skipped steps, step
listeners/live display, run comparison, and JSONL storage."""

from __future__ import annotations

import json

import pytest
from steplot import (
    StepSkipped,
    add_step_listener,
    diff_runs,
    jsonl_log,
    load_jsonl,
    remove_step_listener,
    run_context,
    set_enabled,
    set_max_repr_len,
    set_redact_fn,
    set_redact_keys,
    step_context,
    track,
)
from steplot.display import live_run_context
from steplot.models import StepStatus


@pytest.fixture(autouse=True)
def _reset_capture_settings():
    yield
    set_max_repr_len(None)
    set_redact_keys([])
    set_redact_fn(None)
    set_enabled(True)


class TestTruncation:
    def test_long_output_is_truncated(self):
        set_max_repr_len(10)

        @track
        def big():
            return "x" * 1000

        with run_context("r") as run:
            big()

        assert isinstance(run.steps[0].output, str)
        assert len(run.steps[0].output) < 1000
        assert "truncated" in run.steps[0].output

    def test_short_output_is_untouched(self):
        set_max_repr_len(100)

        @track
        def small():
            return "hi"

        with run_context("r") as run:
            small()

        assert run.steps[0].output == "hi"

    def test_no_cap_by_default(self):
        @track
        def big():
            return "x" * 1000

        with run_context("r") as run:
            big()

        assert run.steps[0].output == "x" * 1000


class TestRedaction:
    def test_redact_keys_masks_matching_kwargs(self):
        set_redact_keys(["password"])

        @track
        def login(user, password):
            return "ok"

        with run_context("r") as run:
            login("alice", password="secret")

        step = run.steps[0]
        assert step.input["kwargs"]["password"] == "***redacted***"
        assert step.input["args"] == ["alice"]

    def test_redact_fn_applies_to_kwargs(self):
        set_redact_fn(lambda k, v: v.upper() if k == "token" else v)

        @track
        def call(token):
            return None

        with run_context("r") as run:
            call(token="abc")

        assert run.steps[0].input["kwargs"]["token"] == "ABC"


class TestSkipped:
    def test_track_sync_skip(self):
        @track
        def maybe():
            raise StepSkipped("cache hit")

        with run_context("r") as run:
            result = maybe()

        assert result is None
        step = run.steps[0]
        assert step.status == StepStatus.SKIPPED
        assert step.skip_reason == "cache hit"

    def test_step_context_skip(self):
        with run_context("r") as run, step_context("inner"):
            raise StepSkipped("nothing to do")

        step = run.steps[0]
        assert step.status == StepStatus.SKIPPED
        assert step.skip_reason == "nothing to do"

    def test_skip_without_reason(self):
        @track
        def maybe():
            raise StepSkipped()

        with run_context("r") as run:
            maybe()

        assert run.steps[0].skip_reason is None

    def test_summary_counts_skipped(self):
        @track
        def maybe():
            raise StepSkipped("skip")

        with run_context("r") as run:
            maybe()

        assert run.summary()["skipped"] == 1


class TestStepListeners:
    def test_listener_called_on_success_and_failure(self):
        seen: list = []
        add_step_listener(seen.append)
        try:

            @track
            def ok():
                return 1

            @track
            def bad():
                raise ValueError("x")

            with run_context("r"):
                ok()
                with pytest.raises(ValueError):
                    bad()
        finally:
            remove_step_listener(seen.append)

        assert [s.name for s in seen] == ["ok", "bad"]
        assert seen[0].status == StepStatus.SUCCESS
        assert seen[1].status == StepStatus.FAILED

    def test_broken_listener_does_not_break_tracking(self):
        def bad_listener(step):
            raise RuntimeError("listener exploded")

        add_step_listener(bad_listener)
        try:

            @track
            def work():
                return 1

            with run_context("r") as run:
                result = work()
        finally:
            remove_step_listener(bad_listener)

        assert result == 1
        assert run.steps[0].status == StepStatus.SUCCESS

    def test_live_run_context_prints_each_step(self, capsys):
        @track
        def a():
            return 1

        with live_run_context("live-demo") as run:
            a()

        out = capsys.readouterr().out
        assert "live-demo" in out
        assert "a" in out
        assert run.steps[0].status == StepStatus.SUCCESS


class TestDiffRuns:
    def test_new_failure_detected(self):
        with run_context("baseline") as baseline:

            @track
            def step_a():
                return 1

            step_a()

        with run_context("candidate") as candidate:

            @track
            def step_a():
                raise ValueError("boom")

            with pytest.raises(ValueError):
                step_a()

        diff = diff_runs(baseline, candidate)
        assert diff["new_failures"] == ["step_a"]
        assert diff["fixed"] == []

    def test_fixed_failure_detected(self):
        with run_context("baseline") as baseline:

            @track
            def step_a():
                raise ValueError("boom")

            with pytest.raises(ValueError):
                step_a()

        with run_context("candidate") as candidate:

            @track
            def step_a():
                return 1

            step_a()

        diff = diff_runs(baseline, candidate)
        assert diff["fixed"] == ["step_a"]
        assert diff["new_failures"] == []

    def test_added_and_removed_steps(self):
        with run_context("baseline") as baseline:
            baseline.add_step("only_in_baseline").succeed()

        with run_context("candidate") as candidate:
            candidate.add_step("only_in_candidate").succeed()

        diff = diff_runs(baseline, candidate)
        assert diff["by_name"]["only_in_baseline"]["status"] == "removed"
        assert diff["by_name"]["only_in_candidate"]["status"] == "added"

    def test_duration_delta_for_common_step(self):
        with run_context("baseline") as baseline:
            s = baseline.add_step("shared")
            s.finish(status=StepStatus.SUCCESS)
        with run_context("candidate") as candidate:
            s = candidate.add_step("shared")
            s.finish(status=StepStatus.SUCCESS)

        diff = diff_runs(baseline, candidate)
        assert diff["by_name"]["shared"]["status"] == "common"
        assert "duration_delta" in diff["by_name"]["shared"]


class TestJsonlLog:
    def test_steps_appended_as_they_finish(self, tmp_path):
        path = tmp_path / "run.jsonl"

        with run_context("r") as run, jsonl_log(str(path)):

            @track
            def a():
                return 1

            @track
            def b():
                return 2

            a()
            b()

        lines = path.read_text().splitlines()
        assert len(lines) == 2
        names = [json.loads(line)["name"] for line in lines]
        assert names == ["a", "b"]

        loaded = load_jsonl(str(path))
        assert [s.name for s in loaded] == ["a", "b"]
        assert run.steps[0].id == loaded[0].id

    def test_survives_a_failure_mid_run(self, tmp_path):
        path = tmp_path / "run.jsonl"

        with run_context("r"), jsonl_log(str(path)):

            @track
            def a():
                return 1

            @track
            def bad():
                raise ValueError("boom")

            a()
            with pytest.raises(ValueError):
                bad()

        loaded = load_jsonl(str(path))
        assert [s.name for s in loaded] == ["a", "bad"]
        assert loaded[1].status == StepStatus.FAILED
