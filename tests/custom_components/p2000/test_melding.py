"""Tests for the melding helpers and the new-message tracker."""

from custom_components.p2000.melding import (
    MeldingTracker,
    event_attributes,
    event_type_for,
    flatten_meldingen,
    parse_prio1,
    to_float,
)


def _group(melding_id: str, *sub_ids: str) -> dict:
    """Build an API group: first message plus follow-up messages."""
    return {
        "id": melding_id,
        "melding": f"melding {melding_id}",
        "subitems": [{"id": sub_id, "melding": f"melding {sub_id}"} for sub_id in sub_ids],
    }


def test_to_float_accepts_comma_decimal_separator() -> None:
    """Test Dutch comma decimal values become floats."""
    assert to_float("52,12345") == 52.12345
    assert to_float("4.98765") == 4.98765
    assert to_float(5) == 5.0
    assert to_float("") is None
    assert to_float(None) is None
    assert to_float("not-a-number") is None


def test_parse_prio1_accepts_int_str_and_bool() -> None:
    """Test the prio1 field is interpreted regardless of API type."""
    assert parse_prio1(1) is True
    assert parse_prio1("1") is True
    assert parse_prio1(True) is True
    assert parse_prio1("true") is True
    assert parse_prio1(0) is False
    assert parse_prio1("0") is False
    assert parse_prio1(None) is False
    assert parse_prio1("") is False


def test_flatten_marks_follow_ups_with_parent_id() -> None:
    """Subitems become separate messages that point at the first message."""
    flat = flatten_meldingen([_group("10", "12", "13"), _group("11")])

    assert [(m["id"], m["parent_id"]) for m in flat] == [
        ("10", None),
        ("12", "10"),
        ("13", "10"),
        ("11", None),
    ]
    assert all("subitems" not in m for m in flat)


def test_flatten_skips_garbage_entries() -> None:
    """Non-dict entries from the API are ignored."""
    flat = flatten_meldingen([_group("10"), "oops", None])  # type: ignore[list-item]
    assert [m["id"] for m in flat] == ["10"]


def test_event_type_and_attributes() -> None:
    """A message with a parent is a vervolgmelding."""
    head, follow_up = flatten_meldingen([_group("10", "12")])[0:2]

    assert event_type_for(head) == "melding"
    assert event_type_for(follow_up) == "vervolgmelding"

    attrs = event_attributes(follow_up)
    assert attrs["id"] == "12"
    assert attrs["parent_id"] == "10"
    assert attrs["melding"] == "melding 12"


def test_tracker_first_update_only_records_existing_meldingen() -> None:
    """After a start or reload nothing is reported as new."""
    tracker = MeldingTracker()

    assert tracker.update([_group("10", "12"), _group("11")]) == []
    assert tracker.update([_group("10", "12"), _group("11")]) == []


def test_tracker_reports_each_new_message_oldest_first() -> None:
    """Two meldingen in one poll are both reported, oldest first."""
    tracker = MeldingTracker()
    tracker.update([_group("10")])

    new = tracker.update([_group("13"), _group("12"), _group("10")])

    assert [m["id"] for m in new] == ["12", "13"]


def test_tracker_reports_follow_up_once() -> None:
    """A follow-up on an older group is new once, then never again."""
    tracker = MeldingTracker()
    tracker.update([_group("10"), _group("11")])

    # Follow-up 12 on group 10 moves group 10 to the top of the list.
    after_follow_up = [_group("10", "12"), _group("11")]
    new = tracker.update(after_follow_up)
    assert [(m["id"], m["parent_id"]) for m in new] == [("12", "10")]

    # The list flips order again with no new message: nothing is reported.
    assert tracker.update([_group("11"), _group("10", "12")]) == []
    assert tracker.update(after_follow_up) == []


def test_tracker_does_not_repeat_after_empty_or_failed_poll() -> None:
    """An empty answer in between does not make old meldingen new again."""
    tracker = MeldingTracker()
    tracker.update([_group("10")])

    assert tracker.update([]) == []
    assert tracker.update([_group("10")]) == []


def test_tracker_empty_baseline_then_first_melding_is_new() -> None:
    """With no meldingen at start, the first one that arrives is reported."""
    tracker = MeldingTracker()
    assert tracker.update([]) == []

    assert [m["id"] for m in tracker.update([_group("10")])] == ["10"]


def test_tracker_limits_events_per_update_to_newest() -> None:
    """A backlog (e.g. after an outage) cannot flood automations."""
    tracker = MeldingTracker(max_new=3)
    tracker.update([_group("1")])

    new = tracker.update([_group(str(i)) for i in range(10, 1, -1)] + [_group("1")])

    assert [m["id"] for m in new] == ["8", "9", "10"]
    # The skipped older ones are not reported later either.
    assert tracker.update([_group(str(i)) for i in range(10, 1, -1)]) == []


def test_tracker_forgets_oldest_ids_beyond_limit() -> None:
    """The memory of seen ids is bounded."""
    tracker = MeldingTracker(seen_limit=3, max_new=100)
    tracker.update([])
    tracker.update([_group(str(i)) for i in range(1, 6)])

    assert len(tracker._seen) == 3


def test_tracker_ignores_messages_without_id() -> None:
    """A message without an id cannot be tracked and is skipped."""
    tracker = MeldingTracker()
    tracker.update([])

    assert tracker.update([{"melding": "no id"}, _group("10")]) == [
        {"id": "10", "melding": "melding 10", "parent_id": None}
    ]
