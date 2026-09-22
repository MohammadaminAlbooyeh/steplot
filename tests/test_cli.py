"""Tests for steplot.cli."""

from pathlib import Path

import pytest
from steplot import run_context, save_run, track
from steplot.cli import main
from steplot.tracker import _current_run, _current_step


@pytest.fixture(autouse=True)
def _reset_state():
    _current_run.set(None)
    _current_step.set(None)
    yield
    _current_run.set(None)
    _current_step.set(None)


@pytest.fixture
def run_file(tmp_path: Path) -> Path:
    @track
    def fetch():
        return "data"

    with run_context("cli-demo") as run:
        fetch()

    path = tmp_path / "run.json"
    save_run(run, str(path))
    return path


def test_show_prints_tree(run_file: Path, capsys):
    exit_code = main(["show", str(run_file)])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "Run: cli-demo" in out
    assert "fetch" in out


def test_show_with_summary_flag(run_file: Path, capsys):
    exit_code = main(["show", str(run_file), "--summary"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "Σ" in out


def test_export_mermaid_to_stdout(run_file: Path, capsys):
    exit_code = main(["export", str(run_file)])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert out.startswith("flowchart TD")
    assert "fetch" in out


def test_export_mermaid_to_file(run_file: Path, tmp_path: Path):
    out_path = tmp_path / "diagram.mmd"
    exit_code = main(["export", str(run_file), "--format", "mermaid", "-o", str(out_path)])

    assert exit_code == 0
    content = out_path.read_text(encoding="utf-8")
    assert content.startswith("flowchart TD")


def test_export_html_to_file(run_file: Path, tmp_path: Path):
    out_path = tmp_path / "report.html"
    exit_code = main(["export", str(run_file), "--format", "html", "-o", str(out_path)])

    assert exit_code == 0
    assert out_path.exists()
    assert "mermaid.min.js" in out_path.read_text(encoding="utf-8")


def test_export_html_default_output(run_file: Path, capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    exit_code = main(["export", str(run_file), "--format", "html"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert (tmp_path / "steplot.html").exists()
    assert "wrote" in out


def test_missing_command_errors():
    with pytest.raises(SystemExit):
        main([])


def test_show_missing_file_raises(tmp_path: Path):
    missing = tmp_path / "nope.json"
    with pytest.raises(FileNotFoundError):
        main(["show", str(missing)])
