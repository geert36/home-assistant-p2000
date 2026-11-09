"""Tests for the P2000 API client."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.p2000.api import P2000Api, P2000ApiError


class _FakeResponse:
    """Minimal aiohttp response stand-in."""

    def __init__(self, status: int = 200, payload=None, json_error=None) -> None:
        self.status = status
        self._payload = payload
        self._json_error = json_error
        self.request_info = MagicMock()
        self.history = ()

    async def json(self, content_type=None):
        if self._json_error:
            raise self._json_error
        return self._payload

    async def text(self) -> str:
        return "raw"

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc) -> None:
        return None


class _FakeSession:
    """Session that plays back a list of responses or exceptions."""

    def __init__(self, *outcomes) -> None:
        self._outcomes = list(outcomes)
        self.calls = 0
        self.headers_seen = None

    def get(self, url, **kwargs):
        self.calls += 1
        self.headers_seen = kwargs.get("headers")
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def _get(session: _FakeSession):
    with patch("custom_components.p2000.api.asyncio.sleep", new=AsyncMock()):
        return asyncio.run(P2000Api(session).get_meldingen({"regios": ["17"]}))


def test_returns_all_groups_with_normalized_coordinates() -> None:
    """All groups come back, with lat/lon renamed (also in subitems)."""
    payload = {
        "meldingen": [
            {
                "id": "2",
                "lat": "52.1",
                "lon": "6.1",
                "subitems": [{"id": "3", "lat": "52.2", "lon": "6.2"}],
            },
            {"id": "1", "lat": "52.0", "lon": "6.0"},
        ]
    }

    groups = _get(_FakeSession(_FakeResponse(payload=payload)))

    assert [g["id"] for g in groups] == ["2", "1"]
    assert groups[0]["latitude"] == "52.1" and "lat" not in groups[0]
    assert groups[0]["subitems"][0]["longitude"] == "6.2"


def test_sends_user_agent() -> None:
    """Requests identify the integration."""
    session = _FakeSession(_FakeResponse(payload={"meldingen": []}))
    _get(session)

    assert "home-assistant-p2000" in session.headers_seen["User-Agent"]


@pytest.mark.parametrize("payload", [{"meldingen": []}, {"meldingen": None}, {}])
def test_no_meldingen_returns_empty_list(payload) -> None:
    """No notifications is a normal answer, not an error."""
    assert _get(_FakeSession(_FakeResponse(payload=payload))) == []


def test_retries_then_succeeds() -> None:
    """A transient timeout is retried."""
    session = _FakeSession(
        asyncio.TimeoutError(),
        aiohttp.ClientConnectionError("boom"),
        _FakeResponse(payload={"meldingen": [{"id": "1"}]}),
    )

    assert [g["id"] for g in _get(session)] == ["1"]
    assert session.calls == 3


def test_raises_after_all_retries_fail() -> None:
    """Persistent failure is an error, so the coordinator can report it."""
    session = _FakeSession(
        asyncio.TimeoutError(), asyncio.TimeoutError(), asyncio.TimeoutError()
    )

    with pytest.raises(P2000ApiError):
        _get(session)
    assert session.calls == 3


def test_server_error_is_retried_and_client_error_is_not() -> None:
    """5xx is retried; a 4xx fails immediately."""
    server_errors = _FakeSession(*[_FakeResponse(status=503) for _ in range(3)])
    with pytest.raises(P2000ApiError):
        _get(server_errors)
    assert server_errors.calls == 3

    not_found = _FakeSession(_FakeResponse(status=404))
    with pytest.raises(P2000ApiError):
        _get(not_found)
    assert not_found.calls == 1


def test_invalid_json_and_unexpected_shape_raise() -> None:
    """Garbage from the API is an error, not 'no meldingen'."""
    with pytest.raises(P2000ApiError):
        _get(_FakeSession(_FakeResponse(json_error=json.JSONDecodeError("bad", "doc", 0))))
    with pytest.raises(P2000ApiError):
        _get(_FakeSession(_FakeResponse(payload=["not", "a", "dict"])))
