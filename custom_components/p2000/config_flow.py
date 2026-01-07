"""Config flow for P2000 integration."""
import logging
from typing import Any, Dict

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_ICON
import homeassistant.helpers.config_validation as cv

from .const import (
    DEFAULT_NAME,
    DEFAULT_ICON,
    CONF_CAPCODES,
    CONF_GEMEENTEN,
    CONF_REGIOS,
    CONF_DISCIPLINES,
)

_LOGGER = logging.getLogger(__name__)

# Formulier voor UI
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_ICON, default=DEFAULT_ICON): cv.icon,
        vol.Optional(CONF_CAPCODES, default=[]): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_GEMEENTEN, default=[]): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_REGIOS, default=""): cv.string,
        vol.Optional(CONF_DISCIPLINES, default=""): cv.string,
    }
)


class P2000FlowHandler(config_entries.ConfigFlow, domain="p2000"):
    """Handle a P2000 config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input: Dict[str, Any] = None):
        """Handle the initial step from the user (UI)."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        # Check of er al een entry is met dezelfde naam
        existing_entry = self._async_current_entries()
        for entry in existing_entry:
            if entry.data.get(CONF_NAME) == user_input[CONF_NAME]:
                return self.async_abort(reason="already_configured")

        return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

    async def async_step_import(self, import_config: Dict[str, Any]):
        """Import a YAML config entry."""
        # Check of er al een entry bestaat met dezelfde naam
        for entry in self._async_current_entries():
            if entry.data.get(CONF_NAME) == import_config.get(CONF_NAME, DEFAULT_NAME):
                _LOGGER.info(
                    "Skipping import of YAML entry '%s', already configured",
                    import_config.get(CONF_NAME),
                )
                return self.async_abort(reason="already_configured")

        _LOGGER.info("Importing YAML P2000 config: %s", import_config)
        return self.async_create_entry(
            title=import_config.get(CONF_NAME, DEFAULT_NAME), data=import_config
        )
