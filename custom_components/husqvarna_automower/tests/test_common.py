"""Common test functions module."""
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioautomower import AutomowerSession, GetMowerData
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from ..const import DOMAIN
from .const import (
    AUTOMER_DM_CONFIG,
    AUTOMOWER_CONFIG_DATA,
    AUTOMOWER_SM_SESSION_DATA,
)


@pytest.mark.asyncio
async def setup_entity(hass: HomeAssistant):
    """Set up entity and config entry"""

    options = deepcopy(AUTOMER_DM_CONFIG)

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=AUTOMOWER_CONFIG_DATA,
        options=options,
        entry_id="automower_test",
        title="Automower Test",
    )

    config_entry.add_to_hass(hass)

    session = deepcopy(AUTOMOWER_SM_SESSION_DATA)

    with patch(
        "aioautomower.AutomowerSession",
        return_value=AsyncMock(
            name="AutomowerMockSession",
            model=AutomowerSession,
            data=session,
            register_data_callback=MagicMock(),
            unregister_data_callback=MagicMock(),
            register_token_callback=MagicMock(),
            connect=AsyncMock(),
            action=AsyncMock(),
        ),
    ) as automower_session_mock:
        with patch(
            "aioautomower.GetMowerData",
            return_value=AsyncMock(name="GetMowerMock", model=GetMowerData, data={}),
        ) as mower_data_mock:
            automower_coordinator_mock = MagicMock(
                name="MockCoordinator", session=automower_session_mock()
            )

            await hass.config_entries.async_setup(config_entry.entry_id)
            await hass.async_block_till_done()
            assert config_entry.state == ConfigEntryState.LOADED
            assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    return config_entry
