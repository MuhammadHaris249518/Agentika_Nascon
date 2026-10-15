"""Typed errors for the fastn integration, each with an actionable hint."""


class FastnError(Exception):
    """Base class for all fastn gateway failures."""

    code = "fastn_error"
    http_status = 502
    hint = "See the backend logs for details."

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if hint:
            self.hint = hint


class FastnConfigError(FastnError):
    code = "fastn_config"
    http_status = 503
    hint = "Set FASTN_MCP_URL and FASTN_API_KEY in backend/.env."


class FastnAuthError(FastnError):
    code = "fastn_auth"
    hint = (
        "The gateway rejected the credentials. Check the API key, and confirm the "
        "header name (FASTN_AUTH_HEADER) and scheme (FASTN_AUTH_SCHEME) in the fastn dashboard."
    )


class FastnConnectionError(FastnError):
    code = "fastn_connection"
    hint = (
        "Could not reach the gateway. Check FASTN_MCP_URL (the docs show both "
        "mcp.fastn.dev and mcp.ucl.dev), your network, and any proxy settings."
    )


class FastnTimeoutError(FastnError):
    code = "fastn_timeout"
    http_status = 504
    hint = (
        "The gateway did not answer in time. fastn's fastest execution tier has a "
        "30 second limit, so keep each tool call small."
    )


class FastnProtocolError(FastnError):
    code = "fastn_protocol"
    hint = (
        "The endpoint answered but did not speak MCP over streamable HTTP. "
        "Check that the URL is the MCP endpoint, not a dashboard or REST URL."
    )


class FastnToolError(FastnError):
    code = "fastn_tool"
    hint = "The tool ran but reported an error. Check the workflow in fastn."
