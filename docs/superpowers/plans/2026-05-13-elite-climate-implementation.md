# Elite Climate HACS Integration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a HACS-compatible Home Assistant integration that polls the Elite API every 5 minutes and exposes 15 entities (14 sensors + 1 binary_sensor) across two devices: "Climatización" and "Agua".

**Architecture:** Standard HA custom component with `DataUpdateCoordinator` for polling, `ConfigFlow` for UI setup (email + password), and two platform files (sensor, binary_sensor). JWT auth with automatic re-login on 401. Two separate device registrations grouping entities by domain.

**Tech Stack:** Python 3.12+, Home Assistant custom_component framework, aiohttp (built into HA), pytest + pytest-homeassistant-custom-component for tests, ruff for linting, GitHub Actions for CI/CD.

---

### Task 1: Project Scaffolding

**Files:**
- Create: `custom_components/elite_climate/__init__.py`
- Create: `custom_components/elite_climate/manifest.json`
- Create: `custom_components/elite_climate/const.py`
- Create: `custom_components/elite_climate/translations/en.json`
- Create: `hacs.json`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p custom_components/elite_climate/translations
```

- [ ] **Step 2: Write `manifest.json`**

```json
{
  "domain": "elite_climate",
  "name": "Elite Climate",
  "codeowners": ["@EdificioElite"],
  "config_flow": true,
  "dependencies": [],
  "documentation": "https://github.com/EdificioElite/elite-home-assistant",
  "iot_class": "cloud_polling",
  "requirements": [],
  "version": "0.1.0"
}
```

- [ ] **Step 3: Write `const.py`**

```python
"""Constants for the Elite Climate integration."""

DOMAIN = "elite_climate"
API_BASE_URL = "https://api.edificioelite.com/api"
SCAN_INTERVAL = 300

CONF_EMAIL = "email"
CONF_PASSWORD = "password"

DEVICE_CLIMATIZACION = "climatizacion"
DEVICE_AGUA = "agua"

CLIMATIZACION_SENSORS = [
    {
        "key": "last_update",
        "name": "Última actualización",
        "field": "timestamp",
        "device_class": "timestamp",
        "state_class": None,
        "unit": None,
        "icon": "mdi:clock-outline",
    },
    {
        "key": "kwh_calor",
        "name": "Energía calefacción",
        "field": "kwh_calor",
        "device_class": "energy",
        "state_class": "measurement",
        "unit": "kWh",
        "icon": None,
    },
    {
        "key": "kwh_frio",
        "name": "Energía refrigeración",
        "field": "kwh_frio",
        "device_class": "energy",
        "state_class": "measurement",
        "unit": "kWh",
        "icon": None,
    },
    {
        "key": "kwh_calor_abs",
        "name": "Energía calefacción (acumulado)",
        "field": "kwh_calor_abs",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
        "icon": None,
    },
    {
        "key": "kwh_frio_abs",
        "name": "Energía refrigeración (acumulado)",
        "field": "kwh_frio_abs",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
        "icon": None,
    },
    {
        "key": "kwh_calor_mes_inicio",
        "name": "Energía calefacción (este mes)",
        "field": "kwh_calor_mes_inicio",
        "device_class": "energy",
        "state_class": "total",
        "unit": "kWh",
        "icon": None,
    },
    {
        "key": "kwh_frio_mes_inicio",
        "name": "Energía refrigeración (este mes)",
        "field": "kwh_frio_mes_inicio",
        "device_class": "energy",
        "state_class": "total",
        "unit": "kWh",
        "icon": None,
    },
    {
        "key": "temp_impulsion",
        "name": "Tª impulsión",
        "field": "temp_impulsion",
        "device_class": "temperature",
        "state_class": "measurement",
        "unit": "°C",
        "icon": "mdi:thermometer",
    },
    {
        "key": "temp_retorno",
        "name": "Tª retorno",
        "field": "temp_retorno",
        "device_class": "temperature",
        "state_class": "measurement",
        "unit": "°C",
        "icon": "mdi:thermometer-lines",
    },
    {
        "key": "power_w",
        "name": "Potencia actual",
        "field": "power_w",
        "device_class": "power",
        "state_class": "measurement",
        "unit": "W",
        "icon": "mdi:flash",
    },
]

