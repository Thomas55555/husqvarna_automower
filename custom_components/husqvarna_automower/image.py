"""Platform for Husqvarna Automower map image integration."""

import io
import json
import logging
import math
from datetime import datetime
from typing import Optional

import numpy as np
from geopy.distance import distance, geodesic
from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from PIL import Image, ImageDraw

from .const import (
    ADD_IMAGES,
    CONF_ZONES,
    DOMAIN,
    ENABLE_IMAGE,
    GPS_BOTTOM_RIGHT,
    GPS_TOP_LEFT,
    HOME_LOCATION,
    MAP_IMG_PATH,
    MAP_IMG_ROTATION,
    MAP_PATH_COLOR,
    MOWER_IMG_PATH,
    ZONE_COLOR,
    ZONE_COORD,
    ZONE_DISPLAY,
    ZONE_MOWERS,
)
from .entity import AutomowerEntity

GpsPoint = tuple[float, float]
ImgPoint = tuple[int, int]
ImgDimensions = tuple[int, int]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up select platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entity_list = []
    for idx, ent in enumerate(coordinator.session.data["data"]):
        if entry.options.get(ent["id"], {}).get(ENABLE_IMAGE):
            entity_list.append(AutomowerImage(coordinator, idx, entry, hass))

    async_add_entities(entity_list)


