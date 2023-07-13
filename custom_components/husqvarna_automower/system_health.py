"""Provide info to system health."""
from aioautomower import TOKEN_URL
from homeassistant.components.system_health import (
    SystemHealthRegistration,
    async_check_can_reach_url,
)
from homeassistant.core import HomeAssistant, callback


# pylint: disable=unused-argument
@callback
def async_register(hass: HomeAssistant, register: SystemHealthRegistration) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info)


async def system_health_info(hass: HomeAssistant):
    """Get info for the info page."""
    return {"can_reach_server": async_check_can_reach_url(hass, TOKEN_URL)}
