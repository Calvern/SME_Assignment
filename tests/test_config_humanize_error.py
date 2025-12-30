# tests/test_config_humanize_error.py

from __future__ import annotations

from typing import Any, Hashable, List

import voluptuous as vol
from voluptuous.humanize import humanize_error as vol_humanize_error

from homeassistant.config import humanize_error
from homeassistant.core import HomeAssistant


class DummyHass:  
    """Minimal hass stub for tests."""
    pass


def _make_invalid(
    message: str, path: List[Hashable] | None = None
) -> vol.Invalid:
    """Construct a vol.Invalid with a fixed path for testing."""
    return vol.Invalid(message, path=path or [])


def test_humanize_error_preserves_core_message() -> None:
    """The new implementation should still contain the original human message."""
    data = {"sensor": {"name": 123}}
    schema = vol.Schema({"sensor": {"name": str}})

    # Trigger a simple type error.
    try:
        schema(data)
    except vol.MultipleInvalid as err:
        exc = err.errors[0]

    hass: HomeAssistant = DummyHass()  # <--- use DummyHass

    before = vol_humanize_error(data, exc)
    after = humanize_error(
        hass=hass,
        validation_error=exc,
        domain="sensor",
        config=data,
        link=None,
    )

    assert exc.error_message in before
    assert exc.error_message in after
    assert "got" in before.lower()
    assert "got" in after.lower() or "offending value" in after.lower()


def test_humanize_error_undefined_variable() -> None:
    """Undefined template variables should be clearly identified."""
    message = "TemplateError: UndefinedError: 'value_json' is undefined"
    exc = _make_invalid(message, path=["sensor", "my_rest_sensor", "value_template"])

    config = {
        "sensor": {
            "my_rest_sensor": {
                "platform": "rest",
                "value_template": "{{ value_json.missing }}",
            }
        }
    }

    hass: HomeAssistant = DummyHass()  # <--- use DummyHass

    msg = humanize_error(
        hass=hass,
        validation_error=exc,
        domain="rest",
        config=config,
        link="https://www.home-assistant.io/docs/configuration/templating/",
    )

    assert "undefined variable" in msg.lower()
    assert "UndefinedError" in msg
    assert "'value_json' is undefined" in msg
    assert "Offending value" in msg
    assert "hint" in msg.lower()
    assert "https://www.home-assistant.io/docs/configuration/templating/" in msg


def test_humanize_error_invalid_schema_missing_key() -> None:
    """Missing required keys should be reported as invalid schema with location."""
    schema = vol.Schema(
        {
            vol.Required("platform"): str,
            vol.Required("name"): str,
        }
    )

    bad_config = {
        "platform": "template",
    }

    try:
        schema(bad_config)
    except vol.MultipleInvalid as err:
        exc = err.errors[0]

    hass: HomeAssistant = DummyHass()  # <--- use DummyHass

    msg = humanize_error(
        hass=hass,
        validation_error=exc,
        domain="sensor",
        config=bad_config,
        link="https://www.home-assistant.io/docs/configuration/",
    )

    lower = msg.lower()
    assert "invalid schema" in lower
    assert "required key" in lower
    assert "location:" in lower
    assert "hint:" in lower
    assert "https://www.home-assistant.io/docs/configuration/" in msg
