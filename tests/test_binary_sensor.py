"""Tests for Edificio Elite binary sensor."""

from unittest.mock import MagicMock


async def test_is_running_true(mock_hass: MagicMock) -> None:
    """Test binary sensor is on when power > 0."""
    from custom_components.edificio_elite.binary_sensor import EliteClimateRunningSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"power_w": 1500}
    coordinator.async_add_listener = MagicMock()

    sensor = EliteClimateRunningSensor(coordinator)

    assert sensor.is_on is True
    assert sensor.available is True


async def test_is_running_false(mock_hass: MagicMock) -> None:
    """Test binary sensor is off when power == 0."""
    from custom_components.edificio_elite.binary_sensor import EliteClimateRunningSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"power_w": 0}
    coordinator.async_add_listener = MagicMock()

    sensor = EliteClimateRunningSensor(coordinator)

    assert sensor.is_on is False


async def test_is_running_null_when_no_data(mock_hass: MagicMock) -> None:
    """Test binary sensor is None when data is missing."""
    from custom_components.edificio_elite.binary_sensor import EliteClimateRunningSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = None
    coordinator.async_add_listener = MagicMock()

    sensor = EliteClimateRunningSensor(coordinator)

    assert sensor.is_on is None


async def test_is_running_null_when_power_none(mock_hass: MagicMock) -> None:
    """Test binary sensor is None when power_w is None."""
    from custom_components.edificio_elite.binary_sensor import EliteClimateRunningSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"power_w": None}
    coordinator.async_add_listener = MagicMock()

    sensor = EliteClimateRunningSensor(coordinator)

    assert sensor.is_on is None


async def test_modo_calefaccion_activado_true(mock_hass: MagicMock) -> None:
    """Test modo_calefaccion_activado binary sensor is on when heating mode active."""
    from custom_components.edificio_elite.binary_sensor import EliteModeBinarySensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"modo_calefaccion_activado": True}
    coordinator.async_add_listener = MagicMock()

    sensor_def = {
        "key": "modo_calefaccion_activado",
        "name": "Modo calefacción activado",
        "field": "modo_calefaccion_activado",
    }

    sensor = EliteModeBinarySensor(coordinator, sensor_def)

    assert sensor.is_on is True
    assert sensor.available is True


async def test_modo_calefaccion_activado_false(mock_hass: MagicMock) -> None:
    """Test modo_calefaccion_activado binary sensor is off when heating mode inactive."""
    from custom_components.edificio_elite.binary_sensor import EliteModeBinarySensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"modo_calefaccion_activado": False}
    coordinator.async_add_listener = MagicMock()

    sensor_def = {
        "key": "modo_calefaccion_activado",
        "name": "Modo calefacción activado",
        "field": "modo_calefaccion_activado",
    }

    sensor = EliteModeBinarySensor(coordinator, sensor_def)

    assert sensor.is_on is False


async def test_modo_refrigeracion_activado_true(mock_hass: MagicMock) -> None:
    """Test modo_refrigeracion_activado binary sensor is on when cooling mode active."""
    from custom_components.edificio_elite.binary_sensor import EliteModeBinarySensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"modo_refrigeracion_activado": True}
    coordinator.async_add_listener = MagicMock()

    sensor_def = {
        "key": "modo_refrigeracion_activado",
        "name": "Modo refrigeración activado",
        "field": "modo_refrigeracion_activado",
    }

    sensor = EliteModeBinarySensor(coordinator, sensor_def)

    assert sensor.is_on is True
    assert sensor.available is True


async def test_modo_sensor_null_when_no_data(mock_hass: MagicMock) -> None:
    """Test mode binary sensor returns None when data is missing."""
    from custom_components.edificio_elite.binary_sensor import EliteModeBinarySensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = None
    coordinator.async_add_listener = MagicMock()

    sensor_def = {
        "key": "modo_calefaccion_activado",
        "name": "Modo calefacción activado",
        "field": "modo_calefaccion_activado",
    }

    sensor = EliteModeBinarySensor(coordinator, sensor_def)

    assert sensor.is_on is None
