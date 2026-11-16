"""Integration test with a real Home Assistant instance."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.edificio_elite.const import DOMAIN

CONSUMO_ACTUAL = {
    "timestamp": "2026-05-13T20:00:00.000Z",
    "kwh_calor": 1.234,
    "kwh_frio": 0.567,
    "m3_acs": 0.123,
    "kwh_acs": 5.72,
    "kwh_calor_abs": 12345.678,
    "kwh_frio_abs": 5678.901,
    "m3_acs_abs": 456.789,
    "kwh_calor_mes_inicio": 50.123,
    "kwh_frio_mes_inicio": 20.456,
    "m3_acs_mes_inicio": 3.789,
    "m3_afs": 0.456,
    "m3_afs_abs": 789.012,
    "m3_afs_mes_inicio": 5.678,
    "temp_impulsion": 35.5,
    "temp_retorno": 30.2,
    "power_w": 1200,
    "modo": "calefaccion",
    "modo_calefaccion_activado": True,
    "modo_refrigeracion_activado": False,
}

FACTURAS = [
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
    }
]


@pytest.fixture
def config_entry():
    """Create a config entry for the integration."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "secret"},
        entry_id="elite-entry",
    )


async def test_setup_and_unload_with_real_hass(
    hass: HomeAssistant,
    enable_custom_integrations,
    config_entry: MockConfigEntry,
) -> None:
    """The integration loads its entity platforms and unloads cleanly."""
    config_entry.add_to_hass(hass)

    client = MagicMock()
    client.async_login = AsyncMock()

    async def fake_get(path: str):
        if path == "/consumo-actual":
            return CONSUMO_ACTUAL
        if path == "/facturas":
            return FACTURAS
        raise AssertionError(f"Unexpected path: {path}")

    client.async_get = AsyncMock(side_effect=fake_get)

    with patch(
        "custom_components.edificio_elite.EliteApiClient", return_value=client
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert config_entry.runtime_data.client is client
    assert config_entry.runtime_data.climate.data["power_w"] == 1200
    assert config_entry.runtime_data.invoices.data["importe_total"] == 87.45

    assert len(hass.states.async_entity_ids("sensor")) == 31
    assert len(hass.states.async_entity_ids("binary_sensor")) == 3

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.NOT_LOADED
    assert not hasattr(config_entry, "runtime_data")
    assert all(
        hass.states.get(entity_id).state == "unavailable"
        for entity_id in hass.states.async_entity_ids("sensor")
    )
    assert all(
        hass.states.get(entity_id).state == "unavailable"
        for entity_id in hass.states.async_entity_ids("binary_sensor")
    )
