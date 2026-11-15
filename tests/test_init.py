"""Tests for Edificio Elite integration setup."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from custom_components.edificio_elite.const import DOMAIN


def make_entry():
    """Create a fake config entry."""
    entry = MagicMock()
    entry.entry_id = "entry-1"
    entry.data = {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "secret"}
    return entry


async def test_setup_entry_wires_coordinators(hass: HomeAssistant) -> None:
    """Setup stores the client and both coordinators and forwards platforms."""
    from custom_components.edificio_elite import async_setup_entry

    entry = make_entry()
    hass.data = {}
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
    ), patch(
        "custom_components.edificio_elite.EliteInvoicesCoordinator",
        return_value=invoices,
    ):
        result = await async_setup_entry(hass, entry)

    assert result is True
    stored = hass.data[DOMAIN]["entry-1"]
    assert stored["client"] is client_cls.return_value
    assert stored["climate"] is climate
    assert stored["invoices"] is invoices
    climate.async_config_entry_first_refresh.assert_awaited_once()
    invoices.async_refresh.assert_awaited_once()
    hass.config_entries.async_forward_entry_setups.assert_awaited_once()


async def test_unload_entry_removes_entry_data(hass: HomeAssistant) -> None:
    """Unload removes the config entry data when platforms unload."""
    from custom_components.edificio_elite import async_unload_entry

    entry = make_entry()
    hass.data = {DOMAIN: {"entry-1": {"climate": MagicMock()}}}
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    result = await async_unload_entry(hass, entry)

    assert result is True
    assert "entry-1" not in hass.data[DOMAIN]
