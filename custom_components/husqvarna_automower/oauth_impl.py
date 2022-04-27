"""Local implementation of OAuth2 specific to Husqvarna to hard code client id and secret and return a proper name."""

import logging

from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import Config, HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import LocalOAuth2Implementation
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

OAUTH2_AUTHORIZE = "https://api.authentication.husqvarnagroup.dev/v1/oauth2/authorize"
OAUTH2_TOKEN = "https://api.authentication.husqvarnagroup.dev/v1/oauth2/token"

_LOGGER = logging.getLogger(__name__)


class HusqvarnaOauth2Implementation(LocalOAuth2Implementation):
    """Local implementation of OAuth2 specific to Husqvarna to hard code client id and secret and return a proper name."""

    def __init__(self, hass: HomeAssistant):
        """Just init default class with default values."""
        super().__init__(
            hass,
            DOMAIN,
            hass.data[DOMAIN][CONF_CLIENT_ID],
            hass.data[DOMAIN][CONF_CLIENT_SECRET],
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
        )

    @property
    def name(self) -> str:
        """Name of the implementation."""
        return DOMAIN
