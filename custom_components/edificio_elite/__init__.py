"""Edificio Elite integration for Home Assistant."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant

from .api import EliteApiClient
from .const import DOMAIN
from .coordinator import EliteClimateCoordinator
from .invoices import EliteInvoicesCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Edificio Elite from a config entry."""
    client = EliteApiClient(
        hass,
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
    )
    climate = EliteClimateCoordinator(hass, client)
    invoices = EliteInvoicesCoordinator(hass, client)

    await climate.async_config_entry_first_refresh()
    # Invoice failures must not block the integration setup.
    await invoices.async_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "climate": climate,
        "invoices": invoices,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
