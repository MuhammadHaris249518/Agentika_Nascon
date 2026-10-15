import asyncio

import httpx
import pytest

from app.core.config import Settings
from app.integrations.errors import (
    FastnAuthError,
    FastnConfigError,
    FastnConnectionError,
    FastnTimeoutError,
)
from app.integrations.fastn_client import FastnClient, classify_exception


def make_client(**overrides) -> FastnClient:
    base = {"fastn_api_key": "secret-key", "fastn_max_retries": 1}
    return FastnClient(Settings(_env_file=None, **{**base, **overrides}))


def status_error(code: int) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://example.test/mcp")
    return httpx.HTTPStatusError("x", request=request, response=httpx.Response(code, request=request))


def test_headers_use_bearer_by_default():
    assert make_client().build_headers() == {"Authorization": "Bearer secret-key"}


def test_headers_support_raw_key_and_extra_headers():
    client = make_client(
        fastn_auth_header="x-api-key",
        fastn_auth_scheme="",
        fastn_extra_headers={"x-space": "abc"},
    )
    assert client.build_headers() == {"x-space": "abc", "x-api-key": "secret-key"}


def test_missing_key_raises_config_error():
    with pytest.raises(FastnConfigError):
        make_client(fastn_api_key=None).build_headers()


@pytest.mark.parametrize("code", [401, 403])
def test_auth_failures_are_classified(code):
    assert isinstance(classify_exception(status_error(code)), FastnAuthError)


def test_exception_groups_are_unwrapped():
    group = ExceptionGroup("tg", [status_error(401)])
    assert isinstance(classify_exception(group), FastnAuthError)


def test_timeout_and_connect_errors_are_classified():
    assert isinstance(classify_exception(TimeoutError()), FastnTimeoutError)
    assert isinstance(classify_exception(httpx.ConnectError("boom")), FastnConnectionError)


def test_retries_connection_errors_then_gives_up():
    client = make_client()
    calls = 0

    async def op(_session):
        raise AssertionError("not reached")

    class FailingOpen:
        async def __aenter__(self):
            nonlocal calls
            calls += 1
            raise httpx.ConnectError("down")

        async def __aexit__(self, *exc):
            return False

    client._open = lambda: FailingOpen()  # type: ignore[method-assign]
    with pytest.raises(FastnConnectionError):
        asyncio.run(client._run(op))
    assert calls == 2  # first try + one retry
