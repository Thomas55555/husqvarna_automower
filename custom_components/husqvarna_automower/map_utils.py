"""Utilities for parsing and validating coordinates."""
from shapely.geometry import Point
from .const import LAT_LON_BOUNDS
from PIL import Image, UnidentifiedImageError


def validate_image(img_path: str) -> bool:
    """Ensure image is valid."""
    try:
        im = Image.open(img_path)
        im.verify()
        im.close()
    except (FileNotFoundError, UnidentifiedImageError):
        return False
    return True


class LatLon:
    """Define a Latitude and Longitude object."""

    def __init__(self, lat: float, lon: float) -> None:
        """Initialize the LatLon Object."""
        self.lat = lat
        self.lon = lon

    @property
    def point(self) -> Point:
        """Return a Point."""
        return Point(self.lat, self.lon)

    def is_valid(self) -> bool:
        """Return True if point is a valid WGS84 Coordinate."""
        return LAT_LON_BOUNDS.intersects(self.point)


class ValidatePointString:
    """Define a Point String Validation Object."""

    def __init__(self, point_string: str) -> None:
        """Initialize the ValidatePointString Object."""
        self.point_str = point_string
        self.point_list = self.point_str.split(",")
        self.error = ""
        self.valid = False
        self.coord = None

        if len(self.point_list) != 2:
            self.error = "invalid_str"
            return

        try:
            self.coord = LatLon(float(self.point_list[0]), float(self.point_list[1]))
            if not self.coord.is_valid():
                self.error = "not_wgs84"
                return
        except ValueError:
            self.error = "cant_parse"
            return

        self.valid = True

    def is_valid(self) -> tuple[bool, str]:
        """Return True if string parses, False and an error if not."""
        return (self.valid, self.error)

    @property
    def point(self) -> Point:
        """Return parsed point."""
        return self.coord.point
