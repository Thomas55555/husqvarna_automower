"""Test for map utils."""

import pytest
from shapely.geometry import Point

from ..map_utils import (
    LatLon,
    ValidatePointString,
    ValidateRGB,
    validate_image,
    validate_rotation,
)


@pytest.mark.asyncio
async def test_validate_rotation():
    """test validate rotation"""

    # Not numeric
    assert validate_rotation("23 deg") is False

    # Outside of bounds
    assert validate_rotation(360) is False
    assert validate_rotation(-360) is False

    # Integer
    assert validate_rotation(180) is True

    # Valid String
    assert validate_rotation("180") is True


@pytest.mark.asyncio
async def test_validate_image():
    """test validate image"""

    # Good Image
    assert (
        validate_image(
            "custom_components/husqvarna_automower/tests/resources/biltmore-min.png"
        )
        is True
    )

    # Bad Path
    assert (
        validate_image(
            "custom_components/husqvarna_automower/tests/resources/not_an_image.png"
        )
        is False
    )

    # Not an image
    assert (
        validate_image(
            "custom_components/husqvarna_automower/tests/resources/bad_image.png"
        )
        is False
    )


@pytest.mark.asyncio
async def test_validate_rgb():
    """test ValidateRGB"""

    # Valid RGB
    assert ValidateRGB("255,255,255").is_valid() is True

    # Not an integer
    assert ValidateRGB("255,255,a").is_valid() is False

    # Not a list
    assert ValidateRGB("255 255 255").is_valid() is False

    # Too many values
    assert ValidateRGB("255,255,255,255").is_valid() is False

    # Too few values
    assert ValidateRGB("255,255").is_valid() is False

    # Out of range
    assert ValidateRGB("255,255,256").is_valid() is False
    assert ValidateRGB("255,255,-1").is_valid() is False


@pytest.mark.asyncio
async def test_lat_lon():
    """test LatLon"""
    # Valid point
    assert LatLon(35.54028774, -82.5526962).is_valid() is True

    # Outside of bounds Lat is -90.0 to 90.0 Long is -180.0 to 180.0
    assert LatLon(-90.1, -82.5526962).is_valid() is False
    assert LatLon(90.1, -82.5526962).is_valid() is False
    assert LatLon(35.54028774, -180.1).is_valid() is False
    assert LatLon(35.54028774, 180.1).is_valid() is False

    # Returns Point
    assert LatLon(35.54028774, -82.5526962).point == Point(35.54028774, -82.5526962)


@pytest.mark.asyncio
async def test_validate_point_string():
    """test ValidatePointString"""

    # Valid point string
    assert ValidatePointString("35.54028774, -82.5526962").is_valid() == (True, "")

    # One point
    assert ValidatePointString("35.54028774").is_valid() == (False, "invalid_str")

    # More than two points
    assert ValidatePointString("35.54028774, -82.5526962, 35.54028774").is_valid() == (
        False,
        "invalid_str",
    )

    # Attribute error, not a string
    assert ValidatePointString([35.54028774, -82.5526962]).is_valid() == (
        False,
        "cant_parse",
    )

    # Value error, not numeric
    assert ValidatePointString("test, -82.5526962").is_valid() == (
        False,
        "cant_parse",
    )

    # Out of bounds
    assert ValidatePointString("35.54028774, -182.5526962").is_valid() == (
        False,
        "not_wgs84",
    )

    # Returns Point
    assert ValidatePointString("35.54028774, -82.5526962").point == Point(
        35.54028774, -82.5526962
    )
