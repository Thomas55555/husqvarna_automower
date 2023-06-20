"""Platform for Husqvarna Automower device tracker integration."""
import json
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import DOMAIN, HEADLIGHTMODES
from .entity import AutomowerEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up select platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AutomowerSelect(coordinator, idx)
        for idx, ent in enumerate(coordinator.session.data["data"])
        if not coordinator.session.data["data"][idx]["attributes"]["system"]["model"]
        in ["550", "Ceora"]
        and coordinator.session.data["data"][idx]["attributes"]["headlight"]["mode"]
        is not None
    )


class AutomowerSelect(SelectEntity, AutomowerEntity):
    """Defining the Headlight Mode Select Entity."""

    _attr_options = HEADLIGHTMODES
    _attr_icon = "mdi:car-light-high"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "headlight_mode"

    def __init__(self, session, idx):
        """Initialize AutomowerSelect."""
        super().__init__(session, idx)
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
        return mower_attributes["headlight"]["mode"].lower()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        command_type = "settings"
        string = {
            "data": {
                "type": "settings",
                "attributes": {"headlight": {"mode": option.upper()}},
            }
        }
        payload = json.dumps(string)
        try:
            await self.coordinator.session.action(self.mower_id, payload, command_type)
        except Exception as exception:
            raise UpdateFailed(exception) from exception
