"""The p2000 sensor integration."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_CAPCODES,
    CONF_DISCIPLINES,
    CONF_GEMEENTEN,
    CONF_ICON,
    CONF_PRIO1,
    CONF_REGIOS,
    DEFAULT_ICON,
    DEFAULT_NAME,
)

PLATFORMS: list[Platform] = [Platform.SENSOR]
CURRENT_CONFIG_ENTRY_VERSION = 2


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up P2000 from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a P2000 config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload P2000 after options changed."""
    await hass.config_entries.async_reload(entry.entry_id)


def _value_to_list(value: Any) -> list[str]:
    """Convert comma, newline, or list values to a clean string list."""
    if not value:
        return []
    if isinstance(value, str):
        parts = value.replace("\n", ",").split(",")
        return [part.strip() for part in parts if part.strip()]
    return [str(item).strip() for item in value if str(item).strip()]


def _to_bool(value: Any) -> bool:
    """Normalize bool-ish values."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _migrate_mapping(values: dict[str, Any]) -> dict[str, Any]:
    """Normalize old config data/options to the current storage shape."""
    migrated = dict(values)
    migrated[CONF_NAME] = migrated.get(CONF_NAME) or DEFAULT_NAME
    migrated[CONF_ICON] = migrated.get(CONF_ICON) or DEFAULT_ICON
    migrated[CONF_CAPCODES] = _value_to_list(migrated.get(CONF_CAPCODES))
    migrated[CONF_GEMEENTEN] = _value_to_list(migrated.get(CONF_GEMEENTEN))
    migrated[CONF_REGIOS] = _value_to_list(migrated.get(CONF_REGIOS))
    migrated[CONF_DISCIPLINES] = _value_to_list(migrated.get(CONF_DISCIPLINES))
    migrated[CONF_PRIO1] = _to_bool(migrated.get(CONF_PRIO1, False))
    return migrated


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old P2000 config entries."""
    if entry.version >= CURRENT_CONFIG_ENTRY_VERSION:
        return True

    hass.config_entries.async_update_entry(
        entry,
        data=_migrate_mapping(entry.data),
        options=_migrate_mapping(entry.options),
        version=CURRENT_CONFIG_ENTRY_VERSION,
    )
    return True
