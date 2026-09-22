"""Tests for steplot.export — Mermaid and HTML exporters."""

from pathlib import Path

import pytest
from steplot import run_context, step_context, to_html, to_mermaid, track
from steplot.tracker import _current_run, _current_step


@pytest.fixture(autouse=True)
def _reset_state():
    _current_run.set(None)
    _current_step.set(None)
    yield
    _current_run.set(None)
    _current_step.set(None)


def test_to_mermaid_empty_run():
    with run_context("empty") as run:
        pass

    out = to_mermaid(run)
    assert out.startswith("flowchart TD\n")
    assert 'root["Run: empty"]' in out
    assert "%% Edges" not in out


def test_to_mermaid_nodes_and_edges():
    @track
    def fetch():
        return "data"

    with run_context("pipeline") as run:
        fetch()

    out = to_mermaid(run)
    step = run.steps[0]
    node_id = f"N{step.id[:8]}"

    assert f'{node_id}["fetch"]:::sSuccess' in out
    assert f"root --> {node_id}" in out


def test_to_mermaid_nested_steps_edge():
    with run_context("pipeline") as run, step_context("outer"), step_context("inner"):
        pass

    outer = run.steps[0]
    inner = outer.children[0]
    out = to_mermaid(run)

    outer_id = f"N{outer.id[:8]}"
    inner_id = f"N{inner.id[:8]}"
    assert f"root --> {outer_id}" in out
    assert f"{outer_id} --> {inner_id}" in out


def test_to_mermaid_status_colors():
    with run_context("pipeline") as run:
        try:
            with step_context("boom"):
                raise ValueError("nope")
        except ValueError:
            pass

    out = to_mermaid(run)
    assert ":::sFailed" in out
    assert "#ef4444" in out


def test_to_mermaid_escapes_quotes_and_newlines():
    with run_context('weird\nname "run"') as run:
        pass

    out = to_mermaid(run)
    label = out.split('root["Run: ')[1].split('"]')[0]
    assert '"' not in label
    assert "\n" not in label


def test_to_html_writes_file(tmp_path: Path):
    @track
    def step_one():
        return 1

    with run_context("html-demo") as run:
        step_one()

    out_path = tmp_path / "run.html"
    result = to_html(run, str(out_path))

    assert Path(result).exists()
    content = Path(result).read_text(encoding="utf-8")
    assert "mermaid.min.js" in content
    assert "html-demo" in content
    assert "step_one" in content
    assert run.id in content


def test_to_html_returns_absolute_path(tmp_path: Path):
    with run_context("abs-path") as run:
        pass

    result = to_html(run, str(tmp_path / "out.html"))
    assert Path(result).is_absolute()
