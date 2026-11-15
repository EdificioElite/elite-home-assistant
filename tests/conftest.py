"""Test fixtures for Edificio Elite integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_frame_report_usage():
    """Prevent frame.report_usage from raising RuntimeError in tests."""
    with patch("homeassistant.helpers.frame.report_usage"):
        yield


@pytest.fixture
def hass():
    """Provide a mock HomeAssistant instance."""
    hass = MagicMock()
    hass.config_entries.flow.async_init = AsyncMock()
    hass.config_entries.flow.async_configure = AsyncMock()
    return hass


@pytest.fixture
def mock_api_session():
    """Mock aiohttp client session used by the API client."""
    with patch(
        "custom_components.edificio_elite.api.async_get_clientsession"
    ) as mock_session:
        yield mock_session


@pytest.fixture
def api_client(hass, mock_api_session):
    """Create an API client with a mocked session."""
    from custom_components.edificio_elite.api import EliteApiClient

    return EliteApiClient(hass, email="test@example.com", password="testpass")


@pytest.fixture
def coordinator(hass, api_client):
    """Create a climate coordinator backed by the mocked client."""
    from custom_components.edificio_elite.coordinator import EliteClimateCoordinator

    return EliteClimateCoordinator(hass, api_client)
