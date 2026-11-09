from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import P2000ApiError
from .melding import MeldingTracker

_LOGGER = logging.getLogger(__name__)


class P2000DataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching P2000 data.

    ``data`` is the group that was most recently active (what the sensor
    shows). ``new_meldingen`` holds the messages that appeared in the latest
    update, oldest first, and is empty after a failed update.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: Any,
        api_filter: dict[str, Any],
        update_interval: int = 30,
    ) -> None:
        """Initialize the update coordinator."""
        self.api = api
        self.api_filter = api_filter
        self.new_meldingen: list[dict[str, Any]] = []
        self._tracker = MeldingTracker()

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name="P2000 Coordinator",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API and handle exceptions."""
        # Listeners also run after a failed update; make sure they cannot
        # see the messages of the previous update a second time.
        self.new_meldingen = []

        _LOGGER.debug(
            "Fetching P2000 data with filter: %s",
            self.api_filter,
        )

        try:
            groups = await self.api.get_meldingen(self.api_filter)
        except P2000ApiError as err:
            raise UpdateFailed(f"P2000 API request failed: {err}") from err

        self.new_meldingen = self._tracker.update(groups)

        if not groups:
            _LOGGER.debug("No notifications for this filter, keeping last known state")
            return self.data or {}

        return groups[0]


type P2000ConfigEntry = ConfigEntry[P2000DataUpdateCoordinator]
