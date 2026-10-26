"""steplot — lightweight agent step tracker with decorator and logging support."""

from .compare import diff_runs, summarize_runs
from .display import display_run, live_run_context
from .export import to_html, to_mermaid
from .otel import to_otel_spans
from .storage import jsonl_log, load_jsonl, load_run, save_run
from .tracker import (
    StepSkipped,
    add_step_listener,
    get_current_run,
    get_current_step,
    is_enabled,
    log_event,
    remove_step_listener,
    reset,
    run_context,
    set_enabled,
    set_max_repr_len,
    set_redact_fn,
    set_redact_keys,
    step_context,
    track,
    with_current_context,
)

__all__ = [
    "track",
    "run_context",
    "step_context",
    "log_event",
    "get_current_run",
    "get_current_step",
    "reset",
    "set_enabled",
    "is_enabled",
    "set_max_repr_len",
    "set_redact_keys",
    "set_redact_fn",
    "StepSkipped",
    "add_step_listener",
    "remove_step_listener",
    "with_current_context",
    "display_run",
    "live_run_context",
    "save_run",
    "load_run",
    "jsonl_log",
    "load_jsonl",
    "to_mermaid",
    "to_html",
    "to_otel_spans",
    "diff_runs",
    "summarize_runs",
]

__version__ = "0.1.0"
