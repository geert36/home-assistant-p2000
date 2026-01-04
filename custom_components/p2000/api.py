import json
import logging
from aiohttp import ClientTimeout
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

class P2000Api:
    url = "https://beta.alarmeringdroid.nl/api2/find/"

    def __init__(self, hass):
        self.hass = hass
        self.session = async_get_clientsession(hass)

    async def get_data(self, apiFilter):
        try:
            async with self.session.get(
                self.url + json.dumps(apiFilter),
                timeout=ClientTimeout(total=10),
                allow_redirects=False
            ) as response:

                if response.status != 200:
                    _LOGGER.error(
                        "P2000 API error (%s) for filter %s",
                        response.status,
                        apiFilter,
                    )
                    return None

                data = await response.json()

        except Exception as err:
            _LOGGER.exception("P2000 API request failed: %s", err)
            return None

        if not data.get("meldingen"):
            return None

        # Eerste melding
        result = data["meldingen"][0]
        if result is None:
            return None

        # lat / lon hernoemen
        result["latitude"] = result.pop("lat", None)
        result["longitude"] = result.pop("lon", None)

        return result
