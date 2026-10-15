"""Diagnostic endpoints for the fastn MCP connection (Phase 1)."""

import time

from fastapi import APIRouter, Depends

from app.integrations.errors import FastnError
from app.integrations.fastn_client import FastnClient, get_fastn_client
from app.schemas.fastn import ErrorInfo, FastnStatus, FastnTools, ToolSummary

router = APIRouter(prefix="/fastn", tags=["fastn"])


@router.get("/status", response_model=FastnStatus)
async def fastn_status(client: FastnClient = Depends(get_fastn_client)) -> FastnStatus:
    """Always answers 200 with diagnostics, so a failed connection is easy to read."""
    started = time.perf_counter()
    try:
        tools = await client.list_tools()
    except FastnError as exc:
        return FastnStatus(
            connected=False,
            error=ErrorInfo(code=exc.code, message=exc.message, hint=exc.hint),
        )
    return FastnStatus(
        connected=True,
        tool_count=len(tools),
        latency_ms=int((time.perf_counter() - started) * 1000),
    )


@router.get("/tools", response_model=FastnTools)
async def fastn_tools(client: FastnClient = Depends(get_fastn_client)) -> FastnTools:
    tools = await client.list_tools()
    return FastnTools(
        tools=[
            ToolSummary(name=t.name, description=t.description, input_schema=t.input_schema)
            for t in tools
        ]
    )
