"""Example: export a run to a Mermaid flowchart and a standalone HTML file."""

import asyncio
import logging

from steplot import display_run, log_event, run_context, step_context, to_html, to_mermaid, track


@track
async def fetch_data(query: str) -> dict:
    await asyncio.sleep(0.1)
    return {"result": f"data for {query}"}


@track
async def process_data(data: dict) -> str:
    await asyncio.sleep(0.1)
    return f"processed: {data['result']}"


async def main():
    with run_context("export-demo", agent="demo") as run:
        with step_context("fetch"):
            log_event(logging.INFO, "fetching data", query="test query")
            data = await fetch_data("test query")
        with step_context("process"):
            result = await process_data(data)
            print(f"agent result: {result}")

    display_run(run)

    print(to_mermaid(run))

    html_path = to_html(run, "steplot/runs/export-demo.html")
    print(f"HTML report written to: {html_path}")


asyncio.run(main())
