"""Platform for Husqvarna Automower basic entity."""

import logging

from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, HUSQVARNA_URL

_LOGGER = logging.getLogger(__name__)


class AutomowerEntity(Entity):
    """Defining the Automower Basic Entity."""

    def __init__(self, session, idx) -> None:
        self.session = session
        self.idx = idx
        self.mower = self.session.data["data"][self.idx]

        mower_attributes = self.get_mower_attributes()
        self.mower_id = self.mower["id"]
        self.mower_name = mower_attributes["system"]["name"]
        self.model = mower_attributes["system"]["model"]

        self._available = self.get_mower_attributes()["metadata"]["connected"]

        self._event = None
        self._next_event = None

    def get_mower_attributes(self) -> dict:
        """Get the mower attributes of the current mower."""
        return self.session.data["data"][self.idx]["attributes"]

    async def async_added_to_hass(self) -> None:
        """Call when entity about to be added to Home Assistant."""
        await super().async_added_to_hass()
        self.session.register_data_callback(
            lambda _: self.async_write_ha_state(), schedule_immediately=True
        )

    async def async_will_remove_from_hass(self) -> None:
        """Call when entity is being removed from Home Assistant."""
        await super().async_will_remove_from_hass()
        self.session.unregister_data_callback(lambda _: self.async_write_ha_state())

    @property
    def device_info(self) -> DeviceInfo:
        """Defines the DeviceInfo for the mower."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.mower_id)},
            name=self.mower_name,
            manufacturer="Husqvarna",
            model=self.model,
            configuration_url=HUSQVARNA_URL,
            suggested_area="Garden",
        )

    @property
    def available(self) -> bool:
        """Return True if the device is available."""
        timestamp = self.get_mower_attributes()["metadata"]["statusTimestamp"]
        age = dt_util.utcnow() - dt_util.utc_from_timestamp(timestamp / 1000)
        if age > dt_util.dt.timedelta(minutes=30):
            available = False
        if age < dt_util.dt.timedelta(minutes=30):
            available = True
        warning_sent = False
        if self._available != available:
            if self._available is not None:
                if available and not warning_sent:
                    _LOGGER.info("Connected to %s again", self.mower_name)
                if not available:
                    _LOGGER.warning("Connection to %s lost", self.mower_name)
                    warning_sent = True
            self._available = available

        return available
