"""Platform for Husqvarna Automower device tracker integration."""
import json
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, UpdateFailed

from . import AutomowerCoordinator
from .const import DOMAIN, HEADLIGHTMODES
from .entity import AutomowerEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up select platform."""
    coordinator: AutomowerCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_config_entry_first_refresh()
    _LOGGER.debug("coordinator: %s", coordinator.data)
    async_add_entities(
        AutomowerSelect(hass, coordinator)
        for idx, ent in enumerate(coordinator.data["data"])
        if not coordinator.data["data"][idx]["attributes"]["system"]["model"]
        in ["550", "Ceora"]
    )


class AutomowerSelect(AutomowerCoordinator, SelectEntity):
    """Defining the Headlight Mode Select Entity."""

    _attr_options = HEADLIGHTMODES
    _attr_icon = "mdi:car-light-high"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_name = "Headlight mode"

    def __init__(self, coordinator) -> None:
        """Initialize AutomowerSelect."""
        super().__init__(coordinator)
        # self.idx = idx
        self._attr_unique_id = f"{self.mower_id}_headlight_mode"

    @property
    def available(self) -> bool:
        """Return True if the device is available."""
        available = self.get_mower_attributes()["metadata"]["connected"]
        return available

    @property
    def current_option(self) -> str:
        """Return a the current option for the entity."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        return mower_attributes["headlight"]["mode"]

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        command_type = "settings"
        string = {
            "data": {
                "type": "settings",
                "attributes": {"headlight": {"mode": option}},
            }
        }
        payload = json.dumps(string)
        try:
            await self.coordinator.api.action(self.mower_id, payload, command_type)
        except Exception as exception:
            raise UpdateFailed(exception) from exception
