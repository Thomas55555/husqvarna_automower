"""Diagnostics support for Husqvarna Automower."""
from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant

from .const import (
    CONF_REFRESH_TOKEN,
    CONF_ZONES,
    DOMAIN,
    GPS_BOTTOM_RIGHT,
    GPS_TOP_LEFT,
    HOME_LOCATION,
    POSITIONS,
)

TO_REDACT = {
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    POSITIONS,
    GPS_TOP_LEFT,
    GPS_BOTTOM_RIGHT,
    CONF_ZONES,
    HOME_LOCATION,
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Return diagnostics of the config entry and mower data."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    diag_data = {
        "config_entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "data_of_all_mowers": async_redact_data(
            coordinator.session.data["data"], TO_REDACT
        ),
    }

    return diag_data
