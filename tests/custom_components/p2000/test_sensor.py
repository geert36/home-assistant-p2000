"""Tests for P2000 sensor helpers."""

from types import SimpleNamespace

from custom_components.p2000.sensor import P2000Sensor, _parse_prio1, _to_float


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


def test_to_float_accepts_comma_decimal_separator() -> None:
    """Test Dutch comma decimal values become floats."""
    assert _to_float("52,12345") == 52.12345
    assert _to_float("4.98765") == 4.98765
    assert _to_float(5) == 5.0
    assert _to_float("") is None
    assert _to_float(None) is None
    assert _to_float("not-a-number") is None


def test_parse_prio1_accepts_int_str_and_bool() -> None:
    """Test the prio1 field is interpreted regardless of API type."""
    assert _parse_prio1(1) is True
    assert _parse_prio1("1") is True
    assert _parse_prio1(True) is True
    assert _parse_prio1("true") is True
    assert _parse_prio1(0) is False
    assert _parse_prio1("0") is False
    assert _parse_prio1(None) is False
    assert _parse_prio1("") is False
