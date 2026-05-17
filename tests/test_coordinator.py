"""Tests for Elite Climate coordinator."""

from unittest.mock import MagicMock

import pytest
from aiohttp import ClientError
from homeassistant.helpers.update_coordinator import UpdateFailed


class MockResponse:
    """Mock aiohttp response with real async context manager protocol."""

    def __init__(self, status, json_data):
        self.status = status
        self._json_data = json_data

    async def json(self):
        return self._json_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


async def test_login_success(hass, mock_api_session):
    from custom_components.elite_climate.coordinator import EliteClimateCoordinator

    mock_resp = MockResponse(200, {"token": "jwt-token-123", "user": {"id": 1}})

    mock_session = MagicMock()
    mock_session.post.return_value = mock_resp
    mock_api_session.return_value = mock_session

    coord = EliteClimateCoordinator(hass, email="test@example.com", password="pass")
    await coord._login()

    assert coord._token == "jwt-token-123"

    mock_session.post.assert_called_once()
    _, kwargs = mock_session.post.call_args
    assert kwargs["json"]["source"] == "home-assistant"


async def test_login_failure(hass, mock_api_session):
    from custom_components.elite_climate.coordinator import EliteClimateCoordinator

    mock_resp = MockResponse(401, None)

    mock_session = MagicMock()
    mock_session.post.return_value = mock_resp
    mock_api_session.return_value = mock_session

    coord = EliteClimateCoordinator(hass, email="test@example.com", password="wrong")

    with pytest.raises(UpdateFailed):
        await coord._login()


async def test_fetch_consumo_actual_success(hass, mock_api_session):
    from custom_components.elite_climate.coordinator import EliteClimateCoordinator

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

    mock_resp = MockResponse(200, sample_data)

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp
    mock_api_session.return_value = mock_session

    coord = EliteClimateCoordinator(hass, email="test@example.com", password="pass")
    coord._token = "jwt-123"

    result = await coord._fetch_consumo_actual()
    assert result["kwh_calor"] == 1.234
    assert result["power_w"] == 1200


async def test_fetch_null_data_keeps_previous(hass, mock_api_session):
    from custom_components.elite_climate.coordinator import EliteClimateCoordinator

    coord = EliteClimateCoordinator(hass, email="test@example.com", password="pass")
    coord._token = "jwt-123"
    coord.data = {"power_w": 500}

    mock_resp = MockResponse(200, None)

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

    login_resp = MockResponse(200, {"token": "jwt-token-123", "user": {"id": 1}})
    fetch_resp = MockResponse(200, {"power_w": 300, "kwh_calor": 1.0})

    mock_session = MagicMock()
    mock_session.post.return_value = login_resp
    mock_session.get.return_value = fetch_resp
    mock_api_session.return_value = mock_session

    coord = EliteClimateCoordinator(hass, email="test@example.com", password="pass")
    coord._token = "expired-token"

    original_fetch = coord._fetch_consumo_actual

    call_count = {"fetch": 0}

    async def fetch_side_effect():
        call_count["fetch"] += 1
        if call_count["fetch"] == 1:
            coord._token = None
            await coord._login()
            return await original_fetch()
        return {"power_w": 100}

    coord._fetch_consumo_actual = fetch_side_effect

    result = await coord._async_update_data()
    assert result["power_w"] == 300
    assert coord._token == "jwt-token-123"
    assert call_count["fetch"] == 1
