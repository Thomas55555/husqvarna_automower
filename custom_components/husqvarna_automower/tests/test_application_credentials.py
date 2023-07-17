"""Tests for application credentials module."""
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.application_credentials import AuthorizationServer
from homeassistant.core import HomeAssistant

from ..application_credentials import (
    async_get_authorization_server,
    async_get_description_placeholders,
)
from ..const import HUSQVARNA_URL

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
