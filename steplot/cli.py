"""Command-line interface for steplot — inspect and export saved runs."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Sequence

from .compare import summarize_runs
from .display import _format_duration, _status_glyph, display_run
from .export import to_html, to_mermaid
from .models import Step
from .storage import load_run


def _cmd_show(args: argparse.Namespace) -> int:
    run = load_run(args.path)
    display_run(run, show_summary=args.summary)
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    run = load_run(args.path)
    if args.format == "mermaid":
        output = to_mermaid(run)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
        else:
            print(output, end="")
    else:
        out_path = args.output or "steplot.html"
        written = to_html(run, out_path)
        print(f"wrote {written}")
    return 0


def _cmd_watch(args: argparse.Namespace) -> int:
    print(f"▶ watching {args.path} (ctrl-c to stop)")
    with open(args.path, encoding="utf-8") as f:
        f.seek(0, 2)  # start at end of file — only show new steps
        try:
            while True:
                line = f.readline()
                if not line:
                    time.sleep(args.interval)
                    continue
                line = line.strip()
                if not line:
                    continue
                step = Step.from_dict(json.loads(line))
                duration = _format_duration(step.duration)
                print(f"  {_status_glyph(step)} {step.name}  {duration}")
        except KeyboardInterrupt:
            print("\n■ stopped watching")
    return 0


def _cmd_stats(args: argparse.Namespace) -> int:
    summary = summarize_runs(args.paths)
    print(f"Σ {summary['run_count']} runs")
    for name, entry in sorted(summary["by_name"].items()):
        p50 = f"{entry['p50']:.2f}s" if entry["p50"] is not None else "-"
        p95 = f"{entry['p95']:.2f}s" if entry["p95"] is not None else "-"
        print(
            f"  {name}  count={entry['count']}  success={entry['success']}  failed={entry['failed']}"
            f"  p50={p50}  p95={p95}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="steplot", description="Inspect and export steplot runs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    show = subparsers.add_parser("show", help="Print a saved run as a terminal tree.")
    show.add_argument("path", help="Path to a run JSON file saved with save_run().")
    show.add_argument("--summary", action="store_true", help="Append a step-count/duration summary footer.")
    show.set_defaults(func=_cmd_show)

    export = subparsers.add_parser("export", help="Export a saved run to Mermaid or HTML.")
    export.add_argument("path", help="Path to a run JSON file saved with save_run().")
    export.add_argument("--format", choices=["mermaid", "html"], default="mermaid", help="Output format.")
    export.add_argument(
        "-o", "--output", help="Output file path. Defaults to stdout (mermaid) or steplot.html (html)."
    )
    export.set_defaults(func=_cmd_export)

    watch = subparsers.add_parser("watch", help="Live-tail a jsonl_log() file as steps complete.")
    watch.add_argument("path", help="Path to a file being written by jsonl_log().")
    watch.add_argument(
        "--interval", type=float, default=0.5, help="Polling interval in seconds (default: 0.5)."
    )
    watch.set_defaults(func=_cmd_watch)

    stats = subparsers.add_parser("stats", help="Aggregate per-step duration stats across many saved runs.")
    stats.add_argument("paths", help="Glob pattern matching run JSON files, e.g. 'runs/*.json'.")
    stats.set_defaults(func=_cmd_stats)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
