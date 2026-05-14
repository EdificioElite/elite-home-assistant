"""Test fixtures for Elite Climate integration."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_frame_report_usage():
    """Prevent frame.report_usage from raising RuntimeError in tests."""
    with patch("homeassistant.helpers.frame.report_usage"):
        yield


@pytest.fixture
def hass():
    """Provide a mock HomeAssistant instance."""
    return MagicMock()


@pytest.fixture
def mock_api_session():
    """Mock aiohttp client session."""
    with patch(
        "custom_components.elite_climate.coordinator.async_get_clientsession"
    ) as mock_session:
        yield mock_session


@pytest.fixture
def coordinator(hass, mock_api_session):
    """Create a coordinator instance with mocked session."""
    from custom_components.elite_climate.coordinator import EliteClimateCoordinator

    coord = EliteClimateCoordinator(
        hass, email="test@example.com", password="testpass"
    )
    return coord
