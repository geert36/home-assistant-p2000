"""Diagnostics support for the P2000 integration."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.json import JSONEncoder

from .const import CONF_CAPCODES, CONF_GEMEENTEN, DOMAIN

TO_REDACT = {CONF_CAPCODES, CONF_GEMEENTEN}


def _redact_data(data: dict[str, Any]) -> dict[str, Any]:
    """Redact user-specific filter values from diagnostics."""
    redacted = dict(data)
    for key in TO_REDACT:
        if key in redacted:
            redacted[key] = "**REDACTED**"
    return redacted


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
