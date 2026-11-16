"""Tests for the Edificio Elite shared API client."""

from unittest.mock import MagicMock

import pytest
from aiohttp import ClientError
from homeassistant.helpers.update_coordinator import UpdateFailed


class MockResponse:
    """Mock aiohttp response with async context manager protocol."""

    def __init__(self, status, json_data=None, text_data=None):
        self.status = status
        self._json_data = json_data
        self._text_data = text_data

    async def json(self):
        return self._json_data

    async def text(self):
        return self._text_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


async def test_login_success(hass, mock_api_session):
    """Login stores the token and identifies Home Assistant as source."""
    from custom_components.edificio_elite.api import EliteApiClient

    mock_session = MagicMock()
    mock_session.post.return_value = MockResponse(200, {"token": "jwt-123"})
    mock_api_session.return_value = mock_session

    client = EliteApiClient(hass, email="test@example.com", password="pass")
    await client.async_login()

    assert client.token == "jwt-123"
    args, kwargs = mock_session.post.call_args
    assert args[0].endswith("/auth/login")
    assert kwargs["json"]["source"] == "home-assistant"
    assert kwargs["json"]["email"] == "test@example.com"
    assert kwargs["json"]["password"] == "pass"


async def test_login_failure_raises(hass, mock_api_session):
    """A rejected login raises UpdateFailed."""
    from custom_components.edificio_elite.api import EliteApiClient

    mock_session = MagicMock()
    mock_session.post.return_value = MockResponse(401, None, "bad credentials")
    mock_api_session.return_value = mock_session

    client = EliteApiClient(hass, email="test@example.com", password="wrong")
    with pytest.raises(UpdateFailed):
        await client.async_login()


async def test_get_returns_json(hass, mock_api_session):
    """GET returns the decoded JSON body."""
    from custom_components.edificio_elite.api import EliteApiClient

    mock_session = MagicMock()
    mock_session.get.return_value = MockResponse(200, {"kwh_calor": 1.5})
    mock_api_session.return_value = mock_session

    client = EliteApiClient(hass, email="test@example.com", password="pass")
    client._token = "jwt-123"

    result = await client.async_get("/consumo-actual")
    assert result["kwh_calor"] == 1.5
    _, kwargs = mock_session.get.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer jwt-123"
    mock_session.post.assert_not_called()


async def test_get_401_relogins_and_retries(hass, mock_api_session):
    """A 401 triggers one re-login and one retry."""
    from custom_components.edificio_elite.api import EliteApiClient

    mock_session = MagicMock()
    mock_session.post.return_value = MockResponse(200, {"token": "new-token"})
    mock_session.get.side_effect = [
        MockResponse(401, None, "expired"),
        MockResponse(200, {"power_w": 100}),
    ]
    mock_api_session.return_value = mock_session

    client = EliteApiClient(hass, email="test@example.com", password="pass")
    client._token = "expired"

    result = await client.async_get("/consumo-actual")
    assert result["power_w"] == 100
    assert client.token == "new-token"
    assert mock_session.get.call_count == 2
    mock_session.post.assert_called_once()


async def test_get_401_after_retry_raises(hass, mock_api_session):
    """A second 401 is not retried again."""
    from custom_components.edificio_elite.api import EliteApiClient

    mock_session = MagicMock()
    mock_session.post.return_value = MockResponse(200, {"token": "new-token"})
    mock_session.get.return_value = MockResponse(401, None, "nope")
    mock_api_session.return_value = mock_session

    client = EliteApiClient(hass, email="test@example.com", password="pass")
    client._token = "expired"

    with pytest.raises(UpdateFailed):
        await client.async_get("/consumo-actual")
    assert mock_session.get.call_count == 2
    mock_session.post.assert_called_once()


async def test_get_non_200_raises(hass, mock_api_session):
    """A non-200 GET raises UpdateFailed."""
    from custom_components.edificio_elite.api import EliteApiClient

    mock_session = MagicMock()
    mock_session.get.return_value = MockResponse(500, None, "server error")
    mock_api_session.return_value = mock_session

    client = EliteApiClient(hass, email="test@example.com", password="pass")
    client._token = "jwt-123"

    with pytest.raises(UpdateFailed):
        await client.async_get("/consumo-actual")


async def test_login_rate_limited_raises(hass, mock_api_session):
    """A 429 login raises UpdateFailed."""
    from custom_components.edificio_elite.api import EliteApiClient

    mock_session = MagicMock()
    mock_session.post.return_value = MockResponse(429, None, "slow down")
    mock_api_session.return_value = mock_session

    client = EliteApiClient(hass, email="test@example.com", password="pass")

    with pytest.raises(UpdateFailed):
        await client.async_login()


async def test_get_network_error_propagates(hass, mock_api_session):
    """Network errors propagate so coordinators can keep previous data."""
    from custom_components.edificio_elite.api import EliteApiClient

    mock_session = MagicMock()
    mock_session.get.side_effect = ClientError("boom")
    mock_api_session.return_value = mock_session

    client = EliteApiClient(hass, email="test@example.com", password="pass")
    client._token = "jwt-123"

    with pytest.raises(ClientError):
        await client.async_get("/consumo-actual")


async def test_login_network_error_propagates(hass, mock_api_session):
    """Transport errors during login propagate so callers can keep data."""
    from custom_components.edificio_elite.api import EliteApiClient

    mock_session = MagicMock()
    mock_session.post.side_effect = ClientError("boom")
    mock_api_session.return_value = mock_session

    client = EliteApiClient(hass, email="test@example.com", password="pass")
    with pytest.raises(ClientError):
        await client.async_login()
