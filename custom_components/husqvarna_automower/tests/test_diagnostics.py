"""Test for diagnostics module."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from ..const import DOMAIN
from ..diagnostics import TO_REDACT, async_get_config_entry_diagnostics
from .const import AUTOMER_SM_CONFIG, AUTOMOWER_CONFIG_DATA


@pytest.mark.asyncio
async def test_redact(hass: HomeAssistant):
    """test automower initialization"""

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=AUTOMOWER_CONFIG_DATA,
        options=AUTOMER_SM_CONFIG,
        entry_id="automower_test",
        title="Automower Test",
    )
    config_entry.add_to_hass(hass)

    with patch(
        "aioautomower.AutomowerSession",
        return_value=AsyncMock(register_token_callback=MagicMock()),
    ) as mock_aioautomower_session:
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

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
