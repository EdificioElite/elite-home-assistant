"""Tests for the Edificio Elite invoices coordinator."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientError
from homeassistant.helpers.update_coordinator import UpdateFailed

INVOICES = [
    {
        "id_factura": "2026-10-01",
        "importe_total": 87.45,
        "importe_fijo": 20.0,
        "kwh_calor": 120,
        "kwh_frio": 8,
        "kwh_acs": 45,
        "m3_acs": 2.4,
        "importe_calor": 42.1,
        "importe_frio": 3.2,
        "importe_variable_acs": 12.4,
        "importe_acs": 22.15,
        "fecha_factura_inicio": "2026-10-01T00:00:00.000Z",
        "fecha_factura_fin": "2026-10-31T00:00:00.000Z",
        "tiene_pdf": True,
    },
    {
        "id_factura": "2026-09-01",
        "importe_total": 100.0,
        "fecha_factura_inicio": "2026-09-01T00:00:00.000Z",
        "fecha_factura_fin": "2026-09-30T00:00:00.000Z",
    },
]


def make_coordinator(hass, return_value=None, side_effect=None):
    """Create an invoices coordinator with a mocked API client."""
    from custom_components.edificio_elite.invoices import EliteInvoicesCoordinator

    client = MagicMock()
    if side_effect is not None:
        client.async_get = AsyncMock(side_effect=side_effect)
    else:
        client.async_get = AsyncMock(return_value=return_value)
    return EliteInvoicesCoordinator(hass, client)


async def test_build_invoice_data_latest_and_sum():
    """Latest invoice is exposed plus the accumulated total."""
    from custom_components.edificio_elite.invoices import build_invoice_data

    data = build_invoice_data(INVOICES)
    assert data["id_factura"] == "2026-10-01"
    assert data["importe_total"] == 87.45
    assert data["importe_acumulado"] == 187.45
    assert data["num_facturas"] == 2


async def test_build_invoice_data_coerces_string_numbers():
    """Numeric columns may arrive as strings; they are coerced to float."""
    from custom_components.edificio_elite.invoices import build_invoice_data

    data = build_invoice_data(
        [{"importe_total": "87.45", "kwh_calor": "120", "m3_acs": "2.4"}]
    )
    assert data["importe_total"] == 87.45
    assert data["kwh_calor"] == 120.0
    assert data["m3_acs"] == 2.4
    assert data["importe_acumulado"] == 87.45


async def test_build_invoice_data_empty():
    """No invoices yields zero accumulation and no latest fields."""
    from custom_components.edificio_elite.invoices import build_invoice_data

    data = build_invoice_data([])
    assert data["importe_acumulado"] == 0
    assert data["num_facturas"] == 0
    assert data.get("importe_total") is None


async def test_refresh_success(hass):
    """A successful refresh builds the invoice data."""
    coord = make_coordinator(hass, return_value=INVOICES)
    result = await coord._async_update_data()
    assert result["id_factura"] == "2026-10-01"
    assert result["importe_acumulado"] == 187.45


async def test_refresh_network_error_keeps_previous(hass):
    """A network error keeps the previous data."""
    coord = make_coordinator(hass, side_effect=ClientError("boom"))
    coord.data = {"importe_total": 50.0}
    result = await coord._async_update_data()
    assert result["importe_total"] == 50.0


async def test_refresh_network_error_without_previous_raises(hass):
    """A network error without previous data raises UpdateFailed."""
    coord = make_coordinator(hass, side_effect=ClientError("boom"))
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()


async def test_refresh_unexpected_response_keeps_previous(hass):
    """A non-list response keeps the previous data."""
    coord = make_coordinator(hass, return_value={"not": "a list"})
    coord.data = {"importe_total": 50.0}
    result = await coord._async_update_data()
    assert result["importe_total"] == 50.0


async def test_to_float_handles_invalid_values():
    """_to_float returns None for invalid, boolean and non-finite values."""
    from custom_components.edificio_elite.invoices import _to_float

    assert _to_float(None) is None
    assert _to_float("") is None
    assert _to_float("abc") is None
    assert _to_float(True) is None
    assert _to_float(float("nan")) is None
    assert _to_float(float("inf")) is None
    assert _to_float(2.5) == 2.5
    assert _to_float(" 3 ") == 3.0


async def test_build_invoice_data_ignores_missing_totals():
    """Missing or invalid totals contribute zero to the accumulation."""
    from custom_components.edificio_elite.invoices import build_invoice_data

    data = build_invoice_data(
        [{"importe_total": None}, {"importe_total": "bad"}, {"importe_total": 10}]
    )
    assert data["importe_acumulado"] == 10.0
    assert data["num_facturas"] == 3


async def test_build_invoice_data_uses_first_element():
    """The API contract is newest-first; the first element is the latest."""
    from custom_components.edificio_elite.invoices import build_invoice_data

    data = build_invoice_data(
        [
            {"id_factura": "new", "fecha_factura_inicio": "2026-12-01"},
            {"id_factura": "old", "fecha_factura_inicio": "2026-01-01"},
        ]
    )
    assert data["id_factura"] == "new"


async def test_refresh_update_failed_propagates(hass):
    """UpdateFailed from the client is not swallowed."""
    coord = make_coordinator(hass, side_effect=UpdateFailed("bad status"))
    coord.data = {"importe_total": 50.0}
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()


async def test_refresh_unexpected_response_without_previous_raises(hass):
    """A non-list response without previous data raises UpdateFailed."""
    coord = make_coordinator(hass, return_value={"not": "a list"})
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()


async def test_invoices_coordinator_uses_config_entry(hass):
    """The invoices coordinator stores the config entry explicitly."""
    from custom_components.edificio_elite.invoices import EliteInvoicesCoordinator

    client = MagicMock()
    client.async_get = AsyncMock(return_value=INVOICES)
    entry = MagicMock()
    coord = EliteInvoicesCoordinator(hass, client, entry)
    assert coord.config_entry is entry
