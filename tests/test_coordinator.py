"""Tests for Elite Climate coordinator."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientError
from homeassistant.helpers.update_coordinator import UpdateFailed


async def test_login_success(hass, mock_api_session):
    from custom_components.elite_climate.coordinator import EliteClimateCoordinator

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"token": "jwt-token-123", "user": {"id": 1}})
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post.return_value = mock_resp
    mock_api_session.return_value = mock_session

    coord = EliteClimateCoordinator(hass, email="test@example.com", password="pass")
    await coord._login()

    assert coord._token == "jwt-token-123"


async def test_login_failure(hass, mock_api_session):
    from custom_components.elite_climate.coordinator import EliteClimateCoordinator

    mock_resp = MagicMock()
    mock_resp.status = 401
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post.return_value = mock_resp
    mock_api_session.return_value = mock_session

    coord = EliteClimateCoordinator(hass, email="test@example.com", password="wrong")

    with pytest.raises(UpdateFailed):
        await coord._login()


async def test_fetch_consumo_actual_success(hass, mock_api_session):
    from custom_components.elite_climate.coordinator import EliteClimateCoordinator

    coord = EliteClimateCoordinator(hass, email="test@example.com", password="pass")
    coord._token = "jwt-123"

    sample_data = {
        "timestamp": "2026-05-13T20:00:00.000Z",
        "kwh_calor": 1.234,
        "kwh_frio": 0.567,
        "m3_acs": 0.123,
        "kwh_acs": 5.720,
        "kwh_calor_abs": 12345.678,
        "kwh_frio_abs": 5678.901,
        "m3_acs_abs": 456.789,
        "kwh_calor_mes_inicio": 50.123,
        "kwh_frio_mes_inicio": 20.456,
        "m3_acs_mes_inicio": 3.789,
        "temp_impulsion": 35.5,
        "temp_retorno": 30.2,
        "power_w": 1200,
    }

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value=sample_data)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp
    mock_api_session.return_value = mock_session

    result = await coord._fetch_consumo_actual()
    assert result["kwh_calor"] == 1.234
    assert result["power_w"] == 1200


async def test_fetch_null_data_keeps_previous(hass, mock_api_session):
    from custom_components.elite_climate.coordinator import EliteClimateCoordinator

    coord = EliteClimateCoordinator(hass, email="test@example.com", password="pass")
    coord._token = "jwt-123"
    coord.data = {"power_w": 500}

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value=None)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp
    mock_api_session.return_value = mock_session

    result = await coord._fetch_consumo_actual()
    assert result["power_w"] == 500


async def test_fetch_network_error_keeps_previous(hass, mock_api_session):
    from custom_components.elite_climate.coordinator import EliteClimateCoordinator

    coord = EliteClimateCoordinator(hass, email="test@example.com", password="pass")
    coord._token = "jwt-123"
    coord.data = {"power_w": 800}

    mock_session = MagicMock()
    mock_session.get.side_effect = ClientError("Connection refused")
    mock_api_session.return_value = mock_session

    result = await coord._fetch_consumo_actual()
    assert result["power_w"] == 800


async def test_fetch_401_renews_token(hass, mock_api_session):
    from custom_components.elite_climate.coordinator import EliteClimateCoordinator

    coord = EliteClimateCoordinator(hass, email="test@example.com", password="pass")
    coord._token = "expired-token"

    original_login = coord._login
    original_fetch = coord._fetch_consumo_actual

    call_count = {"login": 0, "fetch": 0}

    async def login_side_effect():
        call_count["login"] += 1
        coord._token = "new-token"

    async def fetch_side_effect():
        call_count["fetch"] += 1
        if call_count["fetch"] == 1:
            coord._token = None
            await original_login()
            return await original_fetch()
        return {"power_w": 100}

    coord._login = login_side_effect
    coord._fetch_consumo_actual = fetch_side_effect

    result = await coord._async_update_data()
    assert result["power_w"] == 100
    assert call_count["login"] >= 1
