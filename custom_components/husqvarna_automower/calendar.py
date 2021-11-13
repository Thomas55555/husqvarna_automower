from .const import DOMAIN
from homeassistant.components.calendar import CalendarEventDevice, get_date
import homeassistant.util.dt as dt_util
import logging
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, entry, async_add_entities, discovery_info=None):
    """Set up the Demo Calendar platform."""
    # session = hass.data[DOMAIN][entry.entry_id]
    calendar_data_current = DemoGoogleCalendarData()
    async_add_entities(
        [
            DemoGoogleCalendar(hass, calendar_data_current, "Mower 1"),
        ]
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

    def __init__(self, hass, calendar_data, name):
        """Initialize demo calendar."""
        self.data = calendar_data
        self._name = name

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
