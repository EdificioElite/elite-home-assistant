"""Sensor platform for Elite Climate integration."""

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTemperature, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    AGUA_SENSORS,
    CLIMATIZACION_SENSORS,
    DEVICE_AGUA,
    DEVICE_CLIMATIZACION,
    DOMAIN,
)
from .coordinator import EliteClimateCoordinator

DEVICE_CLASS_MAP: dict[str | None, SensorDeviceClass | None] = {
    "energy": SensorDeviceClass.ENERGY,
    "power": SensorDeviceClass.POWER,
    "temperature": SensorDeviceClass.TEMPERATURE,
    "water": SensorDeviceClass.WATER,
    "timestamp": SensorDeviceClass.TIMESTAMP,
    None: None,
}

STATE_CLASS_MAP: dict[str | None, SensorStateClass | None] = {
    "measurement": SensorStateClass.MEASUREMENT,
    "total": SensorStateClass.TOTAL,
    "total_increasing": SensorStateClass.TOTAL_INCREASING,
    None: None,
}

UNIT_MAP: dict[str | None, str | None] = {
    "kWh": UnitOfEnergy.KILO_WATT_HOUR,
    "W": UnitOfPower.WATT,
    "°C": UnitOfTemperature.CELSIUS,
    "m³": UnitOfVolume.CUBIC_METERS,
    None: None,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Elite Climate sensors."""
    coordinator: EliteClimateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    for sensor_def in CLIMATIZACION_SENSORS:
        entities.append(
            EliteClimateSensor(
                coordinator=coordinator,
                device_id=DEVICE_CLIMATIZACION,
                device_name="Climatización",
                sensor_def=sensor_def,
            )
        )

    for sensor_def in AGUA_SENSORS:
        entities.append(
            EliteClimateSensor(
                coordinator=coordinator,
                device_id=DEVICE_AGUA,
                device_name="Agua",
                sensor_def=sensor_def,
            )
        )

    async_add_entities(entities)


class EliteClimateSensor(SensorEntity):
    """Sensor for a single Elite Climate data point."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: EliteClimateCoordinator,
        device_id: str,
        device_name: str,
        sensor_def: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._sensor_def = sensor_def
        self._attr_unique_id = f"{device_id}_{sensor_def['key']}"
        self._attr_translation_key = sensor_def["key"]
        self._attr_name = sensor_def["name"]
        self._attr_device_class = DEVICE_CLASS_MAP[sensor_def["device_class"]]
        self._attr_state_class = STATE_CLASS_MAP[sensor_def["state_class"]]
        self._attr_native_unit_of_measurement = UNIT_MAP[sensor_def["unit"]]
        if sensor_def.get("icon"):
            self._attr_icon = sensor_def["icon"]

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            manufacturer="Edificio Elite",
        )

    @property
    def native_value(self) -> Any:
        """Return the sensor value from coordinator data."""
        if self.coordinator.data is None:
            return None
        field = self._sensor_def["field"]
        value = self.coordinator.data.get(field)
        if self._sensor_def["device_class"] == "timestamp" and value:
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                return None
        return value

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
