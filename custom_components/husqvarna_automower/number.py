"""Platform for Husqvarna Automower number integration."""
import json
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import DOMAIN
from .entity import AutomowerEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setup number platform."""

    session = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        AutomowerNumber(session, idx)
        for idx, ent in enumerate(session.data["data"])
        if "4" in session.data["data"][idx]["attributes"]["system"]["model"]
    )


class AutomowerNumber(NumberEntity, AutomowerEntity):
    """Defining the CuttingHeight Entity."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:grass"
    _attr_min_value = 1
    _attr_max_value = 9

    def __init__(self, session, idx):
        super().__init__(session, idx)
        self._attr_name = f"{self.mower_name} Cutting Height"
        self._attr_unique_id = f"{self.mower_id}_cuttingheight"

    @property
    def available(self) -> bool:
        """Return True if the device is available."""
        available = self.get_mower_attributes()["metadata"]["connected"]
        return available

    @property
    def value(self) -> int:
        """Return the entity value."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        return mower_attributes["cuttingHeight"]

    async def async_set_value(self, value: float) -> None:
        """Change the value."""
        command_type = "settings"
        string = {
            "data": {
                "type": "settings",
                "attributes": {"cuttingHeight": value},
            }
        }
        payload = json.dumps(string)
        try:
            await self.session.action(self.mower_id, payload, command_type)
        except Exception as exception:
            raise UpdateFailed(exception) from exception
