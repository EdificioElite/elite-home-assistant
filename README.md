# Elite Climate for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/EdificioElite/elite-home-assistant)](https://github.com/EdificioElite/elite-home-assistant/releases)
[![CI](https://github.com/EdificioElite/elite-home-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/EdificioElite/elite-home-assistant/actions/workflows/ci.yml)

Home Assistant integration for Edificio Elite residents. Monitors aerothermal climate control (heating / cooling) and hot water (ACS) consumption in real time.

## Features

- **16 entities (15 sensors + 1 binary sensor)** across two devices: Climatización and Agua
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
