import logging
from typing import Any, Dict, List

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

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

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up P2000 sensor from a config entry."""
    api_filter: Dict[str, Any] = {}
    if entry.data.get(CONF_GEMEENTEN):
        api_filter["gemeenten"] = entry.data[CONF_GEMEENTEN]
    if entry.data.get(CONF_CAPCODES):
        api_filter["capcodes"] = entry.data[CONF_CAPCODES]
    if entry.data.get(CONF_REGIOS):
        api_filter["regios"] = entry.data[CONF_REGIOS]
    if entry.data.get(CONF_DISCIPLINES):
        api_filter["disciplines"] = entry.data[CONF_DISCIPLINES]

    session = async_get_clientsession(hass)
    api = P2000Api(session)

    async_add_entities(
        [
            P2000Sensor(
                api,
                entry.data.get("name", DEFAULT_NAME),
                entry.data.get("icon", DEFAULT_ICON),
                api_filter,
            )
        ],
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
            _LOGGER.debug("Fetching P2000 data with filter: %s", self.api_filter)
            data = await self.api.get_data(self.api_filter)

            if not data:
                _LOGGER.debug("No P2000 data returned for filter: %s", self.api_filter)
                self._attr_native_value = None
                self._attr_extra_state_attributes = {}
                return

            if not isinstance(data, dict):
                _LOGGER.warning("Unexpected data format: %s", data)
                self._attr_native_value = None
                self._attr_extra_state_attributes = {}
                return

            # Vul de state en attributes overzichtelijk
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

            # Prio1 als boolean
            prio = data.get("prio1")
            attrs["prio1"] = str(prio) == "1"

            attrs["brandinfo"] = data.get("brandinfo", "Onbekend")
            attrs["grip"] = data.get("grip")

            # Capcodes
            capcodes: List[Dict[str, str]] = data.get("capcodes", [])
            attrs["capcodes"] = capcodes  # originele lijst
            attrs["capcodes_str"] = ", ".join(
                f"{c.get('capcode')} ({c.get('omschrijving')})" for c in capcodes
            )

            # Latitude / Longitude als float
            try:
                attrs["latitude"] = float(data.get("lat") or data.get("latitude"))
                attrs["longitude"] = float(data.get("lon") or data.get("longitude"))
            except (TypeError, ValueError):
                attrs["latitude"] = None
                attrs["longitude"] = None

            # Zet state en attributes
            self._attr_native_value = data.get("id")
            self._attr_extra_state_attributes = attrs

            if self._attr_native_value is None:
                _LOGGER.debug("Received P2000 data does not contain 'id': %s", data)

        except Exception as err:
            _LOGGER.error("Error updating P2000 sensor: %s", err)
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
