"""Tests for Edificio Elite sensors."""

from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant


async def test_sensor_values(hass: HomeAssistant) -> None:
    """Test that sensors return correct values from coordinator data."""
    from custom_components.edificio_elite.sensor import EliteClimateSensor

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
    from custom_components.edificio_elite.sensor import EliteClimateSensor

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
    from custom_components.edificio_elite.sensor import EliteClimateSensor

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

    from datetime import datetime

    assert isinstance(sensor.native_value, datetime)
    assert sensor.native_value.year == 2026


async def test_modo_sensor(hass: HomeAssistant) -> None:
    """Test the modo sensor returns the mode string from the API."""
    from custom_components.edificio_elite.sensor import EliteClimateSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"modo": "refrigeracion"}
    coordinator.async_add_listener = MagicMock()

    sensor_def = {
        "key": "modo",
        "name": "Modo",
        "field": "modo",
        "device_class": None,
        "state_class": None,
        "unit": None,
        "icon": "mdi:heat-pump",
    }

    sensor = EliteClimateSensor(
        coordinator=coordinator,
        device_id="climatizacion",
        device_name="Climatización",
        sensor_def=sensor_def,
    )

    assert sensor.native_value == "refrigeracion"
    assert sensor.available is True


async def test_computed_sensor(hass: HomeAssistant) -> None:
    """Test a computed sensor returns the correct derived value."""
    from custom_components.edificio_elite.const import ACS_KWH_PER_M3, ACS_SENSORS
    from custom_components.edificio_elite.sensor import EliteClimateSensor

    sensor_def = next(s for s in ACS_SENSORS if s["key"] == "kwh_acs_abs")

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"m3_acs_abs": 10.0}
    coordinator.async_add_listener = MagicMock()

    sensor = EliteClimateSensor(
        coordinator=coordinator,
        device_id="agua_caliente",
        device_name="Agua Caliente Sanitaria",
        sensor_def=sensor_def,
    )

    assert sensor.native_value == round(10.0 * ACS_KWH_PER_M3, 3)
    assert sensor.available is True


async def test_computed_sensor_none_when_field_missing(hass: HomeAssistant) -> None:
    """Test a computed sensor returns None when the source field is missing."""
    from custom_components.edificio_elite.const import ACS_SENSORS
    from custom_components.edificio_elite.sensor import EliteClimateSensor

    sensor_def = next(s for s in ACS_SENSORS if s["key"] == "kwh_acs_abs")

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"m3_acs_abs": None}
    coordinator.async_add_listener = MagicMock()

    sensor = EliteClimateSensor(
        coordinator=coordinator,
        device_id="agua_caliente",
        device_name="Agua Caliente Sanitaria",
        sensor_def=sensor_def,
    )

    assert sensor.native_value is None


async def test_afs_sensor_values(hass: HomeAssistant) -> None:
    """Test that AFS sensors return correct values from coordinator data."""
    from custom_components.edificio_elite.sensor import EliteClimateSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {
        "m3_afs": 0.456,
        "m3_afs_abs": 789.012,
        "m3_afs_mes_inicio": 5.678,
    }
    coordinator.async_add_listener = MagicMock()

    sensor_def = {
        "key": "m3_afs_abs",
        "name": "Consumo AFS (contador)",
        "field": "m3_afs_abs",
        "device_class": "water",
        "state_class": "total_increasing",
        "unit": "m³",
        "icon": "mdi:water-outline",
    }

    sensor = EliteClimateSensor(
        coordinator=coordinator,
        device_id="agua_fria_sanitaria",
        device_name="Agua Fría Sanitaria",
        sensor_def=sensor_def,
    )

    assert sensor.native_value == 789.012
    assert sensor.available is True


async def test_afs_sensor_null_data(hass: HomeAssistant) -> None:
    """Test AFS sensor returns None when coordinator data is None."""
    from custom_components.edificio_elite.sensor import EliteClimateSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = None
    coordinator.async_add_listener = MagicMock()

    sensor_def = {
        "key": "m3_afs",
        "name": "Consumo AFS",
        "field": "m3_afs",
        "device_class": "water",
        "state_class": None,
        "unit": "m³",
        "icon": "mdi:water-outline",
    }

    sensor = EliteClimateSensor(
        coordinator=coordinator,
        device_id="agua_fria_sanitaria",
        device_name="Agua Fría Sanitaria",
        sensor_def=sensor_def,
    )

    assert sensor.native_value is None


async def test_afs_sensor_device_info(hass: HomeAssistant) -> None:
    """Test AFS sensor has the correct device info."""
    from custom_components.edificio_elite.sensor import EliteClimateSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"m3_afs_abs": 100.0}
    coordinator.async_add_listener = MagicMock()

    sensor_def = {
        "key": "m3_afs_abs",
        "name": "Consumo AFS (contador)",
        "field": "m3_afs_abs",
        "device_class": "water",
        "state_class": "total_increasing",
        "unit": "m³",
        "icon": "mdi:water-outline",
    }

    sensor = EliteClimateSensor(
        coordinator=coordinator,
        device_id="agua_fria_sanitaria",
        device_name="Agua Fría Sanitaria",
        sensor_def=sensor_def,
    )

    assert sensor.unique_id == "agua_fria_sanitaria_m3_afs_abs"
    assert sensor.name == "Consumo AFS (contador)"
