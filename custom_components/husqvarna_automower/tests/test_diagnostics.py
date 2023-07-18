"""Test for diagnostics module."""
import pytest
from homeassistant.core import HomeAssistant

from ..diagnostics import TO_REDACT, async_get_config_entry_diagnostics

from .test_common import setup_entity


@pytest.mark.asyncio
async def test_redact(hass: HomeAssistant):
    """test automower initialization"""

    config_entry = await setup_entity(hass)

    diag_data = await async_get_config_entry_diagnostics(hass, config_entry)

    redacted = []
    # pylint: disable=invalid-name
    for k, v in diag_data.get("config_entry").get("data").items():
        if k in TO_REDACT:  # pylint: disable=invalid-name
            assert v.get(k) == "**REDACTED**"  # pylint: disable=invalid-name
            redacted.append(k)  # pylint: disable=invalid-name

    # pylint: disable=invalid-name
    for k, v in diag_data.get("config_entry").get("options").items():
        if k in TO_REDACT:  # pylint: disable=invalid-name
            assert v == "**REDACTED**"  # pylint: disable=invalid-name
            redacted.append(k)
        if isinstance(v, dict):
            for k2, v2 in v.items():  # pylint: disable=invalid-name
                if k2 in TO_REDACT:  # pylint: disable=invalid-name
                    assert v2 == "**REDACTED**"  # pylint: disable=invalid-name
                    redacted.append(k2)  # pylint: disable=invalid-name

    assert (
        set(TO_REDACT)
        .difference(redacted)
        .issubset(
            set(
                [
                    "positions",
                    "refresh_token",
                    "access_token",
                ]
            )
        )
    )
