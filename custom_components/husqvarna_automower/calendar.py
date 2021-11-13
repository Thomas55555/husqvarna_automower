from .const import DOMAIN
from homeassistant.components.calendar import CalendarEventDevice, get_date
from homeassistant.config_entries import ConfigEntry
import homeassistant.util.dt as dt_util
import logging

from homeassistant.const import CONF_TOKEN

_LOGGER = logging.getLogger(__name__)


# def setup_platform(
#     hass, config, entry: ConfigEntry, async_add_entities, discovery_info=None
# ):
#     """Set up the Demo Calendar platform."""
#     _LOGGER.debug("entry: %s", entry)
#     api_key = entry.unique_id
#     access_token = entry.data.get(CONF_TOKEN)

#     session = aioautomower.AutomowerSession(api_key, access_token)
#     session.register_token_callback(
#         lambda token: hass.config_entries.async_update_entry(
#             entry,
#             data={
#                 CONF_TOKEN: token,
#             },
#         )
#     )
#     session = hass.data[DOMAIN][entry.entry_id]
#     calendar_data_current = DemoGoogleCalendarData()
#     async_add_entities(
#         [
#             DemoGoogleCalendar(hass, calendar_data_current, "Mower 1"),
#         ]
#     )


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Setup sensor platform."""
    _LOGGER.debug("entry: %s", entry)
    session = hass.data[DOMAIN][entry.entry_id]
    calendar_data_current = DemoGoogleCalendarData()
    # async_add_entities(
    #     [
    #         DemoGoogleCalendar(hass, calendar_data_current, session),
    #     ]
    # )
    async_add_entities(
        DemoGoogleCalendar(hass, calendar_data_current, session, idx)
        for idx, ent in enumerate(session.data["data"])
    )


class DemoGoogleCalendarData:
    """Representation of a Demo Calendar element."""

    event = None

    async def async_get_events(self, hass, start_date, end_date):
        """Get all events in a specific time frame."""
        event = None
        # event = copy.copy(self.event)
        # start = get_date(event["start"])
        # _LOGGER.debug("start %s", start)
        start_of_day = dt_util.start_of_local_day()
        _LOGGER.debug("dt url now %s", start_of_day)
        start_mowing = start_of_day + dt_util.dt.timedelta(minutes=30)
        end_mowing = start_of_day + dt_util.dt.timedelta(minutes=300)
        self.event = {
            "start": {"dateTime": start_mowing},
            "end": {"dateTime": end_mowing},
            "summary": "Mowing",
        }

        return [self.event]


class DemoGoogleCalendar(CalendarEventDevice):
    """Representation of a Demo Calendar element."""

    def __init__(self, hass, calendar_data, session, idx):
        """Initialize demo calendar."""
        self.data = calendar_data
        self.session = session
        self.idx = idx
        self.mower = self.session.data["data"][self.idx]
        mower_attributes = self.__get_mower_attributes()
        self.mower_id = self.mower["id"]
        self._name = mower_attributes["system"]["name"]

    def __get_mower_attributes(self) -> dict:
        return self.session.data["data"][self.idx]["attributes"]

    @property
    def event(self):
        """Return the next upcoming event."""
        return self.data.event

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    async def async_get_events(self, hass, start_date, end_date):
        """Return calendar events within a datetime range."""
        return await self.data.async_get_events(hass, start_date, end_date)
