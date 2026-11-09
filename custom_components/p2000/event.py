"""Event entity that fires once for every new P2000 message."""
from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_ICON,
    DEFAULT_ICON,
    DEFAULT_NAME,
    EVENT_MELDING,
    EVENT_VERVOLGMELDING,
)
from .coordinator import P2000ConfigEntry, P2000DataUpdateCoordinator
from .entity import build_device_info
from .melding import event_attributes, event_type_for


async def async_setup_entry(
    hass: HomeAssistant,
    entry: P2000ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the P2000 event entity from a config entry."""
    config = {**entry.data, **entry.options}

    async_add_entities(
        [
            P2000EventEntity(
                entry.runtime_data,
                entry.entry_id,
                config.get(CONF_NAME, DEFAULT_NAME),
                config.get(CONF_ICON, DEFAULT_ICON),
            )
        ]
    )


class P2000EventEntity(CoordinatorEntity, EventEntity):
    """Fires an event for every new message, so none is missed or repeated."""

    _attr_event_types = [EVENT_MELDING, EVENT_VERVOLGMELDING]

    def __init__(
        self,
        coordinator: P2000DataUpdateCoordinator,
        entry_id: str,
        name: str,
        icon: str,
    ) -> None:
        super().__init__(coordinator)

        self._attr_name = f"{name} melding"
        self._attr_icon = icon
        self._attr_unique_id = f"p2000_{entry_id}_event"
        self._attr_device_info = build_device_info(entry_id, name)

    @property
    def available(self) -> bool:
        """Stay available during API failures.

        No events can arrive while the API is down, and going unavailable
        and back would only add state changes that automations might see.
        The outage is visible on the sensor via ``last_update_success``.
        """
        return True

    @callback
    def _handle_coordinator_update(self) -> None:
        """Fire an event for each message that is new in this update."""
        for melding in self.coordinator.new_meldingen:
            self._trigger_event(event_type_for(melding), event_attributes(melding))
            self.async_write_ha_state()
