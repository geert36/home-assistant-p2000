from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from urllib.parse import quote

import aiohttp

_LOGGER = logging.getLogger(__name__)

USER_AGENT = "home-assistant-p2000 (https://github.com/geert36/home-assistant-p2000)"


class P2000ApiError(Exception):
    """Raised when the P2000 API request fails."""


def _normalize_coordinates(melding: dict[str, Any]) -> None:
    """Rename the API's lat/lon keys to latitude/longitude, in place."""
    if "lat" in melding and "latitude" not in melding:
        melding["latitude"] = melding.pop("lat")
    if "lon" in melding and "longitude" not in melding:
        melding["longitude"] = melding.pop("lon")


class P2000Api:
    """Client for the P2000 API."""

    url = "https://beta.alarmeringdroid.nl/api2/find/"

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self.session = session

    async def get_meldingen(
        self,
        api_filter: dict[str, Any],
        retries: int = 3,
        timeout: int = 10,
    ) -> list[dict[str, Any]]:
        """Fetch the recent P2000 notifications, most recent activity first.

        Each item is a group: the first message of an incident, with later
        pager messages for the same incident in ``subitems``.

        Returns an empty list when there are no notifications for the filter.
        Raises P2000ApiError when the request ultimately fails.
        """
        query_string = quote(json.dumps(api_filter, separators=(",", ":")), safe="")
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
                    headers={"User-Agent": USER_AGENT},
                ) as response:
                    if response.status >= 400:
                        if response.status in (408, 429) or response.status >= 500:
                            raise aiohttp.ClientResponseError(
                                request_info=response.request_info,
                                history=response.history,
                                status=response.status,
                                message="Retryable HTTP error",
                            )
                        raise P2000ApiError(
                            f"Non-retryable HTTP error: {response.status}"
                        )

                    try:
                        data = await response.json(content_type=None)
                    except (aiohttp.ContentTypeError, json.JSONDecodeError) as err:
                        text = await response.text()
                        _LOGGER.debug("Raw response (first 500 chars): %s", text[:500])
                        raise P2000ApiError(f"JSON decode failed: {err}") from err

                    if not isinstance(data, dict):
                        raise P2000ApiError(
                            f"Unexpected API response type: {type(data).__name__}"
                        )

                    meldingen = data.get("meldingen")
                    if not isinstance(meldingen, list) or not meldingen:
                        _LOGGER.debug("No notifications found in API response.")
                        return []

                    groups = [item for item in meldingen if isinstance(item, dict)]
                    for group in groups:
                        _normalize_coordinates(group)
                        for sub in group.get("subitems") or []:
                            if isinstance(sub, dict):
                                _normalize_coordinates(sub)

                    return groups

            except asyncio.TimeoutError:
                _LOGGER.warning(
                    "API timeout (attempt %s/%s)",
                    attempt,
                    retries,
                )

            except aiohttp.ClientError as err:
                _LOGGER.warning(
                    "API client error (attempt %s/%s): %s",
                    attempt,
                    retries,
                    err,
                )

            if attempt < retries:
                sleep_time = attempt * 2
                _LOGGER.debug("Retrying in %s seconds", sleep_time)
                await asyncio.sleep(sleep_time)

        raise P2000ApiError(f"API request failed after {retries} attempts")
