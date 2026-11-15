"""Tests for Edificio Elite climate coordinator."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientError
from homeassistant.helpers.update_coordinator import UpdateFailed

SAMPLE_DATA = {
    "timestamp": "2026-05-13T20:00:00.000Z",
    "kwh_calor": 1.234,
    "kwh_frio": 0.567,
    "m3_acs": 0.123,
    "power_w": 1200,
    "modo": "calefaccion",
}


def make_coordinator(hass, return_value=None, side_effect=None):
    """Create a climate coordinator with a mocked API client."""
    from custom_components.edificio_elite.coordinator import EliteClimateCoordinator

    client = MagicMock()
    if side_effect is not None:
        client.async_get = AsyncMock(side_effect=side_effect)
    else:
        client.async_get = AsyncMock(return_value=return_value)
    return EliteClimateCoordinator(hass, client)


async def test_fetch_consumo_actual_success(hass):
    """The coordinator returns the API payload."""
    coord = make_coordinator(hass, return_value=SAMPLE_DATA)
    result = await coord._fetch_consumo_actual()
    assert result["kwh_calor"] == 1.234
    assert result["power_w"] == 1200


async def test_fetch_null_data_keeps_previous(hass):
    """A null payload keeps the previous data."""
    coord = make_coordinator(hass, return_value=None)
    coord.data = {"power_w": 500}
    result = await coord._fetch_consumo_actual()
    assert result["power_w"] == 500


async def test_fetch_null_data_without_previous_raises(hass):
    """A null payload without previous data raises UpdateFailed."""
    coord = make_coordinator(hass, return_value=None)
    with pytest.raises(UpdateFailed):
        await coord._fetch_consumo_actual()


async def test_fetch_network_error_keeps_previous(hass):
    """A network error keeps the previous data."""
    coord = make_coordinator(hass, side_effect=ClientError("Connection refused"))
    coord.data = {"power_w": 800}
    result = await coord._fetch_consumo_actual()
    assert result["power_w"] == 800


async def test_fetch_update_failed_propagates(hass):
    """UpdateFailed from the client is not swallowed."""
    coord = make_coordinator(hass, side_effect=UpdateFailed("bad status"))
    coord.data = {"power_w": 800}
    with pytest.raises(UpdateFailed):
        await coord._fetch_consumo_actual()


async def test_update_data_calls_fetch(hass):
    """_async_update_data delegates to _fetch_consumo_actual."""
    coord = make_coordinator(hass, return_value=SAMPLE_DATA)
    result = await coord._async_update_data()
    assert result["power_w"] == 1200
