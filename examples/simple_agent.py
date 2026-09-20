"""Simple example demonstrating steplot with a fake agent."""

import asyncio
import logging

from steplot import display_run, log_event, run_context, save_run, step_context, track


@track
async def fetch_data(query: str) -> dict:
    await asyncio.sleep(0.1)
    return {"result": f"data for {query}"}


@track
async def process_data(data: dict) -> str:
    await asyncio.sleep(0.1)
    if not data:
        raise ValueError("empty data")
    return f"processed: {data['result']}"


async def main():
    with run_context("simple-agent", agent="demo") as run:
        with step_context("fetch"):
            log_event(logging.INFO, "fetching data", query="test query")
            data = await fetch_data("test query")
        with step_context("process"):
            log_event(logging.INFO, "processing data")
            result = await process_data(data)
            print(f"agent result: {result}")

    display_run(run)
    save_run(run, "steplot/runs/example-run.json")


asyncio.run(main())
