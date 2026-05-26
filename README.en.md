<p align="center">
  <img src="assets/Logotipo.png" alt="Edificio Elite Logo" width="120">
</p>

# Edificio Elite for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/EdificioElite/elite-home-assistant)](https://github.com/EdificioElite/elite-home-assistant/releases)
[![CI](https://github.com/EdificioElite/elite-home-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/EdificioElite/elite-home-assistant/actions/workflows/ci.yml)

Home Assistant integration for residents of Edificio Elite. Monitors aerothermal climate control (heating / cooling) and DHW (hot water) and cold water consumption in real time.

> 🌐 **Languages:** [Español](README.md) · [English](README.en.md)

## Features

- **22 entities (19 sensors + 3 binary sensors)** across three devices: Climatización, DHW and Cold Water
- **Automatic polling** every 5 minutes
- **JWT authentication** with automatic token renewal
- **HACS compatible** — install directly from the HACS store
- **Config flow UI** — no YAML editing required

## Entities

### Climatización (Climate)

| Sensor | Unit | Description |
|---|---|---|
| Última actualización | — | Timestamp of last data fetch |
| Energía calefacción | kWh | Heating energy since last reading |
| Energía refrigeración | kWh | Cooling energy since last reading |
| Energía calefacción (contador) | kWh | Cumulative heating energy |
| Energía refrigeración (contador) | kWh | Cumulative cooling energy |
| Energía calefacción (este mes) | kWh | Heating energy since month start |
| Energía refrigeración (este mes) | kWh | Cooling energy since month start |
| Tª impulsión | °C | Flow temperature |
| Tª retorno | °C | Return temperature |
| Potencia actual | W | Current power consumption |
| Modo | — | Current climate mode (heating / cooling / unknown) |
| Climatización encendida | — | Binary sensor: on when power > 0 |
| Modo calefacción activado | — | Binary sensor: on when mode is heating |
| Modo refrigeración activado | — | Binary sensor: on when mode is cooling |

### Agua Caliente Sanitaria (DHW)

| Sensor | Unit | Description |
|---|---|---|
| Consumo ACS | m³ | Hot water since last reading |
| Energía ACS | kWh | Hot water energy equivalent |
| Energía ACS (contador) | kWh | Cumulative DHW energy (computed: m³ × 46.5) |
| Consumo ACS (contador) | m³ | Cumulative hot water |
| Consumo ACS (este mes) | m³ | Hot water since month start |

### Agua Fría Sanitaria (Cold Water)

| Sensor | Unit | Description |
|---|---|---|
| Consumo AFS | m³ | Cold water since last reading |
| Consumo AFS (contador) | m³ | Cumulative cold water |
| Consumo AFS (este mes) | m³ | Cold water since month start |

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → **⋮** → **Custom repositories**
3. Paste `https://github.com/EdificioElite/elite-home-assistant` and select **Integration**
4. Click **Add**, then find "Edificio Elite" and install it
5. Restart Home Assistant

### Manual

Copy the `custom_components/edificio_elite/` folder into your Home Assistant `custom_components/` directory.

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Edificio Elite"
3. Enter your Edificio Elite email and password  
   _(same credentials you use to log in at [edificioelite.com](https://www.edificioelite.com/))_
4. Click submit — the integration will start polling immediately

## Requirements

- Home Assistant 2024.1 or newer
- A valid Edificio Elite account
