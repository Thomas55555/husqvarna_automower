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

from .test_common import setup_entity


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
