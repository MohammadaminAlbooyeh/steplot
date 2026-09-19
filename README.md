# steplot

Lightweight agent step tracker with decorator and logging support.

`steplot` helps you visualize and persist the execution flow of your AI agents,
scripts, or any multi-step pipeline. Wrap functions with `@track`, emit log
events with `log_event`, and render a tree of steps to the terminal or to a
JSON file.

## Features

- `@track` decorator -- wraps any function in a timed `Step`.
- `run_context` / `step_context` -- context managers for nesting.
- `log_event` -- emit structured events into the current step.
- `display_run` -- pretty-print a run tree to the terminal.
- `save_run` / `load_run` -- persist runs as JSON.

## Installation

```bash
pip install -e .
```

## Quick start

```python
from steplot import track, run_context, display_run

@track
def research(topic: str) -> str:
    return f"papers about {topic}"

@track
def summarize(papers: str) -> str:
    return papers.upper()

with run_context("my-agent") as run:
    papers = research("transformers")
    summary = summarize(papers)

display_run(run)
```

Output:

```
╔══ Run: my-agent  [0.02s] ═══
║
║  ├─ research  [0.01s]
║  └─ summarize  [0.00s]
╚════════════════════════════╝
```

## Nested steps

```python
from steplot import run_context, step_context

with run_context("pipeline") as run:
    with step_context("fetch"):
        ...
    with step_context("process"):
        with step_context("validate"):
            with step_context("score"):
                ...
```

## Persisting runs

```python
from steplot import save_run, load_run

save_run(run, "steplot/runs/run-1.json")
loaded = load_run("steplot/runs/run-1.json")
```

## API reference

### `track`

```python
@track
def my_step(): ...

@track(step_name="custom", capture_args=True)
def another_step(x, y): ...
```

### `run_context`, `step_context`

Context managers that create and automatically finish a `Run` or `Step`.

### `log_event`

```python
import logging
from steplot import log_event

log_event(logging.INFO, "processing item", item_id=42)
```

### `display_run`

Prints a tree of steps and events to stdout.

## License

MIT