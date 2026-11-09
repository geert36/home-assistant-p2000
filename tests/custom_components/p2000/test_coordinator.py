"""Tests for the P2000 coordinator update logic."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.p2000.api import P2000ApiError
from custom_components.p2000.coordinator import P2000DataUpdateCoordinator


def _group(melding_id: str, *sub_ids: str) -> dict:
    return {
        "id": melding_id,
        "melding": f"melding {melding_id}",
        "subitems": [{"id": sub_id} for sub_id in sub_ids],
    }


def _coordinator(*outcomes) -> P2000DataUpdateCoordinator:
    api = MagicMock()
    api.get_meldingen = AsyncMock(side_effect=list(outcomes))
    return P2000DataUpdateCoordinator(MagicMock(), MagicMock(), api, {"regios": ["17"]}, 30)


def _update(coordinator: P2000DataUpdateCoordinator) -> dict:
    return asyncio.run(coordinator._async_update_data())


def test_first_update_is_baseline_without_events() -> None:
    """Existing meldingen at start are shown but not announced as new."""
    coordinator = _coordinator([_group("10"), _group("9")])

    data = _update(coordinator)

    assert data["id"] == "10"
    assert coordinator.new_meldingen == []


def test_new_meldingen_are_exposed_oldest_first() -> None:
    """Every message that appeared since the last update is exposed."""
    coordinator = _coordinator([_group("10")], [_group("12"), _group("11"), _group("10")])
    _update(coordinator)

    data = _update(coordinator)

    assert data["id"] == "12"
    assert [m["id"] for m in coordinator.new_meldingen] == ["11", "12"]


def test_failed_update_raises_and_exposes_no_new_meldingen() -> None:
    """A failure is reported and leaves nothing for listeners to re-fire."""
    coordinator = _coordinator(
        [_group("10")],
        [_group("11"), _group("10")],
        P2000ApiError("timeout"),
    )
    _update(coordinator)
    _update(coordinator)
    assert [m["id"] for m in coordinator.new_meldingen] == ["11"]

    with pytest.raises(UpdateFailed):
        _update(coordinator)

    assert coordinator.new_meldingen == []


def test_recovery_after_failure_does_not_repeat_meldingen() -> None:
    """When the API is back, the same meldingen are not announced twice."""
    coordinator = _coordinator(
        [_group("10")],
        P2000ApiError("timeout"),
        [_group("10")],
    )
    _update(coordinator)
    with pytest.raises(UpdateFailed):
        _update(coordinator)

    _update(coordinator)

    assert coordinator.new_meldingen == []


def test_message_arriving_during_outage_is_announced_on_recovery() -> None:
    """A melding that came in while the API was down is not lost."""
    coordinator = _coordinator(
        [_group("10")],
        P2000ApiError("timeout"),
        [_group("11"), _group("10")],
    )
    _update(coordinator)
    with pytest.raises(UpdateFailed):
        _update(coordinator)

    _update(coordinator)

    assert [m["id"] for m in coordinator.new_meldingen] == ["11"]


def test_empty_answer_keeps_last_known_data() -> None:
    """No meldingen for the filter keeps the last known melding."""
    coordinator = _coordinator([_group("10")], [])
    _update(coordinator)
    coordinator.data = {"id": "10"}

    assert _update(coordinator) == {"id": "10"}
    assert coordinator.new_meldingen == []