class AutomowerImage(ImageEntity, AutomowerEntity):
    """Representation of the AutomowerImage element."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "mower_img"

    def __init__(self, coordinator, idx, entry, hass: HomeAssistant) -> None:
        """Initialize AutomowerImage."""
        ImageEntity.__init__(self, hass)
        AutomowerEntity.__init__(self, coordinator, idx)

        self.entry = entry
        self._position_history = {}
        self.previous_position_history = {}
        self._attr_unique_id = f"{self.mower_id}_image"
        self.options = self.entry.options.get(self.mower_id, {})
        self.home_location = self.options.get(HOME_LOCATION, None)
        self._image = Image.new(mode="RGB", size=(200, 200))
        self._map_image = None
        self._overlay_image = None
        self._path_color = self.options.get(MAP_PATH_COLOR, [255, 0, 0])
        self._px_meter = 1
        self._c_img_wgs84 = (0, 0)
        self._c_img_px = (0, 0)
        self._mwr_id_to_idx = {}

        # pylint: disable=unused-variable
        for idx, ent in enumerate(coordinator.session.data["data"]):
            self._mwr_id_to_idx[coordinator.session.data["data"][idx]["id"]] = idx

        self._additional_images = self.options.get(ADD_IMAGES, [])

        if self.options.get(ENABLE_IMAGE, False):
            self._top_left_coord = self.options.get(GPS_TOP_LEFT)
            self._bottom_right_coord = self.options.get(GPS_BOTTOM_RIGHT)
            self._map_rotation = self.options.get(MAP_IMG_ROTATION, 0)
            self._load_map_image()
            self._find_image_scale()
            self._load_mower_image()
            self._overlay_zones()

            # pylint: disable=unnecessary-lambda
            self.coordinator.session.register_data_callback(
                lambda data: self._generate_image(data),
                schedule_immediately=True,
            )
        else:
            self._attr_entity_registry_enabled_default = True
            r_earth = 6378000  # meters
            offset = 100  # meters
            lat = AutomowerEntity.get_mower_attributes(self)["positions"][0]["latitude"]
            lon = AutomowerEntity.get_mower_attributes(self)["positions"][0][
                "longitude"
            ]
            top_left_lat = lat - (offset / r_earth) * (180 / math.pi)
            top_left_lon = lon - (offset / r_earth) * (180 / math.pi) / math.cos(
                lat * math.pi / 180
            )
            bottom_right_lat = lat + (offset / r_earth) * (180 / math.pi)
            bottom_right_lon = lon + (offset / r_earth) * (180 / math.pi) / math.cos(
                lat * math.pi / 180
            )
            self._top_left_coord = (top_left_lat, top_left_lon)
            self._bottom_right_coord = (bottom_right_lat, bottom_right_lon)
            self._map_rotation = 0

    async def async_image(self) -> bytes | None:
        """Return bytes of image."""
        return await self._image_to_bytes()

    def _load_map_image(self):
        """Load the map image."""
        map_image_path = self.options.get(MAP_IMG_PATH)
        self._map_image = Image.open(map_image_path, "r").convert("RGBA")

    def _load_mower_image(self):
        """Load the mower overlay image."""
        overlay_path = self.options.get(MOWER_IMG_PATH)
        self._overlay_image = Image.open(overlay_path, "r")
        mower_img_w = 64
        mower_wpercent = mower_img_w / float(self._overlay_image.size[0])
        hsize = int((float(self._overlay_image.size[1]) * float(mower_wpercent)))
        self._overlay_image = self._overlay_image.resize(
            (mower_img_w, hsize), Image.Resampling.LANCZOS
        )

    def _overlay_zones(self) -> None:
        """Draw zone overlays."""
        zones = json.loads(self.entry.options.get(CONF_ZONES, "{}"))

        if not isinstance(zones, dict):
            return

        # pylint: disable=unused-variable
        for zone_id, zone in zones.items():
            if self.mower_id in zone.get(ZONE_MOWERS, []) and zone.get(
                ZONE_DISPLAY, False
            ):
                zone_poly = [
                    self._scale_to_img(
                        point, (self._map_image.size[0], self._map_image.size[1])
                    )
                    for point in zone.get(ZONE_COORD)
                ]

                if len(zone_poly) < 3:
                    return

                poly_img = Image.new(
                    "RGBA", (self._map_image.size[0], self._map_image.size[1])
                )
                pdraw = ImageDraw.Draw(poly_img)

                zone_color = zone.get(ZONE_COLOR, [255, 255, 255])

                pdraw.polygon(
                    zone_poly,
                    fill=tuple(zone_color + [25]),
                    outline=tuple(zone_color + [255]),
                )
                self._map_image.paste(poly_img, mask=poly_img)

    async def _image_to_bytes(
        self, width: Optional[int] = None, height: Optional[int] = None
    ) -> Optional[bytes]:
        img_byte_arr = io.BytesIO()
        map_image = self._image.copy()
        if width and height:
            map_image.thumbnail((width, height), Image.Resampling.LANCZOS)
        map_image.save(img_byte_arr, format="PNG")
        return img_byte_arr.getvalue()

    def _find_image_scale(self):
        """Find the scale ration in m/px and center of image."""
        h_w = (
            self._map_image.size[0],
            self._map_image.size[1],
        )  # Height/Width of image
        self._c_img_px = int((0 + h_w[0]) / 2), int(
            (0 + h_w[1]) / 2
        )  # Center of image in pixels

        # Center of image in lat/long
        self._c_img_wgs84 = (
            (self._top_left_coord[0] + self._bottom_right_coord[0]) / 2,
            (self._top_left_coord[1] + self._bottom_right_coord[1]) / 2,
        )

        # Length of hypotenuse in meters
        len_wgs84_m = geodesic(self._top_left_coord, self._bottom_right_coord).meters

        # Length of hypotenuse in pixels
        len_px = int(math.dist((0, 0), h_w))

        self._px_meter = len_px / len_wgs84_m  # Scale in pixels/meter

        _LOGGER.debug(
            "Center px: %s, Center WGS84: %s, Len (m): %s, Len (px): %s, px/m: %s, Img HW (px): %s",
            self._c_img_px,
            self._c_img_wgs84,
            len_wgs84_m,
            len_px,
            self._px_meter,
            h_w,
        )

    def _generate_image_img(
        self,
        is_home: bool,
        home_location: GpsPoint,
        position_history: list,
        mower_id: str,
        path_color: list,
        map_image: Image.Image,
    ) -> None:
        """Create image and mower overlay."""
        if is_home and home_location:
            location = home_location
        else:
            location = (
                position_history[0]["latitude"],
                position_history[0]["longitude"],
            )

        self._position_history[mower_id] = position_history

        # pylint: disable=invalid-name
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
            for point in range(0, len(plot_points) - 1, 2):
                img_draw.line(
                    (plot_points[point], plot_points[point + 1]),
                    fill=tuple(path_color + [255]),
                    width=2,
                )

        img_w, img_h = self._overlay_image.size

        map_image.paste(
            self._overlay_image, (x1 - img_w // 2, y1 - img_h), self._overlay_image
        )
        return map_image

    def _generate_image(self, data: dict) -> None:  # pylint: disable=unused-argument
        """Generate the image."""
        # self._calculate_update_frequency()

        map_image = self._map_image.copy()

        if self._additional_images:
            for add_img in self._additional_images:
                extra_img = AutomowerEntity(
                    self.coordinator, self._mwr_id_to_idx[add_img]
                )
                options = self.entry.options.get(add_img, {})
                home_location = options.get(HOME_LOCATION, None)
                path_color = options.get(MAP_PATH_COLOR, [255, 0, 0])
                img_position_history = extra_img.get_mower_attributes()["positions"]
                map_image = self._generate_image_img(
                    extra_img.is_home,
                    home_location,
                    img_position_history,
                    extra_img.mower_id,
                    path_color,
                    map_image,
                )

        position_history = AutomowerEntity.get_mower_attributes(self)["positions"]
        if self.previous_position_history != position_history:
            self.previous_position_history = position_history
            map_image = self._generate_image_img(
                self.is_home,
                self.home_location,
                position_history,
                self.mower_id,
                self._path_color,
                map_image,
            )
            self._image = map_image
            self._attr_image_last_updated = datetime.now()

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
        # pylint: disable=unused-variable
        for i in range(dashes):
            points.append(self._get_point_on_vector(points[-1], point_2, dash_length))

        points.append(point_2)

        return points

    def _get_point_on_vector(
        self, initial_pt: ImgPoint, terminal_pt: ImgPoint, dist: int
    ) -> ImgPoint:
        """Find a point on a vector."""
        v = np.array(initial_pt, dtype=float)  # pylint: disable=invalid-name
        u = np.array(terminal_pt, dtype=float)  # pylint: disable=invalid-name
        n = v - u  # pylint: disable=invalid-name
        n /= np.linalg.norm(n, 2)  # pylint: disable=invalid-name
        point = v - dist * n

        return tuple(point)

    def _scale_to_img(
        self, lat_lon: GpsPoint, h_w: ImgDimensions  # pylint: disable=unused-argument
    ) -> ImgPoint:
        """Convert from latitude and longitude to the image pixels."""
        bearing_res = distance(self._c_img_wgs84, lat_lon).geod.Inverse(
            self._c_img_wgs84[0], self._c_img_wgs84[1], lat_lon[0], lat_lon[1]
        )
        c_bearing_deg = bearing_res.get("azi1")
        c_plt_pnt_m = bearing_res.get("s12") * 1000
        c_bearing = math.radians(c_bearing_deg - 90 + self._map_rotation)

        new_pnt_px = (
            self._c_img_px[0] + (c_plt_pnt_m * self._px_meter * math.cos(c_bearing)),
            self._c_img_px[1] + (c_plt_pnt_m * self._px_meter * math.sin(c_bearing)),
        )

        return int(new_pnt_px[0]), int(new_pnt_px[1])
