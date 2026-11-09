"""Tests for the config flow, options flow and the YAML import."""
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component
import pytest

from custom_components.p2000.const import DOMAIN

from ...conftest import make_entry, make_group

USER_INPUT = {
    "name": "Brandweer",
    "icon": "mdi:fire-truck",
    "capcodes": "123, 456",
    "gemeenten": "Zwolle",
    "regios": ["17"],
    "disciplines": ["2"],
    "prio1": True,
    "scan_interval": 45,
}


async def test_user_flow_creates_entry_with_normalized_data(
    hass: HomeAssistant, mock_api, unload_entries
) -> None:
    """Text fields become lists and the entry is set up."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Brandweer"
    assert result["data"]["capcodes"] == ["123", "456"]
    assert result["data"]["gemeenten"] == ["Zwolle"]
    assert result["data"]["regios"] == ["17"]
    assert result["data"]["disciplines"] == ["2"]
    assert result["data"]["prio1"] is True
    assert result["data"]["scan_interval"] == 45

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.state is ConfigEntryState.LOADED
    assert mock_api.call_args.args[0] == {
        "gemeenten": ["Zwolle"],
        "capcodes": ["123", "456"],
        "regios": ["17"],
        "disciplines": ["2"],
        "prio1": True,
    }


async def test_user_flow_rejects_duplicate_name(
    hass: HomeAssistant, mock_api, unload_entries
) -> None:
    """A second sensor with the same name is aborted."""
    first = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await hass.config_entries.flow.async_configure(first["flow_id"], USER_INPUT)
    await hass.async_block_till_done()

    second = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        second["flow_id"], USER_INPUT
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_import_flow_creates_entry(
    hass: HomeAssistant, mock_api, unload_entries
) -> None:
    """The YAML import creates an entry from the legacy settings."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data={"name": "Imported", "regios": ["17"], "prio1": True},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["regios"] == ["17"]
    assert result["data"]["prio1"] is True
    assert result["data"]["scan_interval"] == 30


async def test_yaml_platform_is_imported_and_reported(
    hass: HomeAssistant, mock_api, unload_entries
) -> None:
    """YAML config is imported once and a repair issue asks to remove it."""
    mock_api.return_value = [make_group("10")]

    assert await async_setup_component(
        hass,
        "sensor",
        {"sensor": [{"platform": DOMAIN, "name": "Yaml", "regios": ["17"]}]},
    )
    await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert [e.title for e in entries] == ["Yaml"]
    assert entries[0].state is ConfigEntryState.LOADED
    assert hass.states.get("sensor.yaml").state == "10"

    issue = ir.async_get(hass).async_get_issue(DOMAIN, "yaml_deprecated")
    assert issue is not None
    assert issue.translation_key == "yaml_deprecated"
    assert issue.is_fixable is False


async def test_options_flow_saves_normalized_options(
    hass: HomeAssistant, mock_api, unload_entries
) -> None:
    """Changing options normalizes them and reloads the entry."""
    mock_api.return_value = [make_group("10")]
    entry = make_entry()
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {**USER_INPUT, "scan_interval": 10}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options["scan_interval"] == 10
    assert entry.options["capcodes"] == ["123", "456"]
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.update_interval.total_seconds() == 10


async def test_options_flow_rejects_too_short_interval(
    hass: HomeAssistant, mock_api, unload_entries
) -> None:
    """The form does not accept an interval below the minimum."""
    mock_api.return_value = [make_group("10")]
    entry = make_entry()
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    with pytest.raises(InvalidData):
        await hass.config_entries.options.async_configure(
            result["flow_id"], {**USER_INPUT, "scan_interval": 5}
        )
