"""Binary sensor platform for Elite Climate integration."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_CLIMATIZACION, DOMAIN
from .coordinator import EliteClimateCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Elite Climate binary sensors."""
    coordinator: EliteClimateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([EliteClimateRunningSensor(coordinator)])


class EliteClimateRunningSensor(BinarySensorEntity):
    """Binary sensor indicating if the climate system is running."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_unique_id = f"{DEVICE_CLIMATIZACION}_is_running"
    _attr_name = "Climatización encendida"
    # No device_class to show generic On/Off states
    _attr_device_info = DeviceInfo(
        identifiers={(DOMAIN, DEVICE_CLIMATIZACION)},
        name="Climatización",
        manufacturer="Edificio Elite",
    )

    def __init__(self, coordinator: EliteClimateCoordinator) -> None:
        """Initialize the binary sensor."""
        self.coordinator = coordinator

    @property
    def is_on(self) -> bool | None:
        """Return true if the system is running."""
        if self.coordinator.data is None:
            return None
        power_w = self.coordinator.data.get("power_w")
        if power_w is None:
            return None
        try:
            return float(power_w) > 0
        except (ValueError, TypeError):
            return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self) -> None:
        """Update the entity."""
        await self.coordinator.async_request_refresh()
