"""Simple example demonstrating steplot with a fake agent."""

import asyncio

from steplot import track, display_run, save_run
from steplot.tracker import _current_run
from steplot.models import Run


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
    # Create a run explicitly so we can access it after steps complete
    run = Run()
    token = _current_run.set(run)
    try:
        data = await fetch_data("test query")
        result = await process_data(data)
        print(f"agent result: {result}")
    finally:
        _current_run.reset(token)

    display_run(run)
    save_run(run)


asyncio.run(main())