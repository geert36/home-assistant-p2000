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
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

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
from .melding import melding_attributes

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
    coordinator: P2000DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

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
    def available(self) -> bool:
        """Stay available on transient API failures while a last known melding exists."""
        if self.coordinator.data:
            return True
        return super().available

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

        return {
            "last_update_success": self.coordinator.last_update_success,
            **melding_attributes(data),
        }
