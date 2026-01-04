import logging
import voluptuous as vol
from typing import Any, Dict, List

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_NAME, CONF_ICON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .api import P2000Api
from .const import (
    DEFAULT_NAME,
    DEFAULT_ICON,
    CONF_GEMEENTEN,
    CONF_CAPCODES,
    CONF_REGIOS,
    CONF_DISCIPLINES,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_ICON, default=DEFAULT_ICON): cv.icon,
        vol.Optional(CONF_GEMEENTEN): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_CAPCODES): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_REGIOS): cv.string,
        vol.Optional(CONF_DISCIPLINES): cv.string,
    }
)

async def async_setup_platform(
    hass: HomeAssistant,
    config: Dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
) -> None:
    """Set up the P2000 sensor platform asynchronously."""
    name = config.get(CONF_NAME)
    icon = config.get(CONF_ICON)

    api_filter: Dict[str, Any] = {}
    if config.get(CONF_GEMEENTEN):
        api_filter["gemeenten"] = config[CONF_GEMEENTEN]
    if config.get(CONF_CAPCODES):
        api_filter["capcodes"] = config[CONF_CAPCODES]
    if config.get(CONF_REGIOS):
        api_filter["regios"] = config[CONF_REGIOS]
    if config.get(CONF_DISCIPLINES):
        api_filter["disciplines"] = config[CONF_DISCIPLINES]

    _LOGGER.info("P2000 filter being used: %s", api_filter)

    # Gebruik de Home Assistant aiohttp session
    session = async_get_clientsession(hass)
    api = P2000Api(session)

    async_add_entities(
        [P2000Sensor(api, name, icon, api_filter)],
        update_before_add=True,
    )

class P2000Sensor(SensorEntity):
    """Representation of a P2000 Sensor."""

    def __init__(
        self,
        api: P2000Api,
        name: str,
        icon: str,
        api_filter: Dict[str, Any],
    ):
        self.api = api
        self.api_filter = api_filter

        self._attr_name = name
        self._attr_icon = icon
        self._attr_native_value: str | None = None
        self._attr_extra_state_attributes: Dict[str, Any] = {}

        # Uniek ID (nodig voor entity registry)
        self._attr_unique_id = f"p2000_{name.lower()}"

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        try:
            _LOGGER.debug(
                "Fetching P2000 data with filter: %s",
                self.api_filter,
            )

            data = await self.api.get_data(self.api_filter)

            if not data:
                _LOGGER.debug("No P2000 data returned for filter: %s", self.api_filter)
                self._attr_native_value = None
                self._attr_extra_state_attributes = {}
                return

            # defensief checken of het dict is
            if not isinstance(data, dict):
                _LOGGER.warning("Unexpected data format: %s", data)
                self._attr_native_value = None
                self._attr_extra_state_attributes = {}
                return

            # Lat/lon hernoemen als dat nog niet gebeurd is
            if "lat" in data:
                data["latitude"] = data.pop("lat")
            if "lon" in data:
                data["longitude"] = data.pop("lon")

            self._attr_native_value = data.get("id")
            self._attr_extra_state_attributes = data

            if self._attr_native_value is None:
                _LOGGER.debug("Received P2000 data does not contain 'id': %s", data)

        except Exception as err:
            _LOGGER.error("Error updating P2000 sensor: %s", err)
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
