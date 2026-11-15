"""Tests for the Edificio Elite invoice sensors."""

from datetime import datetime
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

    assert isinstance(sensor.native_value, datetime)
    assert sensor.native_value.month == 10


async def test_invoice_sensor_empty_data(hass: HomeAssistant) -> None:
    """An empty invoice list yields zero accumulated and no failure."""
    from custom_components.edificio_elite.const import FACTURACION_SENSORS

    sensor_def = next(
        s for s in FACTURACION_SENSORS if s["key"] == "importe_acumulado"
    )
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"importe_acumulado": 0, "num_facturas": 0}
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
