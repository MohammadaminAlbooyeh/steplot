"""Tests for Run.summary()."""

import time

from steplot.models import Run


def test_summary_empty_run():
    run = Run(name="empty")
    summary = run.summary()

    assert summary == {
        "total_steps": 0,
        "success": 0,
        "failed": 0,
        "running": 0,
        "total_duration": 0,
        "slowest_step": None,
        "by_name": {},
    }


def test_summary_flat_steps():
    run = Run(name="flat")
    a = run.add_step("a")
    time.sleep(0.01)
    a.succeed()
    b = run.add_step("b")
    time.sleep(0.02)
    b.fail("boom")

    summary = run.summary()

    assert summary["total_steps"] == 2
    assert summary["success"] == 1
    assert summary["failed"] == 1
    assert summary["running"] == 0
    assert summary["total_duration"] > 0
    assert summary["slowest_step"][0] == "b"


def test_summary_nested_steps_counted():
    run = Run(name="nested")
    outer = run.add_step("outer")
    inner = outer.add_child("inner")
    inner.succeed()
    outer.succeed()

    summary = run.summary()

    assert summary["total_steps"] == 2
    assert summary["success"] == 2


def test_summary_running_step_excluded_from_duration():
    run = Run(name="running")
    run.add_step("still-going")  # never finished -> status stays RUNNING

    summary = run.summary()

    assert summary["total_steps"] == 1
    assert summary["running"] == 1
    assert summary["total_duration"] == 0
    assert summary["slowest_step"] is None
    assert summary["by_name"]["still-going"]["count"] == 1
    assert summary["by_name"]["still-going"]["total_duration"] == 0.0


def test_summary_by_name_groups_repeated_step_names():
    run = Run(name="grouped")
    for _ in range(3):
        step = run.add_step("fetch")
        step.succeed()

    summary = run.summary()

    assert summary["by_name"]["fetch"]["count"] == 3
    assert summary["by_name"]["fetch"]["total_duration"] >= 0
