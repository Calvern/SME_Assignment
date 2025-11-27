# tests/test_deprecated_config_loading.py

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config import _log_deprecated_config, _DEPRECATED_CONFIG_OPTIONS
from homeassistant.core import HomeAssistant


class DummyHass:
    """Minimal hass stub for unit tests."""
    # We don’t actually need anything on hass for _log_deprecated_config today.
    pass


def test_log_deprecated_config_emits_warning_for_known_option(caplog) -> None:
    """Deprecated options should log a clear warning with guidance."""
    # Make sure we have an entry in the dictionary to test against.
    # These must match what you put in _DEPRECATED_CONFIG_OPTIONS.
    assert ("sensor", "old_option") in _DEPRECATED_CONFIG_OPTIONS

    caplog.set_level(logging.WARNING)

    config: dict[str, Any] = {
        "sensor": {
            "old_option": True,
            "name": "test_sensor",
        }
    }

    hass: HomeAssistant = DummyHass()  # type: ignore[assignment]

    _log_deprecated_config(hass, config)

    messages = "\n".join(record.getMessage() for record in caplog.records)

    assert "deprecated" in messages.lower()
    assert "sensor" in messages
    assert "old_option" in messages
    # Ensure the guidance text from the dictionary is present
    assert _DEPRECATED_CONFIG_OPTIONS[("sensor", "old_option")] in messages


def test_log_deprecated_config_ignores_unknown_options(caplog) -> None:
    """Non-deprecated options should not cause warnings."""
    caplog.set_level(logging.WARNING)

    config = {
        "sensor": {
            "name": "no_deprecations_here",
        }
    }

    hass: HomeAssistant = DummyHass()  # type: ignore[assignment]

    _log_deprecated_config(hass, config)

    # No warnings expected when no deprecated options are present
    assert not caplog.records
