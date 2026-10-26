"""Compare steplot runs — useful for spotting regressions between agent evals."""

from __future__ import annotations

import glob as glob_module
from typing import Any

from .models import Run, StepStatus
from .storage import load_run


def diff_runs(baseline: Run, candidate: Run) -> dict[str, Any]:
    """Compare ``candidate`` against ``baseline`` by step name.

    Args:
        baseline: The reference run (e.g. the last known-good run).
        candidate: The run being evaluated against the baseline.

    Returns:
        A dict with:
            by_name: mapping of step name -> {"status", "baseline", "candidate",
                "duration_delta"}, where "status" is "added", "removed", or
                "common" (present in both; "duration_delta" is only set then).
            new_failures: step names that failed in ``candidate`` but not
                ``baseline``.
            fixed: step names that failed in ``baseline`` but not ``candidate``.
            total_duration_delta: candidate's total duration minus baseline's.
    """
    baseline_by_name = baseline.summary()["by_name"]
    candidate_by_name = candidate.summary()["by_name"]

    by_name: dict[str, Any] = {}
    for step_name in sorted(set(baseline_by_name) | set(candidate_by_name)):
        base_entry = baseline_by_name.get(step_name)
        cand_entry = candidate_by_name.get(step_name)
        if base_entry is None:
            by_name[step_name] = {"status": "added", "baseline": None, "candidate": cand_entry}
        elif cand_entry is None:
            by_name[step_name] = {"status": "removed", "baseline": base_entry, "candidate": None}
        else:
            by_name[step_name] = {
                "status": "common",
                "baseline": base_entry,
                "candidate": cand_entry,
                "duration_delta": cand_entry["total_duration"] - base_entry["total_duration"],
            }

    baseline_failed = {s.name for s in baseline._iter_steps() if s.status == StepStatus.FAILED}
    candidate_failed = {s.name for s in candidate._iter_steps() if s.status == StepStatus.FAILED}

    return {
        "by_name": by_name,
        "new_failures": sorted(candidate_failed - baseline_failed),
        "fixed": sorted(baseline_failed - candidate_failed),
        "total_duration_delta": candidate.summary()["total_duration"] - baseline.summary()["total_duration"],
    }


def _percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile (0-100) over ``values`` (must be non-empty)."""
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, round(pct / 100 * (len(ordered) - 1))))
    return ordered[k]


def summarize_runs(paths: str | list[str]) -> dict[str, Any]:
    """Aggregate per-step-name duration stats across many saved runs.

    Useful for spotting which steps are typically slow (or flaky) across a
    batch of eval runs, rather than looking at one run at a time.

    Args:
        paths: A glob pattern (e.g. ``"runs/*.json"``), or an explicit list of
            run JSON file paths saved with ``save_run``.

    Returns:
        A dict with:
            run_count: number of run files loaded.
            by_name: mapping of step name -> {"count", "success", "failed",
                "p50", "p95", "min", "max", "mean"} (duration stats in
                seconds, over every occurrence of that step name across all
                loaded runs; steps still running are excluded).
    """
    file_paths = sorted(glob_module.glob(paths)) if isinstance(paths, str) else list(paths)

    runs = [load_run(p) for p in file_paths]

    durations_by_name: dict[str, list[float]] = {}
    counts_by_name: dict[str, dict[str, int]] = {}

    for run in runs:
        for step in run._iter_steps():
            counts = counts_by_name.setdefault(step.name, {"count": 0, "success": 0, "failed": 0})
            counts["count"] += 1
            if step.status == StepStatus.SUCCESS:
                counts["success"] += 1
            elif step.status == StepStatus.FAILED:
                counts["failed"] += 1
            if step.duration is not None:
                durations_by_name.setdefault(step.name, []).append(step.duration)

    by_name: dict[str, Any] = {}
    for name, counts in counts_by_name.items():
        durations = durations_by_name.get(name, [])
        entry: dict[str, Any] = dict(counts)
        if durations:
            entry["p50"] = _percentile(durations, 50)
            entry["p95"] = _percentile(durations, 95)
            entry["min"] = min(durations)
            entry["max"] = max(durations)
            entry["mean"] = sum(durations) / len(durations)
        else:
            entry["p50"] = entry["p95"] = entry["min"] = entry["max"] = entry["mean"] = None
        by_name[name] = entry

    return {"run_count": len(runs), "by_name": by_name}
