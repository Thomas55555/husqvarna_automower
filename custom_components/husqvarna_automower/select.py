"""Platform for Husqvarna Automower device tracker integration."""
import json

from homeassistant.components.select import SelectEntity
from homeassistant.const import ENTITY_CATEGORY_CONFIG
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import DOMAIN, HEADLIGHTMODES
from .entity import AutomowerEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Setup sensor platform."""
    session = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AutomowerSelect(session, idx) for idx, ent in enumerate(session.data["data"])
    )


class AutomowerSelect(SelectEntity, AutomowerEntity):
    """Defining the Headlight Mode Select Entity."""

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return f"{self.mower_name} Headlight mode"

    @property
    def unique_id(self) -> str:
        """Return a unique identifier for this entity."""
        return f"{self.mower_id}_headlight_mode"

    @property
    def options(self) -> list[str]:
        """Return a set of selectable options."""
        return HEADLIGHTMODES

    @property
    def icon(self) -> str:
        """Return a the icon for the entity."""
        return "mdi:car-light-high"

    @property
    def current_option(self) -> str:
        """Return a the current option for the entity."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        try:
            test = mower_attributes["headlight"]["mode"]  ## return of the websocket
        except KeyError:
            test = mower_attributes["settings"]["headlight"][
                "mode"
            ]  ## return from REST, just for start-up
        return test

    @property
    def entity_category(self) -> str:
        """Return a unique identifier for this entity."""
        return ENTITY_CATEGORY_CONFIG

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
            await self.session.action(self.mower_id, payload, command_type)
        except Exception as exception:
            raise UpdateFailed(exception) from exception
