"""Tests for Elite Climate sensors."""

from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant


async def test_sensor_values(hass: HomeAssistant) -> None:
    """Test that sensors return correct values from coordinator data."""
    from custom_components.elite_climate.sensor import EliteClimateSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {
        "timestamp": "2026-05-13T20:00:00.000Z",
        "kwh_calor": 2.5,
        "power_w": 1500,
        "m3_acs": 0.05,
    }
    coordinator.async_add_listener = MagicMock()

    sensor_def = {
        "key": "kwh_calor",
        "name": "Energía calefacción",
        "field": "kwh_calor",
        "device_class": "energy",
        "state_class": "measurement",
        "unit": "kWh",
        "icon": None,
    }

    sensor = EliteClimateSensor(
        coordinator=coordinator,
        device_id="climatizacion",
        device_name="Climatización",
        sensor_def=sensor_def,
    )

    assert sensor.native_value == 2.5
    assert sensor.available is True


async def test_sensor_null_data(hass: HomeAssistant) -> None:
    """Test sensor returns None when coordinator data is None."""
    from custom_components.elite_climate.sensor import EliteClimateSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = None
    coordinator.async_add_listener = MagicMock()

    sensor_def = {
        "key": "kwh_calor",
        "name": "Energía calefacción",
        "field": "kwh_calor",
        "device_class": "energy",
        "state_class": "measurement",
        "unit": "kWh",
        "icon": None,
    }

    sensor = EliteClimateSensor(
        coordinator=coordinator,
        device_id="climatizacion",
        device_name="Climatización",
        sensor_def=sensor_def,
    )

    assert sensor.native_value is None


async def test_last_update_timestamp(hass: HomeAssistant) -> None:
    """Test the last_update sensor parses timestamp correctly."""
    from custom_components.elite_climate.sensor import EliteClimateSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"timestamp": "2026-05-13T20:00:00.000Z"}
    coordinator.async_add_listener = MagicMock()

    sensor_def = {
        "key": "last_update",
        "name": "Última actualización",
        "field": "timestamp",
        "device_class": "timestamp",
        "state_class": None,
        "unit": None,
        "icon": "mdi:clock-outline",
    }

    sensor = EliteClimateSensor(
        coordinator=coordinator,
        device_id="climatizacion",
        device_name="Climatización",
        sensor_def=sensor_def,
    )

    from datetime import datetime, timezone

    assert isinstance(sensor.native_value, datetime)
    assert sensor.native_value.year == 2026
