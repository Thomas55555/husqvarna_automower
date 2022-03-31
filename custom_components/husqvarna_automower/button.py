"""Platform for Husqvarna Automower button integration."""
import json
import logging

from homeassistant.components.button import ButtonEntity
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
    """Setup select platform."""
    session = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        MowForOneHour(session, idx) for idx, ent in enumerate(session.data["data"])
    )


class MowForOneHour(ButtonEntity, AutomowerEntity):
    """Defining the MowForOneHour Button Entity."""

    _attr_icon = "mdi:clock-time-one"
    _attr_entity_registry_enabled_default = False

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return f"{self.mower_name} Mow for 1h"

    @property
    def unique_id(self) -> str:
        """Return a unique identifier for this entity."""
        return f"{self.mower_id}_mowforonehour"

    async def async_press(self) -> None:
        """Handle the button press."""
        command_type = "actions"
        string = {
            "data": {
                "type": "Start",
                "attributes": {"duration": 60},
            }
        }
        payload = json.dumps(string)
        try:
            await self.session.action(self.mower_id, payload, command_type)
        except Exception as exception:
            raise UpdateFailed(exception) from exception
