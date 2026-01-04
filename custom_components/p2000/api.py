import asyncio
import json
import logging
from typing import Optional, Dict, Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

class P2000Api:
    url = "https://beta.alarmeringdroid.nl/api2/find/"

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def get_data(
        self,
        api_filter: Dict[str, Any],
        retries: int = 3,
        timeout: int = 10,
    ) -> Optional[Dict[str, Any]]:
        query_string = json.dumps(api_filter)
        url = f"{self.url}{query_string}"

        client_timeout = aiohttp.ClientTimeout(total=timeout)

        for attempt in range(1, retries + 1):
            try:
                _LOGGER.debug(
                    "API request attempt %s/%s: %s",
                    attempt,
                    retries,
                    url,
                )

                async with self.session.get(
                    url,
                    allow_redirects=False,
                    timeout=client_timeout,
                ) as response:
                
                    if response.status >= 400:
                        if response.status in (408, 429) or response.status >= 500:
                            raise aiohttp.ClientResponseError(
                                request_info=response.request_info,
                                history=response.history,
                                status=response.status,
                                message="Retryable HTTP error",
                            )
                        _LOGGER.error("Non-retryable HTTP error: %s", response.status)
                        return None
                
                    try:
                        text = await response.text()  # <-- hier haakjes + await
                        data = json.loads(text)
                    except json.JSONDecodeError as err:
                        _LOGGER.error(
                            "JSON decode failed at pos %s: %s",
                            err.pos,
                            err.msg,
                        )
                        _LOGGER.debug("Raw response (first 500 chars): %s", text[:500])
                        return None

                    meldingen = data.get("meldingen")
                    if not meldingen:
                        _LOGGER.debug("No notifications found in API response.")
                        return None

                    result = meldingen[0] if isinstance(meldingen, list) else None
                    if not isinstance(result, dict):
                        return None

                    # Rename lat & lon safely
                    if "lat" in result:
                        result["latitude"] = result.pop("lat")
                    if "lon" in result:
                        result["longitude"] = result.pop("lon")

                    return result

            except asyncio.TimeoutError:
                _LOGGER.warning(
                    "API timeout (attempt %s/%s)",
                    attempt,
                    retries,
                )

            except aiohttp.ClientError as e:
                _LOGGER.warning(
                    "API client error (attempt %s/%s): %s",
                    attempt,
                    retries,
                    e,
                )

            # Exponential backoff
            if attempt < retries:
                sleep_time = attempt * 2
                _LOGGER.debug("Retrying in %s seconds", sleep_time)
                await asyncio.sleep(sleep_time)

        _LOGGER.error("API request failed after %s attempts", retries)
        return None
