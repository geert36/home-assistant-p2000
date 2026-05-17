"""Tests for the P2000 config flow helpers."""

from homeassistant.const import CONF_NAME

from custom_components.p2000.config_flow import _normalize_config
from custom_components.p2000.const import (
    CONF_CAPCODES,
    CONF_DISCIPLINES,
    CONF_GEMEENTEN,
    CONF_ICON,
    CONF_PRIO1,
    CONF_REGIOS,
    DEFAULT_ICON,
)


def test_normalize_config_converts_text_fields_to_lists() -> None:
    """Test comma and newline separated filters are normalized."""
    result = _normalize_config(
        {
            CONF_NAME: "P2000 Test",
            CONF_ICON: "mdi:alarm-light",
            CONF_CAPCODES: "010101, 020202\n030303",
            CONF_GEMEENTEN: ["Amsterdam", "Utrecht"],
            CONF_REGIOS: "10,25,999",
            CONF_DISCIPLINES: ["2", "3", "99"],
            CONF_PRIO1: "true",
        }
    )

    assert result[CONF_CAPCODES] == ["010101", "020202", "030303"]
    assert result[CONF_GEMEENTEN] == ["Amsterdam", "Utrecht"]
    assert result[CONF_REGIOS] == ["10", "25"]
    assert result[CONF_DISCIPLINES] == ["2", "3"]
    assert result[CONF_PRIO1] is True


def test_normalize_config_applies_defaults() -> None:
    """Test missing values get safe defaults."""
    result = _normalize_config({})

    assert result[CONF_NAME] == "p2000"
    assert result[CONF_ICON] == DEFAULT_ICON
    assert result[CONF_CAPCODES] == []
    assert result[CONF_GEMEENTEN] == []
    assert result[CONF_REGIOS] == []
    assert result[CONF_DISCIPLINES] == []
    assert result[CONF_PRIO1] is False
