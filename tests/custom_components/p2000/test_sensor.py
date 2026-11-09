"""Tests for the P2000 sensor."""

from types import SimpleNamespace

from custom_components.p2000.sensor import P2000Sensor


def _sensor(data: dict | None, last_update_success: bool) -> P2000Sensor:
    """Build a sensor around a minimal stand-in for the coordinator."""
    coordinator = SimpleNamespace(data=data, last_update_success=last_update_success)
    return P2000Sensor(coordinator, "entry", "p2000", "mdi:ambulance")


def test_available_with_last_known_data_after_failed_update() -> None:
    """A transient API failure must not make the sensor unavailable."""
    sensor = _sensor({"id": "1", "melding": "Brand"}, last_update_success=False)

    assert sensor.available is True
    assert sensor.native_value == "1"
    assert sensor.extra_state_attributes["melding"] == "Brand"
    assert sensor.extra_state_attributes["last_update_success"] is False


def test_unavailable_without_data_after_failed_update() -> None:
    """Without any data (e.g. first start) the default behaviour applies."""
    assert _sensor(None, last_update_success=False).available is False
    assert _sensor({}, last_update_success=False).available is False


def test_available_without_data_after_successful_update() -> None:
    """No notifications yet, but the API works: sensor is available."""
    assert _sensor({}, last_update_success=True).available is True


def test_last_update_success_attribute_true_when_healthy() -> None:
    """The freshness flag is true after a successful update."""
    sensor = _sensor({"id": "1"}, last_update_success=True)

    assert sensor.extra_state_attributes["last_update_success"] is True


def test_sensor_attributes_unchanged_for_existing_users() -> None:
    """The attribute names automations rely on must stay the same."""
    sensor = _sensor(
        {
            "id": "1",
            "melding": "Brand",
            "capcodes": [{"capcode": "123", "omschrijving": "Post"}],
            "prio1": "1",
            "latitude": "52,5",
            "longitude": "6.1",
        },
        last_update_success=True,
    )

    attrs = sensor.extra_state_attributes

    assert set(attrs) == {
        "last_update_success",
        "melding",
        "tekstmelding",
        "dienst",
        "regio",
        "plaats",
        "postcode",
        "straat",
        "datum",
        "tijd",
        "prio1",
        "brandinfo",
        "grip",
        "capcodes",
        "capcodes_str",
        "latitude",
        "longitude",
    }
    assert attrs["prio1"] is True
    assert attrs["capcodes_str"] == "123 (Post)"
    assert attrs["latitude"] == 52.5
