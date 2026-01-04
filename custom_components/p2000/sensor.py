import logging
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_NAME, CONF_ICON
import homeassistant.helpers.config_validation as cv

from .api import P2000Api

"""Start the logger"""
_LOGGER = logging.getLogger(__name__)
 
DEFAULT_NAME = "p2000"

CONF_GEMEENTEN = "gemeenten"
CONF_CAPCODES = "capcodes"
CONF_DIENSTEN = "diensten"
CONF_WOONPLAATSEN = "woonplaatsen"
CONF_REGIOS = "regios"
CONF_PRIO1 = "prio1"
CONF_LIFE = "lifeliners"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_ICON, default="mdi:fire-truck"): cv.icon,
    vol.Optional(CONF_WOONPLAATSEN): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_GEMEENTEN): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_CAPCODES): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_REGIOS): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_DIENSTEN): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_PRIO1, default=False): cv.boolean,
    vol.Optional(CONF_LIFE, default=False): cv.boolean,    
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""

    name = config.get(CONF_NAME)
    icon = config.get(CONF_ICON)
    
    api_filter = {}
        
    # String / list properties
    for prop in [
        CONF_WOONPLAATSEN,
        CONF_GEMEENTEN,
        CONF_CAPCODES,
        CONF_DIENSTEN,
        CONF_REGIOS,
    ]:
        if prop in config:
            api_filter[prop] = config[prop]

    # Boolean properties
    for prop in [CONF_PRIO1, CONF_LIFE]:
        if config.get(prop):
            api_filter[prop] = "1"

    api = P2000Api(hass)

    async_add_entities([
        P2000Sensor(api, name, icon, api_filter)
    ])

class P2000Sensor(SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, api, name, icon, api_filter):
        """Initialize the sensor."""
        self.api = api
        self._attr_name = name
        self._attr_icon = icon
        self.api_filter = api_filter
     
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

    async def async_update(self):
        """Fetch new state data."""
        data = await self.api.get_data(self.api_filter)

        if not data:
            return

        self._attr_extra_state_attributes = data
        self._attr_native_value = data.get("melding")
