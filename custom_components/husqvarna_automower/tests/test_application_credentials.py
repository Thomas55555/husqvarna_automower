"""Tests for application credentials module."""
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioautomower import AutomowerSession
from homeassistant.components.application_credentials import AuthorizationServer
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from ..application_credentials import (
    async_get_authorization_server,
    async_get_description_placeholders,
)
from ..const import DOMAIN, HUSQVARNA_URL
from .const import AUTOMER_DM_CONFIG, AUTOMOWER_CONFIG_DATA, AUTOMOWER_SM_SESSION_DATA


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
        automower_coordinator_mock = MagicMock(
            name="MockCoordinator", session=automower_session_mock()
        )

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        assert config_entry.state == ConfigEntryState.LOADED
        assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    return config_entry


@pytest.mark.asyncio
async def test_application_credentials(hass: HomeAssistant):
    """test application credentials."""
    await setup_entity(hass)

    with patch(
        "custom_components.husqvarna_automower.application_credentials.AuthorizationServer",
        MagicMock(spec=AuthorizationServer),
    ) as mock_auth_server:
        await async_get_authorization_server(hass)
        mock_auth_server.assert_called_once()

    result = await async_get_description_placeholders(hass)
    assert result["oauth_creds_url"] == HUSQVARNA_URL
    assert "redirect_uri" in result
