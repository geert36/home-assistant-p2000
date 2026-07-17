"""Tests for P2000 sensor helpers."""

from custom_components.p2000.sensor import _parse_prio1, _to_float


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
