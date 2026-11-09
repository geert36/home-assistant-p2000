"""Integration tests: set the integration up in a real Home Assistant."""
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.p2000.api import P2000ApiError
from custom_components.p2000.const import DOMAIN
from custom_components.p2000.diagnostics import async_get_config_entry_diagnostics

from ...conftest import make_entry, make_group

SENSOR = "sensor.brandweer"
EVENT = "event.brandweer_melding"


async def _setup(hass: HomeAssistant, mock_api, first_answer, **data):
    mock_api.side_effect = None
    mock_api.return_value = first_answer
    entry = make_entry(**data)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _collect_events(hass: HomeAssistant) -> list[tuple]:
    """Record (event_type, id, parent_id) for every event the entity fires."""
    fired: list[tuple] = []

    def listener(event) -> None:
        if event.data["entity_id"] != EVENT:
            return
        old, new = event.data["old_state"], event.data["new_state"]
        if old is None or new is None:
            return
        attrs = new.attributes
        fired.append((attrs.get("event_type"), attrs.get("id"), attrs.get("parent_id")))

    hass.bus.async_listen("state_changed", listener)
    return fired


async def test_setup_creates_sensor_event_and_one_device(
    hass: HomeAssistant, mock_api, unload_entries
) -> None:
    """Both entities exist, share one device, and nothing fires at startup."""
    entry = await _setup(hass, mock_api, [make_group("10"), make_group("9")])

    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get(SENSOR).state == "10"
    assert hass.states.get(SENSOR).attributes["melding"] == "melding 10"
    assert hass.states.get(EVENT) is not None
    assert hass.states.get(EVENT).attributes["event_types"] == [
        "melding",
        "vervolgmelding",
    ]

    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert len(devices) == 1
    device = devices[0]
    assert (DOMAIN, entry.entry_id) in device.identifiers
    assert device.name == "Brandweer"
    registry = er.async_get(hass)
    assert registry.async_get(SENSOR).device_id == device.id
    assert registry.async_get(EVENT).device_id == device.id


async def test_unload_removes_entities(
    hass: HomeAssistant, mock_api, unload_entries
) -> None:
    """Unloading the entry unloads both platforms."""
    entry = await _setup(hass, mock_api, [make_group("10")])

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
    assert hass.states.get(SENSOR).state == "unavailable"
    assert hass.states.get(EVENT).state == "unavailable"


async def test_new_meldingen_and_follow_up_fire_events_once(
    hass: HomeAssistant, mock_api, unload_entries
) -> None:
    """Two new meldingen in one poll, then a follow-up on an older one."""
    entry = await _setup(hass, mock_api, [make_group("10"), make_group("9")])
    fired = _collect_events(hass)
    coordinator = entry.runtime_data

    mock_api.return_value = [make_group("12"), make_group("11"), make_group("10")]
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert fired == [("melding", "11", None), ("melding", "12", None)]
    assert hass.states.get(SENSOR).state == "12"

    fired.clear()
    mock_api.return_value = [make_group("10", "13"), make_group("12"), make_group("11")]
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert fired == [("vervolgmelding", "13", "10")]

    # The sensor shows the group that was most recently active, so it
    # switches back to the older melding; the event entity did not repeat it.
    assert hass.states.get(SENSOR).state == "10"

    fired.clear()
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert fired == []


async def test_api_outage_keeps_sensor_and_does_not_repeat_events(
    hass: HomeAssistant, mock_api, unload_entries
) -> None:
    """A failing API keeps the last melding visible and fires nothing."""
    entry = await _setup(hass, mock_api, [make_group("10")])
    fired = _collect_events(hass)
    coordinator = entry.runtime_data

    mock_api.side_effect = P2000ApiError("timeout")
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    sensor = hass.states.get(SENSOR)
    assert sensor.state == "10"
    assert sensor.attributes["melding"] == "melding 10"
    assert sensor.attributes["last_update_success"] is False
    assert hass.states.get(EVENT).state != "unavailable"
    assert fired == []

    mock_api.side_effect = None
    mock_api.return_value = [make_group("10")]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get(SENSOR).attributes["last_update_success"] is True
    assert fired == []


async def test_melding_during_outage_is_announced_after_recovery(
    hass: HomeAssistant, mock_api, unload_entries
) -> None:
    """A melding that came in while the API was down is not lost."""
    entry = await _setup(hass, mock_api, [make_group("10")])
    fired = _collect_events(hass)
    coordinator = entry.runtime_data

    mock_api.side_effect = P2000ApiError("timeout")
    await coordinator.async_refresh()
    mock_api.side_effect = None
    mock_api.return_value = [make_group("11"), make_group("10")]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert fired == [("melding", "11", None)]


async def test_setup_is_retried_when_api_is_down_at_start(
    hass: HomeAssistant, mock_api, unload_entries
) -> None:
    """If the API is unreachable at startup Home Assistant retries later."""
    mock_api.side_effect = P2000ApiError("down")
    entry = make_entry()
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_changing_options_reloads_with_new_filter(
    hass: HomeAssistant, mock_api, unload_entries
) -> None:
    """Options are applied by reloading the entry."""
    entry = await _setup(hass, mock_api, [make_group("10")])
    assert mock_api.call_args.args[0] == {"regios": ["17"]}

    hass.config_entries.async_update_entry(
        entry, options={"regios": ["17"], "prio1": True, "scan_interval": 60}
    )
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert mock_api.call_args.args[0] == {"regios": ["17"], "prio1": True}
    assert entry.runtime_data.update_interval.total_seconds() == 60


async def test_diagnostics_redact_locations_and_filters(
    hass: HomeAssistant, mock_api, unload_entries
) -> None:
    """Diagnostics show the structure, not where incidents happened."""
    entry = await _setup(
        hass,
        mock_api,
        [make_group("10", "11")],
        gemeenten=["Zwolle"],
        capcodes=["123"],
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["entry"]["data"]["gemeenten"] == "**REDACTED**"
    assert diagnostics["entry"]["data"]["capcodes"] == "**REDACTED**"
    assert diagnostics["entry"]["data"]["regios"] == ["17"]

    coordinator = diagnostics["coordinator"]
    assert coordinator["last_update_success"] is True
    assert coordinator["update_interval_seconds"] == 30
    assert coordinator["api_filter"]["gemeenten"] == "**REDACTED**"

    melding = coordinator["last_melding"]
    assert melding["id"] == "10"
    assert melding["dienst"] == "Brandweer"
    for key in ("melding", "tekstmelding", "plaats", "postcode", "straat", "lat", "lon", "capcodes"):
        assert melding[key] == "**REDACTED**", key
    assert melding["subitems"][0]["id"] == "11"
    assert melding["subitems"][0]["lat"] == "**REDACTED**"


async def test_diagnostics_without_any_melding(
    hass: HomeAssistant, mock_api, unload_entries
) -> None:
    """No meldingen yet is fine."""
    entry = await _setup(hass, mock_api, [])

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["coordinator"]["last_melding"] == {}
