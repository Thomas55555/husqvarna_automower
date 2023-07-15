"""Test for diagnostics module."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from ..const import DOMAIN
from ..diagnostics import TO_REDACT, async_get_config_entry_diagnostics
from .const import AUTOMER_SM_CONFIG, AUTOMOWER_CONFIG_DATA

from .test_common import setup_entity


@pytest.mark.asyncio
async def test_redact(hass: HomeAssistant):
    """test automower initialization"""

    config_entry = await setup_entity(hass)

    diag_data = await async_get_config_entry_diagnostics(hass, config_entry)

    redacted = []
    for k, v in diag_data.get("config_entry").get("data").items():
        if k in TO_REDACT:
            assert v.get(k) == "**REDACTED**"
            redacted.append(k)

    for k, v in diag_data.get("config_entry").get("options").items():
        if k in TO_REDACT:
            assert v == "**REDACTED**"
            redacted.append(k)
        if isinstance(v, dict):
            for k2, v2 in v.items():
                if k2 in TO_REDACT:
                    assert v2 == "**REDACTED**"
                    redacted.append(k2)

    assert (
        set(TO_REDACT)
        .difference(redacted)
        .issubset(
            set(
                [
                    "positions",
                    "refresh_token",
                    "access_token",
                ]
            )
        )
    )
