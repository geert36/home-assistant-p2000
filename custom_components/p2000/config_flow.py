"""Config flow for P2000 integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ICON, CONF_NAME
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_CAPCODES,
    CONF_DISCIPLINES,
    CONF_GEMEENTEN,
    CONF_REGIOS,
    DEFAULT_ICON,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

LIST_OPTIONS = (CONF_CAPCODES, CONF_GEMEENTEN)
TEXT_OPTIONS = (CONF_REGIOS, CONF_DISCIPLINES)


def _normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    """Normalize imported and UI config data."""
    normalized = dict(config)
    normalized[CONF_NAME] = normalized.get(CONF_NAME) or DEFAULT_NAME
    normalized[CONF_ICON] = normalized.get(CONF_ICON) or DEFAULT_ICON

    for key in LIST_OPTIONS:
        value = normalized.get(key, [])
        normalized[key] = cv.ensure_list(value) if value else []

    for key in TEXT_OPTIONS:
        normalized[key] = normalized.get(key) or ""

    return normalized


def _options_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the schema for setup and options."""
    defaults = _normalize_config(defaults or {})
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults[CONF_NAME]): cv.string,
            vol.Optional(CONF_ICON, default=defaults[CONF_ICON]): cv.icon,
            vol.Optional(CONF_CAPCODES, default=defaults[CONF_CAPCODES]): vol.All(
                cv.ensure_list, [cv.string]
            ),
            vol.Optional(CONF_GEMEENTEN, default=defaults[CONF_GEMEENTEN]): vol.All(
                cv.ensure_list, [cv.string]
            ),
            vol.Optional(CONF_REGIOS, default=defaults[CONF_REGIOS]): cv.string,
            vol.Optional(
                CONF_DISCIPLINES, default=defaults[CONF_DISCIPLINES]
            ): cv.string,
        }
    )


class P2000FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a P2000 config flow."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return P2000OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step from the user (UI)."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=_options_schema()
            )

        user_input = _normalize_config(user_input)
        await self.async_set_unique_id(user_input[CONF_NAME].lower())
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

    async def async_step_import(
        self, import_config: dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Import a YAML config entry."""
        import_config = _normalize_config(import_config)
        await self.async_set_unique_id(import_config[CONF_NAME].lower())
        self._abort_if_unique_id_configured()

        _LOGGER.info("Importing YAML P2000 config: %s", import_config)
        return self.async_create_entry(
            title=import_config[CONF_NAME], data=import_config
        )


class P2000OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle P2000 options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage P2000 options."""
        if user_input is not None:
            return self.async_create_entry(
                title="", data=_normalize_config(user_input)
            )

        defaults = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init", data_schema=_options_schema(defaults)
        )
