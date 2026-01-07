import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from .const import (
    DOMAIN,
    DEFAULT_NAME,
    CONF_GEMEENTEN,
    CONF_CAPCODES,
    CONF_REGIOS,
    CONF_DISCIPLINES,
)

_LOGGER = logging.getLogger(__name__)

class P2000ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for P2000 integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # hier kun je eventueel validatie toevoegen
            return self.async_create_entry(title=user_input.get("name", DEFAULT_NAME),
                                           data=user_input)

        data_schema = vol.Schema({
            vol.Optional("name", default=DEFAULT_NAME): cv.string,
            vol.Optional(CONF_GEMEENTEN, default=[]): vol.All(cv.ensure_list, [cv.string]),
            vol.Optional(CONF_CAPCODES, default=[]): vol.All(cv.ensure_list, [cv.string]),
            vol.Optional(CONF_REGIOS, default=""): cv.string,
            vol.Optional(CONF_DISCIPLINES, default=""): cv.string,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
