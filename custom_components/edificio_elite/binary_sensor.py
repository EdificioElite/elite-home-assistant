"""Binary sensor platform for Edificio Elite integration."""

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_CLIMATIZACION, DOMAIN
from .coordinator import EliteClimateCoordinator

MODE_BINARY_SENSORS = [
    {
        "key": "modo_calefaccion_activado",
        "name": "Modo calefacción activado",
        "field": "modo_calefaccion_activado",
    },
    {
        "key": "modo_refrigeracion_activado",
        "name": "Modo refrigeración activado",
        "field": "modo_refrigeracion_activado",
    },
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Edificio Elite binary sensors."""
    coordinator: EliteClimateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = [
        EliteClimateRunningSensor(coordinator)
    ]

    for sensor_def in MODE_BINARY_SENSORS:
        entities.append(EliteModeBinarySensor(coordinator, sensor_def))

    async_add_entities(entities)


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


class EliteModeBinarySensor(BinarySensorEntity):
    """Binary sensor for climate mode booleans."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: EliteClimateCoordinator,
        sensor_def: dict[str, Any],
    ) -> None:
        """Initialize the binary sensor."""
        self.coordinator = coordinator
        self._field = sensor_def["field"]
        self._attr_unique_id = f"{DEVICE_CLIMATIZACION}_{sensor_def['key']}"
        self._attr_name = sensor_def["name"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, DEVICE_CLIMATIZACION)},
            name="Climatización",
            manufacturer="Edificio Elite",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the mode is active."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._field)

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
