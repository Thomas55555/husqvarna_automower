"""Utilities for parsing and validating coordinates."""

from PIL import Image, UnidentifiedImageError
from shapely.geometry import Point

from .const import LAT_LON_BOUNDS


def validate_rotation(rotation: float) -> float:
    """Ensure rotation is in degrees."""
    try:
        rotation = float(rotation)
        if rotation < 360 and rotation > -360:
            return True
        return False
    except ValueError:
        return False


def validate_image(img_path: str) -> bool:
    """Ensure image is valid."""
    try:
        im = Image.open(img_path)
        im.verify()
        im.close()
    except (FileNotFoundError, UnidentifiedImageError):
        return False
    return True


class ValidateRGB:
    """Ensure RGB input is valid."""

    def __init__(self, rgb_str: str) -> None:
        """Initialize the ValidateRGB Object."""
        self.rgb_val = rgb_str.split(",")

    def is_valid(self) -> bool:
        """Return True if a valid RGB value."""
        if len(self.rgb_val) != 3:
            return False
        else:
            for c in range(3):
                try:
                    color_val = int(self.rgb_val[c])
                    if color_val < 0 or color_val > 255:
                        return False
                        break
                    else:
                        self.rgb_val[c] = color_val
                except ValueError:
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
        self.error = ""
        self.valid = False
        self.coord = None

        try:
            self.point_list = self.point_str.split(",")
        except AttributeError:
            self.error = "cant_parse"
            return

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
