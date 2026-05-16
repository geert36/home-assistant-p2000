"""Config flow for P2000 integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import BooleanSelector, IconSelector, SelectSelector

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

TEXT_LIST_OPTIONS = (CONF_CAPCODES, CONF_GEMEENTEN)
SELECT_LIST_OPTIONS = (CONF_REGIOS, CONF_DISCIPLINES)

REGIO_OPTIONS = [
    {"value": "1", "label": "1: Amsterdam-Amstelland"},
    {"value": "2", "label": "2: Groningen"},
    {"value": "3", "label": "3: Noord- en Oost Gelderland"},
    {"value": "4", "label": "4: Zaanstreek-Waterland"},
    {"value": "5", "label": "5: Hollands Midden"},
    {"value": "6", "label": "6: Brabant Noord"},
    {"value": "7", "label": "7: Friesland"},
    {"value": "8", "label": "8: Gelderland-Midden"},
    {"value": "9", "label": "9: Kennemerland"},
    {"value": "10", "label": "10: Rotterdam-Rijnmond"},
    {"value": "11", "label": "11: Brabant Zuid-Oost"},
    {"value": "12", "label": "12: Drenthe"},
    {"value": "13", "label": "13: Gelderland-Zuid"},
    {"value": "14", "label": "14: Zuid-Holland Zuid"},
    {"value": "15", "label": "15: Limburg-Noord"},
    {"value": "17", "label": "17: IJsselland"},
    {"value": "18", "label": "18: Utrecht"},
    {"value": "19", "label": "19: Gooi en Vechtstreek"},
    {"value": "20", "label": "20: Zeeland"},
    {"value": "21", "label": "21: Limburg-Zuid"},
    {"value": "23", "label": "23: Twente"},
    {"value": "24", "label": "24: Noord-Holland Noord"},
    {"value": "25", "label": "25: Haaglanden"},
    {"value": "26", "label": "26: Midden- en West Brabant"},
    {"value": "27", "label": "27: Flevoland"},
]

DISCIPLINE_OPTIONS = [
    {"value": "1", "label": "1: Politie"},
    {"value": "2", "label": "2: Brandweer"},
    {"value": "3", "label": "3: Ambulance"},
    {"value": "4", "label": "4: KNRM"},
    {"value": "5", "label": "5: Lifeliner"},
    {"value": "7", "label": "7: DARES"},
]

REGIO_VALUES = {option["value"] for option in REGIO_OPTIONS}
DISCIPLINE_VALUES = {option["value"] for option in DISCIPLINE_OPTIONS}


def _list_to_text(value: Any) -> str:
    """Convert a list-style config value to editable text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return ", ".join(str(item) for item in cv.ensure_list(value) if item)


def _value_to_list(value: Any) -> list[str]:
    """Convert comma, newline, or list values to a clean string list."""
    if not value:
        return []
    if isinstance(value, str):
        parts = value.replace("\n", ",").split(",")
        return [part.strip() for part in parts if part.strip()]
    return [str(item).strip() for item in cv.ensure_list(value) if str(item).strip()]


def _filter_allowed(values: list[str], allowed: set[str]) -> list[str]:
    """Keep only selector values that are still valid options."""
    return [value for value in values if value in allowed]


def _to_bool(value: Any) -> bool:
    """Normalize bool-ish config values."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    """Normalize imported and UI config data."""
    normalized = dict(config)
    normalized[CONF_NAME] = normalized.get(CONF_NAME) or DEFAULT_NAME
    normalized[CONF_ICON] = normalized.get(CONF_ICON) or DEFAULT_ICON
    normalized[CONF_PRIO1] = _to_bool(normalized.get(CONF_PRIO1, False))

    for key in TEXT_LIST_OPTIONS:
        normalized[key] = _value_to_list(normalized.get(key))

    normalized[CONF_REGIOS] = _filter_allowed(
        _value_to_list(normalized.get(CONF_REGIOS)), REGIO_VALUES
    )
    normalized[CONF_DISCIPLINES] = _filter_allowed(
        _value_to_list(normalized.get(CONF_DISCIPLINES)), DISCIPLINE_VALUES
    )

    return normalized


def _multi_select(options: list[dict[str, str]]) -> SelectSelector:
    """Create a multi-select dropdown selector."""
    return SelectSelector(
        {
            "options": options,
            "multiple": True,
            "mode": "dropdown",
        }
    )


def _options_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the schema for setup and options."""
    defaults = _normalize_config(defaults or {})
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults[CONF_NAME]): cv.string,
            vol.Optional(CONF_ICON, default=defaults[CONF_ICON]): IconSelector(),
            vol.Optional(
                CONF_CAPCODES, default=_list_to_text(defaults[CONF_CAPCODES])
            ): cv.string,
            vol.Optional(
                CONF_GEMEENTEN, default=_list_to_text(defaults[CONF_GEMEENTEN])
            ): cv.string,
            vol.Optional(CONF_REGIOS, default=defaults[CONF_REGIOS]): _multi_select(
                REGIO_OPTIONS
            ),
            vol.Optional(
                CONF_DISCIPLINES, default=defaults[CONF_DISCIPLINES]
            ): _multi_select(DISCIPLINE_OPTIONS),
            vol.Optional(CONF_PRIO1, default=defaults[CONF_PRIO1]): BooleanSelector(),
        }
    )


class P2000FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a P2000 config flow."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Create the options flow."""
        return P2000OptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ):
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
    ):
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

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ):
        """Manage P2000 options."""
        if user_input is not None:
            return self.async_create_entry(
                title="", data=_normalize_config(user_input)
            )

        defaults = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init", data_schema=_options_schema(defaults)
        )
