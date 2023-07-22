"""Common test functions module."""
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioautomower import AutomowerSession, GetMowerData
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.components.application_credentials import (
    ClientCredential,
    async_import_client_credential,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from ..const import DOMAIN
from .const import (
    AUTOMER_SM_CONFIG,
    AUTOMER_DM_CONFIG,
    AUTOMOWER_CONFIG_DATA,
    AUTOMOWER_SM_SESSION_DATA,
    AUTOMOWER_DM_SESSION_DATA,
)


@pytest.mark.asyncio
async def setup_entity(hass: HomeAssistant, dual_mower: bool = False, conf_version=1):
    """Set up entity and config entry"""

    if dual_mower:
        options = deepcopy(AUTOMER_DM_CONFIG)
    else:
        options = deepcopy(AUTOMER_SM_CONFIG)

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=AUTOMOWER_CONFIG_DATA,
        options=options,
        entry_id="automower_test",
        title="Automower Test",
        version=conf_version,
    )

    config_entry.add_to_hass(hass)

    if dual_mower:
        session = deepcopy(AUTOMOWER_DM_SESSION_DATA)
    else:
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
    ):
        with patch(
            "aioautomower.GetMowerData",
            return_value=AsyncMock(
                name="GetMowerDataMock",
                model=GetMowerData,
                async_mower_state=AsyncMock(
                    name="mower_state_mock", return_value=session
                ),
            ),
        ):
            await hass.config_entries.async_setup(config_entry.entry_id)
            await hass.async_block_till_done()
            assert config_entry.state == ConfigEntryState.LOADED
            assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    return config_entry


async def configure_application_credentials(hass: HomeAssistant):
    """Configure application credentials"""
    app_cred_config_entry = MockConfigEntry(
        domain="application_credentials",
        data={},
        entry_id="application_credentials",
        title="Application Credentials",
    )
    app_cred_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(app_cred_config_entry.entry_id)

    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(
            "test_client_id",
            "test_config_secret",
        ),
    )
