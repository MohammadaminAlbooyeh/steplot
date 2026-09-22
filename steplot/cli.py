"""Command-line interface for steplot — inspect and export saved runs."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from .display import display_run
from .export import to_html, to_mermaid
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

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
