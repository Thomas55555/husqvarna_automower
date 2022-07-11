"""Platform for Husqvarna Automower camera integration."""

import io
import logging
import math
from typing import Optional

from PIL import Image, ImageDraw
import numpy as np

from homeassistant.components.camera import SUPPORT_ON_OFF, Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    ENABLE_CAMERA,
    GPS_BOTTOM_RIGHT,
    GPS_TOP_LEFT,
    MAP_IMG_PATH,
    MOWER_IMG_PATH,
)
from .entity import AutomowerEntity
from .vacuum import HusqvarnaAutomowerStateMixin

GpsPoint = tuple[float, float]
ImgPoint = tuple[int, int]
ImgDimensions = tuple[int, int]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up select platform."""
    session = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AutomowerCamera(session, idx, entry)
        for idx, ent in enumerate(session.data["data"])
    )


class AutomowerCamera(HusqvarnaAutomowerStateMixin, Camera, AutomowerEntity):
    """Representation of the AutomowerCamera element."""

    _attr_entity_registry_enabled_default = False
    _attr_frame_interval: float = 300
    _attr_name = "Map"

    def __init__(self, session, idx, entry):
        """Initialize AutomowerCamera."""
        Camera.__init__(self)
        AutomowerEntity.__init__(self, session, idx)

        self.entry = entry
        self._position_history = []
        self._attr_unique_id = f"{self.mower_id}_camera"
        self._image = Image.new(mode="RGB", size=(200, 200))
        self._image_bytes = None
        self._image_to_bytes()

        self.session = session

        if self.entry.options.get(ENABLE_CAMERA, False):
            self.top_left_coord = self.entry.options.get(GPS_TOP_LEFT)
            self.bottom_right_coord = self.entry.options.get(GPS_BOTTOM_RIGHT)
            self.session.register_data_callback(
                lambda data: self._generate_image(data), schedule_immediately=True
            )
        else:
            self._attr_entity_registry_enabled_default = True
            r_earth = 6378000  # meters
            offset = 100  # meters
            pi = 3.14
            lat = AutomowerEntity.get_mower_attributes(self)["positions"][0]["latitude"]
            lon = AutomowerEntity.get_mower_attributes(self)["positions"][0][
                "longitude"
            ]
            top_left_lat = lat - (offset / r_earth) * (180 / pi)
            top_left_lon = lon - (offset / r_earth) * (180 / pi) / math.cos(
                lat * pi / 180
            )
            bottom_right_lat = lat + (offset / r_earth) * (180 / pi)
            bottom_right_lon = lon + (offset / r_earth) * (180 / pi) / math.cos(
                lat * pi / 180
            )
            self.top_left_coord = (top_left_lat, top_left_lon)
            self.bottom_right_coord = (bottom_right_lat, bottom_right_lon)

    def model(self) -> str:
        """Return the mower model."""
        return self.model

    async def async_camera_image(
        self, width: Optional[int] = None, height: Optional[int] = None
    ) -> Optional[bytes]:
        """Return the caerma image."""
        return self._image_bytes

    def _image_to_bytes(self):
        img_byte_arr = io.BytesIO()
        self._image.save(img_byte_arr, format="PNG")
        self._image_bytes = img_byte_arr.getvalue()

    def turn_on(self):
        """Turn the camera on."""
        self.session.register_data_callback(
            lambda data: self._generate_image(data), schedule_immediately=True
        )

    def turn_off(self):
        """Turn the camera off."""
        self.session.unregister_data_callback(lambda data: self._generate_image(data))

    @property
    def supported_features(self) -> int:
        """Show supported features."""
        return SUPPORT_ON_OFF

    def _generate_image(self, data: dict):
        position_history = AutomowerEntity.get_mower_attributes(self)["positions"]
        location = (position_history[0]["latitude"], position_history[0]["longitude"])
        if len(position_history) == 1:
            self._position_history += position_history
            position_history = self._position_history
        else:
            self._position_history = position_history

        map_image_path = self.entry.options.get(MAP_IMG_PATH)
        map_image = Image.open(map_image_path, "r")
        overlay_path = self.entry.options.get(MOWER_IMG_PATH)
        overlay_image = Image.open(overlay_path, "r")
        x1, y1 = self._scale_to_img(location, (map_image.size[0], map_image.size[1]))
        img_draw = ImageDraw.Draw(map_image)
        for i in range(len(position_history) - 1, 0, -1):
            point_1 = (
                position_history[i]["latitude"],
                position_history[i]["longitude"],
            )
            scaled_loc_1 = self._scale_to_img(
                point_1, (map_image.size[0], map_image.size[1])
            )
            point_2 = (
                position_history[i - 1]["latitude"],
                position_history[i - 1]["longitude"],
            )
            scaled_loc_2 = self._scale_to_img(
                point_2, (map_image.size[0], map_image.size[1])
            )
            plot_points = self._find_points_on_line(scaled_loc_1, scaled_loc_2)
            for p in range(0, len(plot_points) - 1, 2):
                img_draw.line((plot_points[p], plot_points[p + 1]), fill="red", width=2)
        overlay_image = overlay_image.resize((64, 64))
        img_w, img_h = overlay_image.size
        map_image.paste(
            overlay_image, (x1 - img_w // 2, y1 - img_h // 2), overlay_image
        )
        self._image = map_image
        self._image_to_bytes()

    def _find_points_on_line(
        self, point_1: ImgPoint, point_2: ImgPoint
    ) -> list[ImgPoint]:
        dash_length = 10
        line_length = math.sqrt(
            (point_2[0] - point_1[0]) ** 2 + (point_2[1] - point_1[1]) ** 2
        )
        dashes = int(line_length // dash_length)

        points = []
        points.append(point_1)
        for i in range(dashes):
            points.append(self._get_point_on_vector(points[-1], point_2, dash_length))

        points.append(point_2)

        return points

    def _get_point_on_vector(
        self, initial_pt: ImgPoint, terminal_pt: ImgPoint, distance: int
    ) -> ImgPoint:
        v = np.array(initial_pt, dtype=float)
        u = np.array(terminal_pt, dtype=float)
        n = v - u
        n /= np.linalg.norm(n, 2)
        point = v - distance * n

        return tuple(point)

    def _scale_to_img(self, lat_lon: GpsPoint, h_w: ImgDimensions) -> ImgPoint:
        """Convert from latitude and longitude to the image pixels."""
        old = (self.bottom_right_coord[0], self.top_left_coord[0])
        new = (0, h_w[1])
        y = ((lat_lon[0] - old[0]) * (new[1] - new[0]) / (old[1] - old[0])) + new[0]
        old = (self.top_left_coord[1], self.bottom_right_coord[1])
        new = (0, h_w[0])
        x = ((lat_lon[1] - old[0]) * (new[1] - new[0]) / (old[1] - old[0])) + new[0]
        return int(x), h_w[1] - int(y)
