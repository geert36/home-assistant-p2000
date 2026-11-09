"""Diagnostics support for the P2000 integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_CAPCODES, CONF_GEMEENTEN, DOMAIN
from .coordinator import P2000ConfigEntry

# User-specific filter values.
TO_REDACT = {CONF_CAPCODES, CONF_GEMEENTEN}

# Where an incident took place and what exactly was reported. The structure
# and the remaining fields (id, dienst, regio, datum, tijd, prio1, ...) are
# enough to debug problems without publishing addresses in a bug report.
TO_REDACT_MELDING = {
    "melding",
    "tekstmelding",
    "plaats",
    "postcode",
    "straat",
    "lat",
    "lon",
    "latitude",
    "longitude",
    "capcodes",
    "capstring",
}


def _redact_data(data: dict[str, Any]) -> dict[str, Any]:
    """Redact user-specific filter values from diagnostics."""
    return async_redact_data(data, TO_REDACT)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: P2000ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    update_interval = coordinator.update_interval

    return {
        "domain": DOMAIN,
        "entry": {
            "title": entry.title,
            "version": entry.version,
            "minor_version": getattr(entry, "minor_version", 1),
            "data": _redact_data(dict(entry.data)),
            "options": _redact_data(dict(entry.options)),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval_seconds": (
                update_interval.total_seconds() if update_interval else None
            ),
            "api_filter": _redact_data(dict(coordinator.api_filter)),
            "last_melding": async_redact_data(
                dict(coordinator.data or {}), TO_REDACT_MELDING
            ),
        },
    }
