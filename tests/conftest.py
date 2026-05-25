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
    """Mock aiohttp client session."""
    with patch(
        "custom_components.edificio_elite.coordinator.async_get_clientsession"
    ) as mock_session:
        yield mock_session


@pytest.fixture
def coordinator(hass, mock_api_session):
    """Create a coordinator instance with mocked session."""
    from custom_components.edificio_elite.coordinator import EliteClimateCoordinator

    coord = EliteClimateCoordinator(
        hass, email="test@example.com", password="testpass"
    )
    return coord
