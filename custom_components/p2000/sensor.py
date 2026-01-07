import logging
import voluptuous as vol
from typing import Any, Dict

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_NAME, CONF_ICON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import homeassistant.helpers.config_validation as cv

from .api import P2000Api
from .coordinator import P2000DataUpdateCoordinator
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
    """Set up the P2000 sensor platform."""
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

    session = async_get_clientsession(hass)
    api = P2000Api(session)

    coordinator = P2000DataUpdateCoordinator(
        hass=hass,
        api=api,
        api_filter=api_filter,
        update_interval=30,
    )

    # Eerste fetch, anders blijft data = None
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [P2000Sensor(coordinator, name, icon)],
    )


class P2000Sensor(CoordinatorEntity, SensorEntity):
    """Representation of a P2000 Sensor."""

    def __init__(
        self,
        coordinator: P2000DataUpdateCoordinator,
        name: str,
        icon: str,
    ):
        super().__init__(coordinator)

        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"p2000_{name.lower()}"

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

        # Basis melding
        attrs["melding"] = data.get("melding")
        attrs["tekstmelding"] = data.get("tekstmelding")

        # Context (zonder id-velden)
        attrs["dienst"] = data.get("dienst", "Onbekend")
        attrs["regio"] = data.get("regio", "Onbekend")
        attrs["plaats"] = data.get("plaats")
        attrs["postcode"] = data.get("postcode", "Onbekend")
        attrs["straat"] = data.get("straat")
        attrs["datum"] = data.get("datum")
        attrs["tijd"] = data.get("tijd")

        # Prioriteit → boolean
        attrs["prio1"] = str(data.get("prio1")) == "1"

        attrs["brandinfo"] = data.get("brandinfo", "Onbekend")
        attrs["grip"] = data.get("grip")

        # Capcodes (meerdere mogelijk)
        capcodes = data.get("capcodes", [])
        attrs["capcodes"] = capcodes
        attrs["capcodes_str"] = ", ".join(
            f"{c.get('capcode')} ({c.get('omschrijving')})"
            for c in capcodes
        )

        # Locatie
        try:
            attrs["latitude"] = float(data.get("latitude"))
            attrs["longitude"] = float(data.get("longitude"))
        except (TypeError, ValueError):
            attrs["latitude"] = None
            attrs["longitude"] = None

        return attrs
