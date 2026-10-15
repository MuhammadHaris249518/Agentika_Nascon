"""Response models for the fastn diagnostic endpoints."""

from typing import Any

from pydantic import BaseModel


class ErrorInfo(BaseModel):
    code: str
    message: str
    hint: str


class ToolSummary(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


class FastnStatus(BaseModel):
    connected: bool
    tool_count: int = 0
    latency_ms: int | None = None
    error: ErrorInfo | None = None


class FastnTools(BaseModel):
    tools: list[ToolSummary]
