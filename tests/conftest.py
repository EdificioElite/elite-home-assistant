"""Test fixtures for Elite Climate integration."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant


@pytest.fixture
def mock_api_session():
    """Mock aiohttp client session."""
    with patch(
        "homeassistant.helpers.aiohttp_client.async_get_clientsession"
    ) as mock_session:
        yield mock_session


@pytest.fixture
def coordinator(hass: HomeAssistant, mock_api_session):
    """Create a coordinator instance with mocked session."""
    from custom_components.elite_climate.coordinator import EliteClimateCoordinator

    coord = EliteClimateCoordinator(
        hass, email="test@example.com", password="testpass"
    )
    return coord
