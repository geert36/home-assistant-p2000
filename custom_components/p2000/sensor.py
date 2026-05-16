from __future__ import annotations

import logging
from typing import Any, Dict

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import P2000Api
from .coordinator import P2000DataUpdateCoordinator
from .const import (
    CONF_CAPCODES,
    CONF_DISCIPLINES,
    CONF_GEMEENTEN,
    CONF_ICON,
    CONF_PRIO1,
    CONF_REGIOS,
    DEFAULT_ICON,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_ICON, default=DEFAULT_ICON): cv.string,
        vol.Optional(CONF_GEMEENTEN): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_CAPCODES): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_REGIOS): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_DISCIPLINES): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_PRIO1, default=False): cv.boolean,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: Dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict[str, Any] | None = None,
) -> bool:
    """Import YAML platform config into a config entry."""
    await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data=dict(config),
    )
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up P2000 sensor from a config entry."""
    config = {**entry.data, **entry.options}

    api_filter: Dict[str, Any] = {}
    if config.get(CONF_GEMEENTEN):
        api_filter["gemeenten"] = config[CONF_GEMEENTEN]
    if config.get(CONF_CAPCODES):
        api_filter["capcodes"] = config[CONF_CAPCODES]
    if config.get(CONF_REGIOS):
        api_filter["regios"] = config[CONF_REGIOS]
    if config.get(CONF_DISCIPLINES):
        api_filter["disciplines"] = config[CONF_DISCIPLINES]
    if config.get(CONF_PRIO1):
        api_filter["prio1"] = True

    _LOGGER.info("P2000 filter being used: %s", api_filter)
    session = async_get_clientsession(hass)
    api = P2000Api(session)
    coordinator = P2000DataUpdateCoordinator(
        hass=hass,
        api=api,
        api_filter=api_filter,
        update_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        P2000Sensor(
            coordinator,
            entry.entry_id,
            config.get(CONF_NAME, DEFAULT_NAME),
            config.get(CONF_ICON, DEFAULT_ICON),
        )
    ])


class P2000Sensor(CoordinatorEntity, SensorEntity):
    """Representation of a P2000 Sensor."""

    def __init__(
        self,
        coordinator: P2000DataUpdateCoordinator,
        entry_id: str,
        name: str,
        icon: str,
    ):
        super().__init__(coordinator)

        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"p2000_{entry_id}"

    @property
    def native_value(self) -> str | None:
        """Return the sensor state."""
        data = self.coordinator.data
        if not data:
            return None
        return data.get("id")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        data = self.coordinator.data
        if not data:
            return {}

        attrs: Dict[str, Any] = {}
        attrs["melding"] = data.get("melding")
        attrs["tekstmelding"] = data.get("tekstmelding")
        attrs["dienst"] = data.get("dienst", "Onbekend")
        attrs["regio"] = data.get("regio", "Onbekend")
        attrs["plaats"] = data.get("plaats")
        attrs["postcode"] = data.get("postcode", "Onbekend")
        attrs["straat"] = data.get("straat")
        attrs["datum"] = data.get("datum")
        attrs["tijd"] = data.get("tijd")
        attrs["prio1"] = str(data.get("prio1")) == "1"
        attrs["brandinfo"] = data.get("brandinfo", "Onbekend")
        attrs["grip"] = data.get("grip")

        capcodes = data.get("capcodes", [])
        attrs["capcodes"] = capcodes
        attrs["capcodes_str"] = ", ".join(
            f"{c.get('capcode')} ({c.get('omschrijving')})"
            for c in capcodes
        )

        try:
            attrs["latitude"] = float(data.get("latitude"))
            attrs["longitude"] = float(data.get("longitude"))
        except (TypeError, ValueError):
            attrs["latitude"] = None
            attrs["longitude"] = None

        return attrs
