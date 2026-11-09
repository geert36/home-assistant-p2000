"""Shared fixtures for the P2000 tests."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.p2000.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Let Home Assistant load the integration from this repository."""
    yield


@pytest.fixture
def mock_api():
    """Replace the API with a mock; tests set return_value or side_effect."""
    with (
        patch(
            "custom_components.p2000.api.P2000Api.get_meldingen",
            new_callable=AsyncMock,
        ) as get_meldingen,
        patch(
            "custom_components.p2000.async_get_clientsession",
            return_value=MagicMock(),
        ),
    ):
        get_meldingen.return_value = []
        yield get_meldingen


@pytest.fixture
async def unload_entries(hass: HomeAssistant):
    """Unload all entries after the test so no timers are left behind."""
    yield
    for entry in hass.config_entries.async_entries(DOMAIN):
        await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


def make_entry(**data) -> MockConfigEntry:
    """Create a config entry in the current storage shape."""
    return MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="Brandweer",
        data={
            "name": "Brandweer",
            "icon": "mdi:fire-truck",
            "regios": ["17"],
            "scan_interval": 30,
            **data,
        },
    )


def make_group(melding_id: str, *sub_ids: str) -> dict:
    """Create an API group: the first message plus follow-up messages."""
    return {
        "id": melding_id,
        "melding": f"melding {melding_id}",
        "tekstmelding": f"tekst {melding_id}",
        "dienst": "Brandweer",
        "regio": "IJsselland",
        "plaats": "Zwolle",
        "postcode": "8031ER",
        "straat": "Teststraat",
        "datum": "09-11",
        "tijd": "18:54",
        "prio1": "1",
        "lat": "52.5",
        "lon": "6.1",
        "capcodes": [{"capcode": "123", "omschrijving": "Post"}],
        "subitems": [
            {"id": sub_id, "melding": f"melding {sub_id}", "lat": "52.5", "lon": "6.1"}
            for sub_id in sub_ids
        ],
    }
