"""Tests for Elite Climate binary sensor."""

from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant


async def test_is_running_true(hass: HomeAssistant) -> None:
    """Test binary sensor is on when power > 0."""
    from custom_components.elite_climate.binary_sensor import EliteClimateRunningSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"power_w": 1500}
    coordinator.async_add_listener = MagicMock()

    sensor = EliteClimateRunningSensor(coordinator)

    assert sensor.is_on is True
    assert sensor.available is True


async def test_is_running_false(hass: HomeAssistant) -> None:
    """Test binary sensor is off when power == 0."""
    from custom_components.elite_climate.binary_sensor import EliteClimateRunningSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"power_w": 0}
    coordinator.async_add_listener = MagicMock()

    sensor = EliteClimateRunningSensor(coordinator)

    assert sensor.is_on is False


async def test_is_running_null_when_no_data(hass: HomeAssistant) -> None:
    """Test binary sensor is None when data is missing."""
    from custom_components.elite_climate.binary_sensor import EliteClimateRunningSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = None
    coordinator.async_add_listener = MagicMock()

    sensor = EliteClimateRunningSensor(coordinator)

    assert sensor.is_on is None


async def test_is_running_null_when_power_none(hass: HomeAssistant) -> None:
    """Test binary sensor is None when power_w is None."""
    from custom_components.elite_climate.binary_sensor import EliteClimateRunningSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"power_w": None}
    coordinator.async_add_listener = MagicMock()

    sensor = EliteClimateRunningSensor(coordinator)

    assert sensor.is_on is None
