"""Tests for P2000 integration setup helpers."""

from homeassistant.const import CONF_NAME

from custom_components.p2000 import _migrate_mapping
from custom_components.p2000.const import (
    CONF_CAPCODES,
    CONF_DISCIPLINES,
    CONF_GEMEENTEN,
    CONF_ICON,
    CONF_PRIO1,
    CONF_REGIOS,
    DEFAULT_ICON,
)


def test_migrate_mapping_normalizes_old_storage_shape() -> None:
    """Test old string-based values migrate to the current storage shape."""
    result = _migrate_mapping(
        {
            CONF_NAME: "P2000",
            CONF_CAPCODES: "123,456",
            CONF_GEMEENTEN: "Amsterdam\nUtrecht",
            CONF_REGIOS: "10,25",
            CONF_DISCIPLINES: "2",
            CONF_PRIO1: "on",
        }
    )

    assert result[CONF_CAPCODES] == ["123", "456"]
    assert result[CONF_GEMEENTEN] == ["Amsterdam", "Utrecht"]
    assert result[CONF_REGIOS] == ["10", "25"]
    assert result[CONF_DISCIPLINES] == ["2"]
    assert result[CONF_PRIO1] is True
    assert result[CONF_ICON] == DEFAULT_ICON
