"""Tests for cost/token tracking on Step and summarize_runs() aggregation."""

from __future__ import annotations

from steplot import run_context, save_run, step_context, summarize_runs, track


class TestUsageTracking:
    def test_add_usage_accumulates(self):
        with run_context("r"), step_context("llm_call") as step:
            step.add_usage(cost=0.01, tokens=100)
            step.add_usage(cost=0.02, tokens=50)

        assert step.cost == 0.03
        assert step.tokens == 150

    def test_summary_rolls_up_cost_and_tokens(self):
        with run_context("r") as run:
            with step_context("a") as a:
                a.add_usage(cost=0.5, tokens=10)
            with step_context("b") as b:
                b.add_usage(cost=1.5, tokens=20)

        summary = run.summary()
        assert summary["total_cost"] == 2.0
        assert summary["total_tokens"] == 30
        assert summary["by_name"]["a"]["total_cost"] == 0.5
        assert summary["by_name"]["b"]["total_tokens"] == 20

    def test_summary_cost_none_when_unused(self):
        with run_context("r") as run, step_context("a"):
            pass

        summary = run.summary()
        assert summary["total_cost"] is None
        assert summary["total_tokens"] is None

    def test_usage_round_trips_through_save_load(self, tmp_path):
        from steplot import load_run

        with run_context("r") as run, step_context("a") as a:
            a.add_usage(cost=0.1, tokens=5)

        path = save_run(run, str(tmp_path))
        loaded = load_run(path)
        assert loaded.steps[0].cost == 0.1
        assert loaded.steps[0].tokens == 5


class TestSummarizeRuns:
    def test_aggregates_across_multiple_runs(self, tmp_path):
        @track
        def work():
            return 1

        for _ in range(3):
            with run_context("r") as run:
                work()
            save_run(run, str(tmp_path))

        summary = summarize_runs(str(tmp_path / "*.json"))
        assert summary["run_count"] == 3
        assert summary["by_name"]["work"]["count"] == 3
        assert summary["by_name"]["work"]["success"] == 3
        assert summary["by_name"]["work"]["p50"] is not None

    def test_accepts_explicit_path_list(self, tmp_path):
        paths = []
        for _ in range(2):
            with run_context("r") as run, step_context("x"):
                pass
            paths.append(save_run(run, str(tmp_path)))

        summary = summarize_runs(paths)
        assert summary["run_count"] == 2
        assert summary["by_name"]["x"]["count"] == 2

    def test_empty_glob_returns_zero_runs(self, tmp_path):
        summary = summarize_runs(str(tmp_path / "*.json"))
        assert summary["run_count"] == 0
        assert summary["by_name"] == {}
