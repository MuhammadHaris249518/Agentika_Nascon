"""Verify the fastn MCP connection from the command line.

Run from the backend/ folder:
    python -m scripts.verify_fastn                       # connect and list tools
    python -m scripts.verify_fastn --call TOOL --args '{"query": "chevening"}'
"""

import argparse
import asyncio
import json
import sys
import time

from app.core.config import get_settings
from app.integrations.errors import FastnError
from app.integrations.fastn_client import FastnClient


def ok(msg: str) -> None:
    print(f"[ OK ] {msg}")


def fail(err: FastnError) -> int:
    print(f"[FAIL] {err.code}: {err.message}")
    print(f"       Hint: {err.hint}")
    return 1


async def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the fastn MCP gateway connection.")
    parser.add_argument("--call", help="Name of a tool to call after listing tools.")
    parser.add_argument("--args", default="{}", help="JSON arguments for --call.")
    args = parser.parse_args()

    settings = get_settings()
    client = FastnClient(settings)

    print(f"Gateway: {settings.fastn_mcp_url}")
    try:
        client.build_headers()
    except FastnError as exc:
        return fail(exc)
    ok("Configuration present (API key is set)")

    started = time.perf_counter()
    try:
        tools = await client.list_tools()
    except FastnError as exc:
        return fail(exc)
    ok(f"Connected and listed {len(tools)} tool(s) in {time.perf_counter() - started:.2f}s")
    for tool in tools:
        print(f"       - {tool.name}: {tool.description[:80]}")

    if args.call:
        try:
            arguments = json.loads(args.args)
        except json.JSONDecodeError as exc:
            print(f"[FAIL] --args is not valid JSON: {exc}")
            return 2
        if not isinstance(arguments, dict):
            print("[FAIL] --args must be a JSON object, for example '{\"query\": \"chevening\"}'.")
            return 2
        started = time.perf_counter()
        try:
            result = await client.call_tool(args.call, arguments)
        except FastnError as exc:
            return fail(exc)
        ok(f"Tool '{args.call}' returned in {time.perf_counter() - started:.2f}s")
        print(result.text[:2000])
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
