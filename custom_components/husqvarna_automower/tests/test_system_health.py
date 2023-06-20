"""Test for system health."""

from unittest.mock import MagicMock, patch

import pytest
from aioautomower import TOKEN_URL
from homeassistant.core import HomeAssistant

from ..system_health import async_register, system_health_info


@pytest.mark.asyncio
async def test_system_health_info(hass: HomeAssistant):
    """test system_health_info."""
    with patch(
        "custom_components.husqvarna_automower.system_health.async_check_can_reach_url",
        MagicMock(),
    ) as can_reach_url:
        await system_health_info(hass)
        can_reach_url.assert_called_once_with(hass, TOKEN_URL)


@pytest.mark.asyncio
async def test_async_register(hass: HomeAssistant):
    """test async_register."""
    system_health = MagicMock(async_register_info=MagicMock())
    async_register(hass, system_health)
    system_health.async_register_info.assert_called_once()
