"""Platform for Husqvarna Automower number integration."""
import json
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.const import ENTITY_CATEGORY_CONFIG
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import DOMAIN
from .entity import AutomowerEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Setup number platform."""

    session = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        AutomowerNumber(session, idx)
        for idx, ent in enumerate(session.data["data"])
        if "4" in session.data["data"][idx]["attributes"]["system"]["model"]
    )


class AutomowerNumber(NumberEntity, AutomowerEntity):
    """Defining the CuttingHeight Entity."""

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return f"{self.mower_name} Cutting height"

    @property
    def unique_id(self) -> str:
        """Return a unique identifier for this entity."""
        return f"{self.mower_id}_cuttingheight"

    @property
    def min_value(self) -> float:
        """Return the minimum value."""
        return 1

    @property
    def max_value(self) -> float:
        """Return the maximum value."""
        return 9

    @property
    def value(self) -> int:
        """Return the entity value."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        try:
            test = mower_attributes["cuttingHeight"]  ## return of the websocket
        except KeyError:
            test = mower_attributes["settings"][
                "cuttingHeight"
            ]  ## return from REST, just for start-up
        return test

    @property
    def entity_category(self) -> str:
        """Return a unique identifier for this entity."""
        return ENTITY_CATEGORY_CONFIG

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
