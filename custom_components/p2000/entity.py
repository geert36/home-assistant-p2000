"""Shared entity helpers."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import DOMAIN


def build_device_info(entry_id: str, name: str) -> DeviceInfo:
    """Group the sensor and the event entity of one entry under one device."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name=name,
        manufacturer="alarmeringdroid.nl",
        model="P2000 meldingen",
        entry_type=DeviceEntryType.SERVICE,
    )
