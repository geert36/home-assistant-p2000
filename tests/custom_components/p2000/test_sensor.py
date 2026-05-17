"""Tests for P2000 sensor helpers."""

from custom_components.p2000.sensor import _to_float


def test_to_float_accepts_comma_decimal_separator() -> None:
    """Test Dutch comma decimal values become floats."""
    assert _to_float("52,12345") == 52.12345
    assert _to_float("4.98765") == 4.98765
    assert _to_float(5) == 5.0
    assert _to_float("") is None
    assert _to_float(None) is None
    assert _to_float("not-a-number") is None
