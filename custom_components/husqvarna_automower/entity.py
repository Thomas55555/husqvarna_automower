"""Platform for Husqvarna Automower basic entity."""

import logging

from homeassistant.helpers.entity import DeviceInfo, Entity

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

        self.session.register_cb(
            lambda _: self.async_write_ha_state(), schedule_immediately=True
        )

        self._available = None

        self._event = None
        self._next_event = None

    def get_mower_attributes(self) -> dict:
        return self.session.data["data"][self.idx]["attributes"]

    @property
    def device_info(self) -> DeviceInfo:
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
        available = False
        try:
            available = (
                self.get_mower_attributes()["metadata"]["connected"]
                and self.session.data["data"][self.idx]["id"] == self.mower_id
            )
        except (IndexError, KeyError):
            pass

        if self._available != available:
            if self._available is not None:
                if available:
                    _LOGGER.info("Connected to %s again", self.mower_name)
                else:
                    _LOGGER.warning("Connection to %s lost", self.mower_name)
            self._available = available

        return available
