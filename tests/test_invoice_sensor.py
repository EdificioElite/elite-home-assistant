"""Tests for the Edificio Elite invoice sensors."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant


def make_sensor(coordinator, sensor_def):
    """Create an invoice sensor with a mocked coordinator."""
    from custom_components.edificio_elite.sensor import EliteClimateSensor

    return EliteClimateSensor(
        coordinator=coordinator,
        device_id="facturacion",
        device_name="Facturación",
        sensor_def=sensor_def,
    )


async def test_invoice_monetary_sensor(hass: HomeAssistant) -> None:
    """The total invoice sensor exposes value and detail attributes."""
    from custom_components.edificio_elite.const import FACTURACION_SENSORS

    sensor_def = next(
        s for s in FACTURACION_SENSORS if s["key"] == "importe_total"
    )
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {
        "importe_total": 87.45,
        "id_factura": "2026-10-01",
        "fecha_factura_inicio": "2026-10-01T00:00:00.000Z",
        "fecha_factura_fin": "2026-10-31T00:00:00.000Z",
        "tiene_pdf": True,
        "num_facturas": 3,
        "importe_variable_acs": 12.4,
    }
    coordinator.async_add_listener = MagicMock()

    sensor = make_sensor(coordinator, sensor_def)

    assert sensor.native_value == 87.45
    assert sensor.available is True
    attrs = sensor.extra_state_attributes
    assert attrs["id_factura"] == "2026-10-01"
    assert attrs["num_facturas"] == 3
    assert attrs["dashboard_url"] == "https://www.edificioelite.com/"


async def test_invoice_attributes_omit_missing_values(
    hass: HomeAssistant,
) -> None:
    """Missing invoice details are not exposed as None attributes."""
    from custom_components.edificio_elite.const import FACTURACION_SENSORS

    sensor_def = next(
        s for s in FACTURACION_SENSORS if s["key"] == "importe_total"
    )
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"importe_total": 10.0}
    coordinator.async_add_listener = MagicMock()

    sensor = make_sensor(coordinator, sensor_def)

    attrs = sensor.extra_state_attributes
    assert "id_factura" not in attrs
    assert "tiene_pdf" not in attrs
    assert attrs["dashboard_url"] == "https://www.edificioelite.com/"


async def test_invoice_period_sensor_parses_timestamp(
    hass: HomeAssistant,
) -> None:
    """Period-end sensor returns a datetime."""
    from custom_components.edificio_elite.const import FACTURACION_SENSORS

    sensor_def = next(s for s in FACTURACION_SENSORS if s["key"] == "periodo_fin")
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"fecha_factura_fin": "2026-10-31T00:00:00.000Z"}
    coordinator.async_add_listener = MagicMock()

    sensor = make_sensor(coordinator, sensor_def)

    assert sensor.native_value == datetime(
        2026, 10, 31, tzinfo=timezone.utc
    )


async def test_invoice_sensor_empty_data(hass: HomeAssistant) -> None:
    """An empty invoice list yields zero accumulated and no failure."""
    from custom_components.edificio_elite.const import FACTURACION_SENSORS
    from custom_components.edificio_elite.invoices import build_invoice_data

    sensor_def = next(
        s for s in FACTURACION_SENSORS if s["key"] == "importe_acumulado"
    )
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = build_invoice_data([])
    coordinator.async_add_listener = MagicMock()

    sensor = make_sensor(coordinator, sensor_def)

    assert sensor.native_value == 0
    assert sensor.available is True


async def test_non_invoice_sensor_has_no_invoice_attributes(
    hass: HomeAssistant,
) -> None:
    """Only the total invoice sensor carries invoice detail attributes."""
    from custom_components.edificio_elite.const import FACTURACION_SENSORS

    sensor_def = next(s for s in FACTURACION_SENSORS if s["key"] == "importe_fijo")
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"importe_fijo": 20.0}
    coordinator.async_add_listener = MagicMock()

    sensor = make_sensor(coordinator, sensor_def)

    assert sensor.native_value == 20.0
    assert sensor.extra_state_attributes is None


async def test_invoice_sensor_device_info(hass: HomeAssistant) -> None:
    """Invoice sensors belong to the Facturación device."""
    from custom_components.edificio_elite.const import (
        DEVICE_FACTURACION,
        DOMAIN,
        FACTURACION_SENSORS,
    )

    sensor_def = next(
        s for s in FACTURACION_SENSORS if s["key"] == "importe_total"
    )
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"importe_total": 1.0}
    coordinator.async_add_listener = MagicMock()

    sensor = make_sensor(coordinator, sensor_def)

    assert sensor.unique_id == "facturacion_importe_total"
    assert sensor.device_info["identifiers"] == {(DOMAIN, DEVICE_FACTURACION)}


async def test_invoice_period_sensor_handles_bad_timestamp(
    hass: HomeAssistant,
) -> None:
    """A malformed timestamp yields None instead of raising."""
    from custom_components.edificio_elite.const import FACTURACION_SENSORS

    sensor_def = next(
        s for s in FACTURACION_SENSORS if s["key"] == "periodo_fin"
    )
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"fecha_factura_fin": "not-a-date"}
    coordinator.async_add_listener = MagicMock()

    sensor = make_sensor(coordinator, sensor_def)

    assert sensor.native_value is None


async def test_invoice_sensor_unavailable_on_failed_update(
    hass: HomeAssistant,
) -> None:
    """Invoice sensors become unavailable when the refresh fails."""
    from custom_components.edificio_elite.const import FACTURACION_SENSORS

    sensor_def = next(
        s for s in FACTURACION_SENSORS if s["key"] == "importe_total"
    )
    coordinator = MagicMock()
    coordinator.last_update_success = False
    coordinator.data = {"importe_total": 10.0}
    coordinator.async_add_listener = MagicMock()

    sensor = make_sensor(coordinator, sensor_def)

    assert sensor.available is False


async def test_facturacion_sensor_metadata(hass: HomeAssistant) -> None:
    """Invoice sensors expose the expected device/state class and unit."""
    from homeassistant.components.sensor import (
        SensorDeviceClass,
        SensorStateClass,
    )

    from custom_components.edificio_elite.const import FACTURACION_SENSORS

    expected = {
        "importe_total": (SensorDeviceClass.MONETARY, None, "EUR"),
        "importe_acumulado": (
            SensorDeviceClass.MONETARY,
            SensorStateClass.TOTAL,
            "EUR",
        ),
        "importe_fijo": (SensorDeviceClass.MONETARY, None, "EUR"),
        "importe_calor": (SensorDeviceClass.MONETARY, None, "EUR"),
        "importe_frio": (SensorDeviceClass.MONETARY, None, "EUR"),
        "importe_acs": (SensorDeviceClass.MONETARY, None, "EUR"),
        "kwh_calor": (SensorDeviceClass.ENERGY, None, "kWh"),
        "kwh_frio": (SensorDeviceClass.ENERGY, None, "kWh"),
        "kwh_acs": (SensorDeviceClass.ENERGY, None, "kWh"),
        "m3_acs": (SensorDeviceClass.WATER, None, "m³"),
        "periodo_inicio": (SensorDeviceClass.TIMESTAMP, None, None),
        "periodo_fin": (SensorDeviceClass.TIMESTAMP, None, None),
    }

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {}
    coordinator.async_add_listener = MagicMock()

    for sensor_def in FACTURACION_SENSORS:
        sensor = make_sensor(coordinator, sensor_def)
        device_class, state_class, unit = expected[sensor_def["key"]]
        assert sensor.device_class is device_class
        assert sensor.state_class is state_class
        assert sensor.native_unit_of_measurement == unit


async def test_invoice_attributes_when_data_is_none(
    hass: HomeAssistant,
) -> None:
    """The total invoice sensor only exposes the dashboard link without data."""
    from custom_components.edificio_elite.const import FACTURACION_SENSORS

    sensor_def = next(
        s for s in FACTURACION_SENSORS if s["key"] == "importe_total"
    )
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = None
    coordinator.async_add_listener = MagicMock()

    sensor = make_sensor(coordinator, sensor_def)

    assert sensor.extra_state_attributes == {
        "dashboard_url": "https://www.edificioelite.com/"
    }