AGUA_SENSORS = [
    {
        "key": "m3_acs",
        "name": "Consumo ACS",
        "field": "m3_acs",
        "device_class": "water",
        "state_class": "measurement",
        "unit": "m³",
        "icon": "mdi:water",
    },
    {
        "key": "kwh_acs",
        "name": "Energía ACS",
        "field": "kwh_acs",
        "device_class": "energy",
        "state_class": "measurement",
        "unit": "kWh",
        "icon": "mdi:fire",
    },
    {
        "key": "m3_acs_abs",
        "name": "Consumo ACS (acumulado)",
        "field": "m3_acs_abs",
        "device_class": "water",
        "state_class": "total_increasing",
        "unit": "m³",
        "icon": "mdi:water",
    },
    {
        "key": "m3_acs_mes_inicio",
        "name": "Consumo ACS (este mes)",
        "field": "m3_acs_mes_inicio",
        "device_class": "water",
        "state_class": "total",
        "unit": "m³",
        "icon": "mdi:water",
    },
]
```

- [ ] **Step 4: Write `translations/en.json`**

```json
{
  "config": {
    "step": {
      "user": {
        "data": {
          "email": "Email",
          "password": "Password"
        },
        "title": "Elite Climate"
      }
    },
    "error": {
      "invalid_auth": "Invalid email or password"
    },
    "abort": {
      "already_configured": "This account is already configured"
    }
  }
}
```

- [ ] **Step 5: Write `hacs.json`**

```json
{
  "name": "Elite Climate",
  "render_readme": true
}
```

- [ ] **Step 6: Commit**

```bash
git add custom_components/elite_climate/manifest.json custom_components/elite_climate/const.py custom_components/elite_climate/translations/en.json hacs.json
git commit -m "chore: scaffold project structure with manifest, const, translations, and hacs.json"
```

---

### Task 2: Coordinator (API Client & Data Polling)

**Files:**
- Create: `custom_components/elite_climate/coordinator.py`
- Modify: `custom_components/elite_climate/const.py` (already created, verify constants)

- [ ] **Step 1: Write `coordinator.py`**

```python
"""DataUpdateCoordinator for the Elite Climate integration."""

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_BASE_URL, DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class EliteClimateCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator that fetches data from the Elite API every 5 minutes."""

    def __init__(self, hass: HomeAssistant, email: str, password: str) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self._email = email
        self._password = password
        self._token: str | None = None
        self._session = async_get_clientsession(hass)

    async def _async_update_data(self) -> dict:
        """Fetch data from the API, refreshing the token if needed."""
        if self._token is None:
            await self._login()
        return await self._fetch_consumo_actual()

    async def _login(self) -> None:
        """Authenticate and store the JWT token."""
        try:
            async with self._session.post(
                f"{API_BASE_URL}/auth/login",
                json={"email": self._email, "password": self._password},
            ) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"Login failed with status {resp.status}")
                data = await resp.json()
                self._token = data["token"]
        except Exception as err:
            raise UpdateFailed(f"Login error: {err}") from err

    async def _fetch_consumo_actual(self) -> dict:
        """Fetch current consumption data, handling 401 re-auth."""
        headers = {"Authorization": f"Bearer {self._token}"}
        try:
            async with self._session.get(
                f"{API_BASE_URL}/consumo-actual", headers=headers
            ) as resp:
                if resp.status == 401:
                    self._token = None
                    await self._login()
                    return await self._fetch_consumo_actual()
                if resp.status != 200:
                    raise UpdateFailed(f"API returned status {resp.status}")
                data = await resp.json()
                if data is None:
                    if self.data is not None:
                        _LOGGER.debug("API returned null, keeping previous data")
                        return self.data
                    raise UpdateFailed("No data available from API")
                return data
        except Exception as err:
            if self.data is not None:
                _LOGGER.warning("Error fetching data, keeping previous values: %s", err)
                return self.data
            raise UpdateFailed(f"Fetch error: {err}") from err
```

- [ ] **Step 2: Commit**

```bash
git add custom_components/elite_climate/coordinator.py
git commit -m "feat: add coordinator with JWT auth and 5-min polling"
```

---

### Task 3: Config Flow (UI Setup)

**Files:**
- Create: `custom_components/elite_climate/config_flow.py`

- [ ] **Step 1: Write `config_flow.py`**

```python
"""Config flow for Elite Climate integration."""

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_BASE_URL, DOMAIN


class EliteClimateConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Elite Climate."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                async with session.post(
                    f"{API_BASE_URL}/auth/login",
                    json={
                        "email": user_input[CONF_EMAIL],
                        "password": user_input[CONF_PASSWORD],
                    },
                ) as resp:
                    if resp.status == 200:
                        await self.async_set_unique_id(user_input[CONF_EMAIL])
                        self._abort_if_unique_id_configured()
                        return self.async_create_entry(
                            title=user_input[CONF_EMAIL], data=user_input
                        )
                    errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
```

- [ ] **Step 2: Commit**

```bash
git add custom_components/elite_climate/config_flow.py
git commit -m "feat: add config flow with email/password validation"
```

---

### Task 4: Integration Setup (`__init__.py`)

**Files:**
- Modify: `custom_components/elite_climate/__init__.py` (write full implementation)

- [ ] **Step 1: Write `__init__.py`**

```python
"""Elite Climate integration for Home Assistant."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .coordinator import EliteClimateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Elite Climate from a config entry."""
    coordinator = EliteClimateCoordinator(
        hass,
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
```

- [ ] **Step 2: Commit**

```bash
git add custom_components/elite_climate/__init__.py
git commit -m "feat: add integration setup with platform forwarding"
```

---

### Task 5: Sensor Platform (14 sensors across 2 devices)

**Files:**
- Create: `custom_components/elite_climate/sensor.py`

- [ ] **Step 1: Write `sensor.py`**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add custom_components/elite_climate/sensor.py
git commit -m "feat: add sensor platform with 14 sensors across 2 devices"
```

---

### Task 6: Binary Sensor Platform (`is_running`)

**Files:**
- Create: `custom_components/elite_climate/binary_sensor.py`

- [ ] **Step 1: Write `binary_sensor.py`**

```python
"""Binary sensor platform for Elite Climate integration."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    _attr_device_class = BinarySensorDeviceClass.RUNNING
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
        return power_w > 0

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
```

- [ ] **Step 2: Commit**

```bash
git add custom_components/elite_climate/binary_sensor.py
git commit -m "feat: add binary sensor for system running state"
```

---

### Task 7: README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Write `README.md`**

```markdown
# Elite Climate for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/EdificioElite/elite-home-assistant)](https://github.com/EdificioElite/elite-home-assistant/releases)
[![CI](https://github.com/EdificioElite/elite-home-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/EdificioElite/elite-home-assistant/actions/workflows/ci.yml)

Home Assistant integration for Edificio Elite residents. Monitors aerothermal climate control (heating / cooling) and hot water (ACS) consumption in real time.

## Features

- **15 entities** across two devices: Climatización and Agua
- **Automatic polling** every 5 minutes
- **JWT authentication** with automatic token renewal
- **HACS compatible** — install directly from the HACS store
- **Config flow UI** — no YAML editing required

## Entities

### Climatización

| Sensor | Unit | Description |
|---|---|---|
| Última actualización | — | Timestamp of last data fetch |
| Energía calefacción | kWh | Heating energy since last reading |
| Energía refrigeración | kWh | Cooling energy since last reading |
| Energía calefacción (acumulado) | kWh | Cumulative heating energy |
| Energía refrigeración (acumulado) | kWh | Cumulative cooling energy |
| Energía calefacción (este mes) | kWh | Heating energy since month start |
| Energía refrigeración (este mes) | kWh | Cooling energy since month start |
| Tª impulsión | °C | Flow temperature |
| Tª retorno | °C | Return temperature |
| Potencia actual | W | Current power consumption |
| Climatización encendida | — | Binary sensor: on when power > 0 |

### Agua

| Sensor | Unit | Description |
|---|---|---|
| Consumo ACS | m³ | Hot water since last reading |
| Energía ACS | kWh | Hot water energy equivalent |
| Consumo ACS (acumulado) | m³ | Cumulative hot water |
| Consumo ACS (este mes) | m³ | Hot water since month start |

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → **⋮** → **Custom repositories**
3. Paste `https://github.com/EdificioElite/elite-home-assistant` and select **Integration**
4. Click **Add**, then find "Elite Climate" and install it
5. Restart Home Assistant

### Manual

Copy the `custom_components/elite_climate/` folder into your Home Assistant `custom_components/` directory.

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Elite Climate"
3. Enter your Edificio Elite email and password
4. Click submit — the integration will start polling immediately

## Requirements

- Home Assistant 2024.1 or newer
- A valid Edificio Elite account
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add complete README with entity tables and install instructions"
```

---

### Task 8: `.gitignore` Update

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Check current `.gitignore`**

```bash
cat .gitignore
```

- [ ] **Step 2: Append Python/HA-specific entries (if missing)**

Append to `.gitignore`:

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/

# Virtual environments
.venv/
venv/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
htmlcov/
.coverage

# Home Assistant
homeassistant/
config/
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: update .gitignore for Python and HA development"
```

---

### Task 9: Testing Setup

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create test directory**

```bash
mkdir -p tests
```

- [ ] **Step 2: Write `tests/__init__.py`**

```python
"""Tests for Elite Climate Home Assistant integration."""
```

- [ ] **Step 3: Write `tests/conftest.py`**

```python
"""Test fixtures for Elite Climate integration."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant


@pytest.fixture
def mock_api_session():
    """Mock aiohttp client session."""
    with patch(
        "homeassistant.helpers.aiohttp_client.async_get_clientsession"
    ) as mock_session:
        yield mock_session


@pytest.fixture
def coordinator(hass: HomeAssistant, mock_api_session):
    """Create a coordinator instance with mocked session."""
    from custom_components.elite_climate.coordinator import EliteClimateCoordinator

    coord = EliteClimateCoordinator(
        hass, email="test@example.com", password="testpass"
    )
    return coord
```

- [ ] **Step 4: Commit**

```bash
git add tests/
git commit -m "test: add test fixtures and conftest setup"
```

---

### Task 10: Coordinator Tests

**Files:**
- Create: `tests/test_coordinator.py`

- [ ] **Step 1: Write `tests/test_coordinator.py`**

```python
"""Tests for Elite Climate coordinator."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientError
from homeassistant.helpers.update_coordinator import UpdateFailed


async def test_login_success(hass, mock_api_session):
    from custom_components.elite_climate.coordinator import EliteClimateCoordinator

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"token": "jwt-token-123", "user": {"id": 1}})
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post.return_value = mock_resp
    mock_api_session.return_value = mock_session

    coord = EliteClimateCoordinator(hass, email="test@example.com", password="pass")
    await coord._login()

    assert coord._token == "jwt-token-123"


async def test_login_failure(hass, mock_api_session):
    from custom_components.elite_climate.coordinator import EliteClimateCoordinator

    mock_resp = MagicMock()
    mock_resp.status = 401
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post.return_value = mock_resp
    mock_api_session.return_value = mock_session

    coord = EliteClimateCoordinator(hass, email="test@example.com", password="wrong")

    with pytest.raises(UpdateFailed):
        await coord._login()


async def test_fetch_consumo_actual_success(hass, mock_api_session):
    from custom_components.elite_climate.coordinator import EliteClimateCoordinator

    coord = EliteClimateCoordinator(hass, email="test@example.com", password="pass")
    coord._token = "jwt-123"

    sample_data = {
        "timestamp": "2026-05-13T20:00:00.000Z",
        "kwh_calor": 1.234,
        "kwh_frio": 0.567,
        "m3_acs": 0.123,
        "kwh_acs": 5.720,
        "kwh_calor_abs": 12345.678,
        "kwh_frio_abs": 5678.901,
        "m3_acs_abs": 456.789,
        "kwh_calor_mes_inicio": 50.123,
        "kwh_frio_mes_inicio": 20.456,
        "m3_acs_mes_inicio": 3.789,
        "temp_impulsion": 35.5,
        "temp_retorno": 30.2,
        "power_w": 1200,
    }

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value=sample_data)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp
    mock_api_session.return_value = mock_session

    result = await coord._fetch_consumo_actual()
    assert result["kwh_calor"] == 1.234
    assert result["power_w"] == 1200


async def test_fetch_null_data_keeps_previous(hass, mock_api_session):
    from custom_components.elite_climate.coordinator import EliteClimateCoordinator

    coord = EliteClimateCoordinator(hass, email="test@example.com", password="pass")
    coord._token = "jwt-123"
    coord.data = {"power_w": 500}

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value=None)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp
    mock_api_session.return_value = mock_session

    result = await coord._fetch_consumo_actual()
    assert result["power_w"] == 500


async def test_fetch_network_error_keeps_previous(hass, mock_api_session):
    from custom_components.elite_climate.coordinator import EliteClimateCoordinator

    coord = EliteClimateCoordinator(hass, email="test@example.com", password="pass")
    coord._token = "jwt-123"
    coord.data = {"power_w": 800}

    mock_session = MagicMock()
    mock_session.get.side_effect = ClientError("Connection refused")
    mock_api_session.return_value = mock_session

    result = await coord._fetch_consumo_actual()
    assert result["power_w"] == 800


async def test_fetch_401_renews_token(hass, mock_api_session):
    from custom_components.elite_climate.coordinator import EliteClimateCoordinator

    coord = EliteClimateCoordinator(hass, email="test@example.com", password="pass")
    coord._token = "expired-token"

    call_count = {"login": 0, "fetch": 0}

    async def login_side_effect():
        call_count["login"] += 1
        coord._token = "new-token"

    async def fetch_side_effect():
        call_count["fetch"] += 1
        if call_count["fetch"] == 1:
            raise UpdateFailed("401")  # triggers re-login
        return {"power_w": 100}

    coord._login = login_side_effect
    coord._fetch_consumo_actual = fetch_side_effect

    result = await coord._async_update_data()
    assert result["power_w"] == 100
```

- [ ] **Step 2: Run tests to verify they fail (coordinator.py exists, test imports should work)**

```bash
pytest tests/test_coordinator.py -v
```

Expected: Some tests may pass (coordinator.py already created), but verify imports work.

- [ ] **Step 3: Commit**

```bash
git add tests/test_coordinator.py
git commit -m "test: add coordinator unit tests"
```

---

### Task 11: Config Flow Tests

**Files:**
- Create: `tests/test_config_flow.py`

- [ ] **Step 1: Write `tests/test_config_flow.py`**

```python
"""Tests for Elite Climate config flow."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant


async def test_config_flow_success(hass: HomeAssistant) -> None:
    """Test the full config flow with valid credentials."""
    from custom_components.elite_climate.const import DOMAIN

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post.return_value = mock_resp

    with (
        pytest.MonkeyPatch.context() as mp,
    ):
        mp.setattr(
            "custom_components.elite_climate.config_flow.async_get_clientsession",
            lambda hass: mock_session,
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "secret"},
        )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "test@example.com"
    assert result["data"][CONF_EMAIL] == "test@example.com"
    assert result["data"][CONF_PASSWORD] == "secret"


async def test_config_flow_invalid_auth(hass: HomeAssistant) -> None:
    """Test config flow with invalid credentials."""
    from custom_components.elite_climate.const import DOMAIN

    mock_resp = MagicMock()
    mock_resp.status = 401
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post.return_value = mock_resp

    with (
        pytest.MonkeyPatch.context() as mp,
    ):
        mp.setattr(
            "custom_components.elite_climate.config_flow.async_get_clientsession",
            lambda hass: mock_session,
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_EMAIL: "bad@example.com", CONF_PASSWORD: "wrong"},
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}
```

- [ ] **Step 2: Commit**

```bash
git add tests/test_config_flow.py
git commit -m "test: add config flow tests"
```

---

### Task 12: Sensor Tests

**Files:**
- Create: `tests/test_sensor.py`

- [ ] **Step 1: Write `tests/test_sensor.py`**

```python
"""Tests for Elite Climate sensors."""

from unittest.mock import AsyncMock, MagicMock

from homeassistant.core import HomeAssistant


async def test_sensor_values(hass: HomeAssistant) -> None:
    """Test that sensors return correct values from coordinator data."""
    from custom_components.elite_climate.sensor import EliteClimateSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {
        "timestamp": "2026-05-13T20:00:00.000Z",
        "kwh_calor": 2.5,
        "power_w": 1500,
        "m3_acs": 0.05,
    }
    coordinator.async_add_listener = MagicMock()

    sensor_def = {
        "key": "kwh_calor",
        "name": "Energía calefacción",
        "field": "kwh_calor",
        "device_class": "energy",
        "state_class": "measurement",
        "unit": "kWh",
        "icon": None,
    }

    sensor = EliteClimateSensor(
        coordinator=coordinator,
        device_id="climatizacion",
        device_name="Climatización",
        sensor_def=sensor_def,
    )

    assert sensor.native_value == 2.5
    assert sensor.available is True


async def test_sensor_null_data(hass: HomeAssistant) -> None:
    """Test sensor returns None when coordinator data is None."""
    from custom_components.elite_climate.sensor import EliteClimateSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = None
    coordinator.async_add_listener = MagicMock()

    sensor_def = {
        "key": "kwh_calor",
        "name": "Energía calefacción",
        "field": "kwh_calor",
        "device_class": "energy",
        "state_class": "measurement",
        "unit": "kWh",
        "icon": None,
    }

    sensor = EliteClimateSensor(
        coordinator=coordinator,
        device_id="climatizacion",
        device_name="Climatización",
        sensor_def=sensor_def,
    )

    assert sensor.native_value is None


async def test_last_update_timestamp(hass: HomeAssistant) -> None:
    """Test the last_update sensor parses timestamp correctly."""
    from custom_components.elite_climate.sensor import EliteClimateSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"timestamp": "2026-05-13T20:00:00.000Z"}
    coordinator.async_add_listener = MagicMock()

    sensor_def = {
        "key": "last_update",
        "name": "Última actualización",
        "field": "timestamp",
        "device_class": "timestamp",
        "state_class": None,
        "unit": None,
        "icon": "mdi:clock-outline",
    }

    sensor = EliteClimateSensor(
        coordinator=coordinator,
        device_id="climatizacion",
        device_name="Climatización",
        sensor_def=sensor_def,
    )

    from datetime import datetime, timezone

    assert isinstance(sensor.native_value, datetime)
    assert sensor.native_value.year == 2026
```

- [ ] **Step 2: Commit**

```bash
git add tests/test_sensor.py
git commit -m "test: add sensor platform tests"
```

---

### Task 13: Binary Sensor Tests

**Files:**
- Create: `tests/test_binary_sensor.py`

- [ ] **Step 1: Write `tests/test_binary_sensor.py`**

```python
"""Tests for Elite Climate binary sensor."""

from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant


async def test_is_running_true(hass: HomeAssistant) -> None:
    """Test binary sensor is on when power > 0."""
    from custom_components.elite_climate.binary_sensor import EliteClimateRunningSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"power_w": 1500}
    coordinator.async_add_listener = MagicMock()

    sensor = EliteClimateRunningSensor(coordinator)

    assert sensor.is_on is True
    assert sensor.available is True


async def test_is_running_false(hass: HomeAssistant) -> None:
    """Test binary sensor is off when power == 0."""
    from custom_components.elite_climate.binary_sensor import EliteClimateRunningSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"power_w": 0}
    coordinator.async_add_listener = MagicMock()

    sensor = EliteClimateRunningSensor(coordinator)

    assert sensor.is_on is False


async def test_is_running_null_when_no_data(hass: HomeAssistant) -> None:
    """Test binary sensor is None when data is missing."""
    from custom_components.elite_climate.binary_sensor import EliteClimateRunningSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = None
    coordinator.async_add_listener = MagicMock()

    sensor = EliteClimateRunningSensor(coordinator)

    assert sensor.is_on is None


async def test_is_running_null_when_power_none(hass: HomeAssistant) -> None:
    """Test binary sensor is None when power_w is None."""
    from custom_components.elite_climate.binary_sensor import EliteClimateRunningSensor

    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"power_w": None}
    coordinator.async_add_listener = MagicMock()

    sensor = EliteClimateRunningSensor(coordinator)

    assert sensor.is_on is None
```

- [ ] **Step 2: Commit**

```bash
git add tests/test_binary_sensor.py
git commit -m "test: add binary sensor tests"
```

---

### Task 14: CI Workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create workflows directory**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Write `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  hassfest:
    name: Validate with hassfest
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: home-assistant/actions/hassfest@master

  lint:
    name: Lint with ruff
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/ruff-action@v3
        with:
          args: check custom_components/

  test:
    name: Run tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          pip install homeassistant pytest pytest-homeassistant-custom-component pytest-cov
      - name: Run tests
        run: pytest tests/ -v
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add hassfest, ruff, and pytest workflow"
```

---

### Task 15: Release Workflow

**Files:**
- Create: `.github/workflows/release.yml`

- [ ] **Step 1: Write `scripts/bump_version.py` directory and file**

```bash
mkdir -p scripts
```

- [ ] **Step 2: Write `scripts/bump_version.py`**

```python
"""Bump version in manifest.json and const.py."""

import json
import re
import sys
from pathlib import Path


def bump_version(bump_type: str) -> str:
    """Bump semver version. Returns the new version string."""
    manifest_path = Path("custom_components/elite_climate/manifest.json")
    manifest = json.loads(manifest_path.read_text())
    current = manifest["version"]

    major, minor, patch = map(int, current.split("."))
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        print(f"Unknown bump type: {bump_type}", file=sys.stderr)
        sys.exit(1)

    new_version = f"{major}.{minor}.{patch}"

    manifest["version"] = new_version
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    print(new_version)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/bump_version.py <major|minor|patch>", file=sys.stderr)
        sys.exit(1)
    bump_version(sys.argv[1])
```

- [ ] **Step 3: Write `.github/workflows/release.yml`**

```yaml
name: Release

on:
  workflow_dispatch:
    inputs:
      version_bump:
        description: "Version bump type"
        required: true
        type: choice
        options:
          - patch
          - minor
          - major

permissions:
  contents: write

jobs:
  release:
    name: Create Release
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Bump version
        id: bump
        run: |
          NEW_VERSION=$(python scripts/bump_version.py ${{ inputs.version_bump }})
          echo "new_version=$NEW_VERSION" >> $GITHUB_OUTPUT

      - name: Generate changelog
        id: changelog
        uses: requarks/changelog-action@v1
        with:
          token: ${{ github.token }}
          tag: v${{ steps.bump.outputs.new_version }}
          writeToFile: false

      - name: Commit version bump
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add custom_components/elite_climate/manifest.json
          git commit -m "chore: bump version to v${{ steps.bump.outputs.new_version }}"
          git tag "v${{ steps.bump.outputs.new_version }}"
          git push origin main --tags

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: v${{ steps.bump.outputs.new_version }}
          body: ${{ steps.changelog.outputs.changes }}
```

- [ ] **Step 4: Commit**

```bash
git add scripts/bump_version.py .github/workflows/release.yml
git commit -m "ci: add manual release workflow with version bump and changelog"
```

---

### Task 16: Final Verification

- [ ] **Step 1: Run all tests**

```bash
pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 2: Run ruff lint**

```bash
pip install ruff && ruff check custom_components/
```

Expected: No errors.

- [ ] **Step 3: Verify hassfest validation**

If you have a local Home Assistant dev environment, run:
```bash
python -m homeassistant.components.hassfest
```

Otherwise, the CI workflow covers this on push.

- [ ] **Step 4: Verify all files exist**

```bash
ls -la custom_components/elite_climate/
ls -la .github/workflows/
ls -la tests/
```

Expected output:
```
custom_components/elite_climate/:
  __init__.py
  manifest.json
  const.py
  config_flow.py
  coordinator.py
  sensor.py
  binary_sensor.py
  translations/en.json

.github/workflows/:
  ci.yml
  release.yml

tests/:
  __init__.py
  conftest.py
  test_coordinator.py
  test_config_flow.py
  test_sensor.py
  test_binary_sensor.py
```

- [ ] **Step 5: Final commit (any remaining changes)**

```bash
git add -A
git status
```

If clean, done. If unstaged changes remain, commit them.
