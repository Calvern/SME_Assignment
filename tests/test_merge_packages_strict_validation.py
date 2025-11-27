import pytest
from typing import Any, List

from homeassistant import config as config_util
from homeassistant.const import CONF_PACKAGES
from homeassistant.core import HomeAssistant, DOMAIN as HOMEASSISTANT_DOMAIN


@pytest.mark.asyncio
async def test_merge_packages_valid_list_items(hass: HomeAssistant) -> None:
    """Valid list-based items from packages are merged without errors."""
    packages: dict[str, Any] = {
        "valid_pkg": {
            "light": [
                {"platform": "test1"},
                {"platform": "test2"},
            ]
        },
    }
    config: dict[str, Any] = {
        HOMEASSISTANT_DOMAIN: {CONF_PACKAGES: packages},
        "light": [
            {"platform": "base"},
        ],
    }

    log_messages: List[str] = []

    def capture_log(
        hass_: HomeAssistant,
        pack_name: str,
        comp_name: str | None,
        conf: dict,
        msg: str,
    ) -> None:
        log_messages.append(msg)

    await config_util.merge_packages_config(
        hass,
        config,
        packages,
        _log_pkg_error=capture_log,
    )

    # No errors should be logged for a fully valid package
    assert log_messages == []

    # All items should be present: existing + two from the package
    assert "light" in config
    assert isinstance(config["light"], list)
    assert [item["platform"] for item in config["light"]] == [
        "base",
        "test1",
        "test2",
    ]


@pytest.mark.asyncio
async def test_merge_packages_invalid_list_item_logged_and_skipped(
    hass: HomeAssistant,
) -> None:
    """Invalid list items in list-based integrations should be logged and skipped."""
    # Bad package: light config contains a scalar in the list instead of a dict
    packages: dict[str, Any] = {
        "bad_pkg": {
            "light": [
                "not-a-dict",  # invalid item
                {"platform": "test-ok"},  # valid item
            ]
        },
    }
    config: dict[str, Any] = {
        HOMEASSISTANT_DOMAIN: {CONF_PACKAGES: packages},
    }

    log_messages: List[str] = []

    def capture_log(
        hass_: HomeAssistant,
        pack_name: str,
        comp_name: str | None,
        conf: dict,
        msg: str,
    ) -> None:
        log_messages.append(msg)

    await config_util.merge_packages_config(
        hass,
        config,
        packages,
        _log_pkg_error=capture_log,
    )

    # We should log exactly one detailed error for the invalid list item
    assert len(log_messages) == 1
    assert "integration 'light' in package 'bad_pkg'" in log_messages[0]
    assert "invalid list item at index 0" in log_messages[0]
    assert "expected a dict" in log_messages[0]

    # The invalid list item should be dropped, but the valid one should remain
    assert "light" in config
    assert isinstance(config["light"], list)
    assert config["light"] == [{"platform": "test-ok"}]
