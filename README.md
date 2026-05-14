<p align="center">
  <img src="assets/Logotipo.png" alt="Elite Climate Logo" width="120">
</p>

# Elite Climate para Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/EdificioElite/elite-home-assistant)](https://github.com/EdificioElite/elite-home-assistant/releases)
[![CI](https://github.com/EdificioElite/elite-home-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/EdificioElite/elite-home-assistant/actions/workflows/ci.yml)

Integración de Home Assistant para residentes de Edificio Elite. Monitoriza en tiempo real el control climático aerotérmico (calefacción / refrigeración) y el consumo de agua caliente sanitaria (ACS).

> 🌐 **Idiomas:** [Español](README.md) · [English](README.en.md)

## Características

- **16 entidades (15 sensores + 1 sensor binario)** repartidos en dos dispositivos: Climatización y Agua
- **Actualización automática** cada 5 minutos
- **Autenticación JWT** con renovación automática de token
- **Compatible con HACS** — instálalo directamente desde la tienda de HACS
- **Config flow UI** — no es necesario editar YAML

## Entidades

### Climatización

| Sensor | Unidad | Descripción |
|---|---|---|
| Última actualización | — | Marca de tiempo de la última actualización |
| Energía calefacción | kWh | Energía de calefacción desde la última lectura |
| Energía refrigeración | kWh | Energía de refrigeración desde la última lectura |
| Energía calefacción (contador) | kWh | Energía de calefacción acumulada |
| Energía refrigeración (contador) | kWh | Energía de refrigeración acumulada |
| Energía calefacción (este mes) | kWh | Energía de calefacción desde el inicio del mes |
| Energía refrigeración (este mes) | kWh | Energía de refrigeración desde el inicio del mes |
| Tª impulsión | °C | Temperatura de impulsión |
| Tª retorno | °C | Temperatura de retorno |
| Potencia actual | W | Consumo de potencia actual |
| Climatización encendida | — | Sensor binario: activo cuando la potencia > 0 |

### Agua

| Sensor | Unidad | Descripción |
|---|---|---|
| Consumo ACS | m³ | Agua caliente desde la última lectura |
| Energía ACS | kWh | Equivalente energético del agua caliente |
| Consumo ACS (contador) | m³ | Agua caliente acumulada |
| Consumo ACS (este mes) | m³ | Agua caliente desde el inicio del mes |

## Instalación

### Mediante HACS (recomendado)

1. Abre HACS en Home Assistant
2. Ve a **Integraciones** → **⋮** → **Repositorios personalizados**
3. Pega `https://github.com/EdificioElite/elite-home-assistant` y selecciona **Integration**
4. Haz clic en **Añadir**, luego busca "Elite Climate" e instálala
5. Reinicia Home Assistant

### Manual

Copia la carpeta `custom_components/elite_climate/` en el directorio `custom_components/` de tu Home Assistant.

## Configuración

1. Ve a **Configuración** → **Dispositivos y servicios** → **Añadir integración**
2. Busca "Elite Climate"
3. Introduce tu email y contraseña de Edificio Elite  
   _(las mismas credenciales que usas para iniciar sesión en [edificioelite.com](https://www.edificioelite.com/))_
4. Haz clic en enviar — la integración comenzará a consultar los datos inmediatamente

## Requisitos

- Home Assistant 2024.1 o superior
- Una cuenta válida de Edificio Elite
