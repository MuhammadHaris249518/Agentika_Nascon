"""Client for the fastn MCP gateway (MCP over streamable HTTP).

Each operation opens a short-lived session. That keeps the client stateless and
safe to share across requests; connection setup cost is small next to a search call.
"""

import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, TypeVar

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.core.config import Settings, get_settings
from app.integrations.errors import (
    FastnAuthError,
    FastnConfigError,
    FastnConnectionError,
    FastnError,
    FastnProtocolError,
    FastnTimeoutError,
    FastnToolError,
)

logger = logging.getLogger(__name__)
T = TypeVar("T")

_RETRYABLE = (FastnConnectionError, FastnTimeoutError)


@dataclass(frozen=True)
class ToolInfo:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    text: str
    structured: Any | None = None


def _leaf_exceptions(exc: BaseException) -> list[BaseException]:
    """Flatten (possibly nested) exception groups raised by anyio task groups."""
    if isinstance(exc, BaseExceptionGroup):
        leaves: list[BaseException] = []
        for inner in exc.exceptions:
            leaves.extend(_leaf_exceptions(inner))
        return leaves
    return [exc]


def classify_exception(exc: BaseException) -> FastnError:
    """Translate transport-level exceptions into typed fastn errors."""
    if isinstance(exc, FastnError):
        return exc
    leaves = _leaf_exceptions(exc)

    for leaf in leaves:
        if isinstance(leaf, httpx.HTTPStatusError):
            status = leaf.response.status_code
            if status in (401, 403):
                return FastnAuthError(f"Gateway returned HTTP {status}.")
            if status == 404:
                return FastnConnectionError(
                    "Gateway returned HTTP 404.",
                    hint="The MCP path was not found. Check FASTN_MCP_URL.",
                )
            if status == 429:
                return FastnConnectionError(
                    "Gateway returned HTTP 429 (rate limited).",
                    hint="Slow down or check your fastn plan limits.",
                )
            return FastnConnectionError(f"Gateway returned HTTP {status}.")
    for leaf in leaves:
        if isinstance(leaf, (TimeoutError, httpx.TimeoutException)):
            return FastnTimeoutError("Timed out talking to the gateway.")
    for leaf in leaves:
        if isinstance(leaf, (httpx.ConnectError, OSError)):
            return FastnConnectionError(f"Connection failed: {type(leaf).__name__}.")
    return FastnProtocolError(f"Unexpected gateway error: {type(leaves[0]).__name__}.")


class FastnClient:
    def __init__(self, settings: Settings) -> None:
        self._url = settings.fastn_mcp_url.strip()
        self._key = (
            settings.fastn_api_key.get_secret_value().strip()
            if settings.fastn_api_key
            else ""
        )
        self._auth_header = settings.fastn_auth_header
        self._auth_scheme = settings.fastn_auth_scheme.strip()
        self._extra_headers = dict(settings.fastn_extra_headers)
        self._timeout = settings.fastn_timeout_seconds
        self._max_retries = settings.fastn_max_retries

    # -- configuration ---------------------------------------------------
    def build_headers(self) -> dict[str, str]:
        if not self._url:
            raise FastnConfigError("FASTN_MCP_URL is empty.")
        if not self._key:
            raise FastnConfigError("FASTN_API_KEY is empty.")
        value = f"{self._auth_scheme} {self._key}" if self._auth_scheme else self._key
        return {**self._extra_headers, self._auth_header: value}

    # -- session handling ------------------------------------------------
    @asynccontextmanager
    async def _open(self) -> AsyncIterator[ClientSession]:
        headers = self.build_headers()
        async with streamablehttp_client(self._url, headers=headers) as streams:
            read, write = streams[0], streams[1]
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

    async def _run(self, operation: Callable[[ClientSession], Awaitable[T]]) -> T:
        attempt = 0
        while True:
            try:
                async with asyncio.timeout(self._timeout):
                    async with self._open() as session:
                        return await operation(session)
            except Exception as exc:  # CancelledError is not an Exception: it passes through
                error = classify_exception(exc)
                if isinstance(error, _RETRYABLE) and attempt < self._max_retries:
                    delay = 0.5 * (2**attempt)
                    attempt += 1
                    logger.warning(
                        "fastn call failed (%s); retry %d/%d in %.1fs",
                        error.code, attempt, self._max_retries, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                if error is exc:
                    raise
                raise error from exc

    # -- public API ------------------------------------------------------
    async def list_tools(self) -> list[ToolInfo]:
        async def op(session: ClientSession) -> list[ToolInfo]:
            result = await session.list_tools()
            return [
                ToolInfo(t.name, t.description or "", dict(t.inputSchema or {}))
                for t in result.tools
            ]

        return await self._run(op)

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> ToolResult:
        async def op(session: ClientSession) -> ToolResult:
            result = await session.call_tool(name, arguments or {})
            text = "\n".join(
                block.text for block in result.content if getattr(block, "type", "") == "text"
            )
            if result.isError:
                raise FastnToolError(f"Tool '{name}' failed: {text[:500]}")
            return ToolResult(text=text, structured=getattr(result, "structuredContent", None))

        return await self._run(op)


@lru_cache
def get_fastn_client() -> FastnClient:
    return FastnClient(get_settings())
