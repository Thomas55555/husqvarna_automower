"""Platform for Husqvarna Automower number integration."""
import json
import logging

from aiohttp import ClientResponseError

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import TIME_MINUTES
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import CHANGING_CUTTING_HEIGHT_SUPPORT, DOMAIN
from .entity import AutomowerEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up number platform."""
    session = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        AutomowerNumber(session, idx)
        for idx, ent in enumerate(session.data["data"])
        if any(
            ele in session.data["data"][idx]["attributes"]["system"]["model"]
            for ele in CHANGING_CUTTING_HEIGHT_SUPPORT
        )
    )
    async_add_entities(
        AutomowerParkStartNumberEntity(session, idx, description)
        for idx, ent in enumerate(session.data["data"])
        for description in NUMBER_SENSOR_TYPES
    )


NUMBER_SENSOR_TYPES: tuple[NumberEntityDescription, ...] = (
    NumberEntityDescription(
        key="Park",
        name="Park for",
        icon="mdi:clock-outline",
        entity_registry_enabled_default=True,
        native_unit_of_measurement=TIME_MINUTES,
    ),
    NumberEntityDescription(
        key="Start",
        name="Mow for",
        icon="mdi:clock-outline",
        entity_registry_enabled_default=True,
        native_unit_of_measurement=TIME_MINUTES,
    ),
)


class AutomowerNumber(NumberEntity, AutomowerEntity):
    """Defining the CuttingHeight Entity."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:grass"
    _attr_native_min_value = 1
    _attr_native_max_value = 9
    _attr_name = "Cutting height"

    def __init__(self, session, idx):
        """Initialize AutomowerNumber."""
        super().__init__(session, idx)
        self._attr_unique_id = f"{self.mower_id}_cuttingheight"

    @property
    def available(self) -> bool:
        """Return True if the device is available."""
        available = self.get_mower_attributes()["metadata"]["connected"]
        return available

    @property
    def native_value(self) -> int:
        """Return the entity value."""
        mower_attributes = AutomowerEntity.get_mower_attributes(self)
        return mower_attributes["cuttingHeight"]

    async def async_set_native_value(self, value: float) -> None:
        """Change the value."""
        command_type = "settings"
        string = {
            "data": {
                "type": "settings",
                "attributes": {"cuttingHeight": int(value)},
            }
        }
        payload = json.dumps(string)
        try:
            await self.session.action(self.mower_id, payload, command_type)
        except Exception as exception:
            raise UpdateFailed(exception) from exception


class AutomowerParkStartNumberEntity(NumberEntity, AutomowerEntity):
    """Defining the AutomowerParkStartNumberEntity."""

    _attr_native_value: float = 1
    _attr_native_min_value: float = 1
    _attr_native_max_value: float = 60480
    _attr_native_step: float = 1

    def __init__(self, session, idx, description: NumberEntityDescription):
        """Initialize AutomowerParkStartNumberEntity."""
        super().__init__(session, idx)
        self.description = description
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{self.mower_id}_{description.key}"

    @property
    def available(self) -> bool:
        """Return True if the device is available."""
        available = self.get_mower_attributes()["metadata"]["connected"]
        return available

    async def async_set_native_value(self, value: float) -> None:
        """Change the value."""
        command_type = "actions"
        duration = int(value)
        string = {
            "data": {
                "type": self.entity_description.key,
                "attributes": {"duration": duration},
            }
        }
        payload = json.dumps(string)
        try:
            await self.session.action(self.mower_id, payload, command_type)
        except ClientResponseError as exception:
            _LOGGER.error("Command couldn't be sent to the command que: %s", exception)
