"""Test fixtures for Edificio Elite integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_hass():
    """Provide a mock HomeAssistant instance for unit tests.

    The real ``hass`` fixture from pytest-homeassistant-custom-component
    remains available for integration tests.
    """
    mock_hass = MagicMock()
    mock_hass.config_entries.flow.async_init = AsyncMock()
    mock_hass.config_entries.flow.async_configure = AsyncMock()
    return mock_hass


@pytest.fixture
def mock_api_session():
    """Mock aiohttp client session used by the API client."""
    with patch(
        "custom_components.edificio_elite.api.async_get_clientsession"
    ) as mock_session:
        yield mock_session


@pytest.fixture
def api_client(mock_hass, mock_api_session):
    """Create an API client with a mocked session."""
    from custom_components.edificio_elite.api import EliteApiClient

    return EliteApiClient(mock_hass, email="test@example.com", password="testpass")


@pytest.fixture
def coordinator(mock_hass, api_client):
    """Create a climate coordinator backed by the mocked client."""
    from custom_components.edificio_elite.coordinator import EliteClimateCoordinator

    return EliteClimateCoordinator(mock_hass, api_client)
