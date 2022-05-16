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

        self._available = self.get_mower_attributes()["metadata"]["connected"]

        self._event = None
        self._next_event = None
        self.loc = None

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
    def should_poll(self) -> bool:
        """Return True if the device is available."""
        return False
