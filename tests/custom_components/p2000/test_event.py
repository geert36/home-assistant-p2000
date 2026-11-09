"""Tests for the P2000 event entity."""

from types import SimpleNamespace

from custom_components.p2000.event import P2000EventEntity
from custom_components.p2000.melding import flatten_meldingen


def _entity(new_meldingen: list[dict]) -> tuple[P2000EventEntity, list[dict]]:
    """Build an event entity; the list collects the state at every write."""
    coordinator = SimpleNamespace(
        new_meldingen=new_meldingen, data={}, last_update_success=True
    )
    entity = P2000EventEntity(coordinator, "entry", "Brandweer", "mdi:fire-truck")

    written: list[dict] = []
    entity.async_write_ha_state = lambda: written.append(dict(entity.state_attributes))
    return entity, written


def test_fires_one_event_per_new_message_with_matching_type() -> None:
    """A first message and a follow-up each produce their own event."""
    messages = flatten_meldingen(
        [{"id": "10", "melding": "eerste", "subitems": [{"id": "12", "melding": "vervolg"}]}]
    )
    entity, written = _entity(messages)

    entity._handle_coordinator_update()

    assert [(w["event_type"], w["id"], w["parent_id"]) for w in written] == [
        ("melding", "10", None),
        ("vervolgmelding", "12", "10"),
    ]
    assert written[0]["melding"] == "eerste"


def test_does_nothing_without_new_meldingen() -> None:
    """Regular polls without news (or after a failure) fire nothing."""
    entity, written = _entity([])

    entity._handle_coordinator_update()

    assert written == []


def test_stays_available_when_the_api_fails() -> None:
    """No spurious unavailable/available transitions during an outage."""
    entity, _ = _entity([])
    entity.coordinator.last_update_success = False

    assert entity.available is True


def test_entity_identity() -> None:
    """Name, unique id and event types."""
    entity, _ = _entity([])

    assert entity.name == "Brandweer melding"
    assert entity.unique_id == "p2000_entry_event"
    assert entity.event_types == ["melding", "vervolgmelding"]
