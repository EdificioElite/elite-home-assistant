"""Tests for Edificio Elite integration setup."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.edificio_elite import PLATFORMS


def make_entry():
    """Create a fake config entry."""
    entry = MagicMock()
    entry.entry_id = "entry-1"
    entry.data = {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "secret"}
    return entry


async def test_setup_entry_wires_coordinators(hass: HomeAssistant) -> None:
    """Setup stores runtime data and forwards the expected platforms."""
    from custom_components.edificio_elite import async_setup_entry

    entry = make_entry()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=None)

    climate = MagicMock()
    climate.async_config_entry_first_refresh = AsyncMock()
    invoices = MagicMock()
    invoices.async_refresh = AsyncMock()

    with patch(
        "custom_components.edificio_elite.EliteApiClient"
    ) as client_cls, patch(
        "custom_components.edificio_elite.EliteClimateCoordinator",
        return_value=climate,
    ) as climate_cls, patch(
        "custom_components.edificio_elite.EliteInvoicesCoordinator",
        return_value=invoices,
    ) as invoices_cls:
        result = await async_setup_entry(hass, entry)

    assert result is True
    client_cls.assert_called_once_with(
        hass, email="test@example.com", password="secret"
    )
    assert entry.runtime_data.client is client_cls.return_value
    assert entry.runtime_data.climate is climate
    assert entry.runtime_data.invoices is invoices
    climate_cls.assert_called_once_with(hass, client_cls.return_value, entry)
    invoices_cls.assert_called_once_with(hass, client_cls.return_value, entry)
    climate.async_config_entry_first_refresh.assert_awaited_once()
    invoices.async_refresh.assert_awaited_once()
    hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
        entry, PLATFORMS
    )


async def test_setup_survives_invoice_refresh_failure(hass: HomeAssistant) -> None:
    """A failed invoice refresh does not block setup."""
    from custom_components.edificio_elite import async_setup_entry

    entry = make_entry()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=None)

    climate = MagicMock()
    climate.async_config_entry_first_refresh = AsyncMock()
    invoices = MagicMock()

    async def failed_refresh():
        invoices.last_update_success = False

    invoices.async_refresh = AsyncMock(side_effect=failed_refresh)

    with patch(
        "custom_components.edificio_elite.EliteApiClient"
    ), patch(
        "custom_components.edificio_elite.EliteClimateCoordinator",
        return_value=climate,
    ), patch(
        "custom_components.edificio_elite.EliteInvoicesCoordinator",
        return_value=invoices,
    ):
        result = await async_setup_entry(hass, entry)

    assert result is True
    assert entry.runtime_data.invoices is invoices
    invoices.async_refresh.assert_awaited_once()
    hass.config_entries.async_forward_entry_setups.assert_awaited_once()


async def test_setup_fails_when_climate_refresh_fails(hass: HomeAssistant) -> None:
    """A climate first-refresh failure blocks setup and platform forwarding."""
    from custom_components.edificio_elite import async_setup_entry

    entry = make_entry()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=None)

    climate = MagicMock()
    climate.async_config_entry_first_refresh = AsyncMock(
        side_effect=ConfigEntryNotReady("no data")
    )

    with patch(
        "custom_components.edificio_elite.EliteApiClient"
    ), patch(
        "custom_components.edificio_elite.EliteClimateCoordinator",
        return_value=climate,
    ), patch(
        "custom_components.edificio_elite.EliteInvoicesCoordinator",
        return_value=MagicMock(),
    ), pytest.raises(ConfigEntryNotReady):
        await async_setup_entry(hass, entry)

    hass.config_entries.async_forward_entry_setups.assert_not_awaited()


async def test_unload_entry_unloads_platforms(hass: HomeAssistant) -> None:
    """Unload delegates to the platform unloader."""
    from custom_components.edificio_elite import async_unload_entry

    entry = make_entry()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    result = await async_unload_entry(hass, entry)

    assert result is True
    hass.config_entries.async_unload_platforms.assert_awaited_once_with(
        entry, PLATFORMS
    )


async def test_sensor_setup_binds_invoice_entities(hass: HomeAssistant) -> None:
    """The sensor platform creates 31 sensors, 12 of them on Facturación."""
    from custom_components.edificio_elite import EliteRuntimeData, sensor
    from custom_components.edificio_elite.const import DEVICE_FACTURACION, DOMAIN

    entry = make_entry()
    entry.runtime_data = EliteRuntimeData(
        client=MagicMock(), climate=MagicMock(), invoices=MagicMock()
    )

    added = []
    await sensor.async_setup_entry(hass, entry, added.extend)

    assert len(added) == 31
    invoice_entities = [
        entity
        for entity in added
        if entity.unique_id.startswith("facturacion_")
    ]
    assert len(invoice_entities) == 12
    assert all(
        entity.coordinator is entry.runtime_data.invoices
        for entity in invoice_entities
    )
    assert all(
        entity.device_info["identifiers"] == {(DOMAIN, DEVICE_FACTURACION)}
        for entity in invoice_entities
    )
    climate_entities = [
        entity
        for entity in added
        if entity.coordinator is entry.runtime_data.climate
    ]
    assert len(climate_entities) == 19


async def test_binary_sensor_setup_uses_climate_coordinator(
    hass: HomeAssistant,
) -> None:
    """The binary sensor platform creates 3 entities bound to climate."""
    from custom_components.edificio_elite import EliteRuntimeData, binary_sensor

    entry = make_entry()
    entry.runtime_data = EliteRuntimeData(
        client=MagicMock(), climate=MagicMock(), invoices=MagicMock()
    )

    added = []
    await binary_sensor.async_setup_entry(hass, entry, added.extend)

    assert len(added) == 3
    assert all(entity.coordinator is entry.runtime_data.climate for entity in added)
