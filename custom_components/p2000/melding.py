"""Helpers for working with P2000 meldingen (notifications)."""
from __future__ import annotations

from collections import OrderedDict
import logging
from typing import Any

from .const import (
    EVENT_MELDING,
    EVENT_VERVOLGMELDING,
    MAX_EVENTS_PER_UPDATE,
    SEEN_IDS_LIMIT,
)

_LOGGER = logging.getLogger(__name__)


def to_float(value: Any) -> float | None:
    """Convert API coordinates to floats, accepting comma decimals."""
    if value in (None, ""):
        return None
    if isinstance(value, str):
        value = value.strip().replace(",", ".")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_prio1(value: Any) -> bool:
    """Interpret the prio1 field, which the API may send as int, str, or bool."""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def melding_attributes(data: dict[str, Any]) -> dict[str, Any]:
    """Build the user-facing attributes for a single melding."""
    capcodes = data.get("capcodes") or []

    return {
        "melding": data.get("melding"),
        "tekstmelding": data.get("tekstmelding"),
        "dienst": data.get("dienst", "Onbekend"),
        "regio": data.get("regio", "Onbekend"),
        "plaats": data.get("plaats"),
        "postcode": data.get("postcode", "Onbekend"),
        "straat": data.get("straat"),
        "datum": data.get("datum"),
        "tijd": data.get("tijd"),
        "prio1": parse_prio1(data.get("prio1")),
        "brandinfo": data.get("brandinfo", "Onbekend"),
        "grip": data.get("grip"),
        "capcodes": capcodes,
        "capcodes_str": ", ".join(
            f"{c.get('capcode')} ({c.get('omschrijving')})"
            for c in capcodes
            if isinstance(c, dict)
        ),
        "latitude": to_float(data.get("latitude")),
        "longitude": to_float(data.get("longitude")),
    }


def event_type_for(melding: dict[str, Any]) -> str:
    """Return the event type: a follow-up message has a parent melding."""
    return EVENT_VERVOLGMELDING if melding.get("parent_id") else EVENT_MELDING


def event_attributes(melding: dict[str, Any]) -> dict[str, Any]:
    """Build the attributes that accompany a melding event."""
    return {
        "id": melding.get("id"),
        "parent_id": melding.get("parent_id"),
        **melding_attributes(melding),
    }


def flatten_meldingen(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten API groups into single messages.

    The API groups follow-up pager messages for the same incident as
    ``subitems`` of the first message. Every message has its own id; a
    follow-up gets ``parent_id`` set to the id of the first message.
    """
    flat: list[dict[str, Any]] = []
    for group in groups:
        if not isinstance(group, dict):
            continue

        head = {key: value for key, value in group.items() if key != "subitems"}
        head["parent_id"] = None
        flat.append(head)

        for sub in group.get("subitems") or []:
            if isinstance(sub, dict):
                flat.append({**sub, "parent_id": group.get("id")})

    return flat


def _melding_id(melding: dict[str, Any]) -> str | None:
    """Return the melding id as a string, or None when it has none."""
    value = melding.get("id")
    if value in (None, ""):
        return None
    return str(value)


def _id_sort_key(melding_id: str) -> tuple[int, int, str]:
    """Sort numeric ids numerically (oldest first), others after them."""
    if melding_id.isdigit():
        return (0, int(melding_id), "")
    return (1, 0, melding_id)


class MeldingTracker:
    """Detect messages that were not seen in earlier updates.

    API ids are not monotonic (the list is ordered by last activity and a
    follow-up moves an older group to the top), so new messages are found by
    remembering the ids that were already seen instead of comparing ids.
    """

    def __init__(
        self,
        seen_limit: int = SEEN_IDS_LIMIT,
        max_new: int = MAX_EVENTS_PER_UPDATE,
    ) -> None:
        """Initialize the tracker."""
        self._seen: OrderedDict[str, None] | None = None
        self._seen_limit = seen_limit
        self._max_new = max_new

    def update(self, groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return messages not seen before, oldest first.

        The first call only records what is currently there: after a start
        or reload the existing meldingen are not reported as new.
        """
        messages = [
            (message_id, message)
            for message in flatten_meldingen(groups)
            if (message_id := _melding_id(message)) is not None
        ]

        if self._seen is None:
            self._seen = OrderedDict.fromkeys(message_id for message_id, _ in messages)
            return []

        new = [
            (message_id, message)
            for message_id, message in messages
            if message_id not in self._seen
        ]
        new.sort(key=lambda item: _id_sort_key(item[0]))

        for message_id, _ in new:
            self._seen[message_id] = None
        while len(self._seen) > self._seen_limit:
            self._seen.popitem(last=False)

        if len(new) > self._max_new:
            _LOGGER.warning(
                "%s new meldingen in one update, only reporting the newest %s",
                len(new),
                self._max_new,
            )
            new = new[-self._max_new :]

        return [message for _, message in new]
