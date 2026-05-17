"""Diagnostics support for the P2000 integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_CAPCODES, CONF_GEMEENTEN, DOMAIN

TO_REDACT = {CONF_CAPCODES, CONF_GEMEENTEN}


def _redact_data(data: dict[str, Any]) -> dict[str, Any]:
    """Redact user-specific filter values from diagnostics."""
    return async_redact_data(data, TO_REDACT)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    return {
        "domain": DOMAIN,
        "entry": {
            "title": entry.title,
            "version": entry.version,
            "minor_version": getattr(entry, "minor_version", 1),
            "data": _redact_data(dict(entry.data)),
            "options": _redact_data(dict(entry.options)),
        },
    }
