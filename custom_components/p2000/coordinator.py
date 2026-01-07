from datetime import timedelta
import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

class P2000DataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching P2000 data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: Any,
        api_filter: Dict[str, Any],
        update_interval: int = 30,
    ) -> None:
        self.api = api
        self.api_filter = api_filter

        super().__init__(
            hass,
            _LOGGER,
            name="P2000 Coordinator",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from API and handle exceptions."""
        try:
            _LOGGER.debug(
                "Fetching P2000 data with filter: %s",
                self.api_filter,
            )

            result = await self.api.get_data(self.api_filter)

            if not result:
                return {}

            return result

        except Exception as err:
            raise UpdateFailed(
                f"P2000 API request failed: {err}"
            ) from err
