# Elite Climate — Home Assistant HACS Integration

## Overview

Integracion HACS para Home Assistant que consulta la API del Edificio Elite cada 5 minutos y expone los datos de climatizacion y agua como entidades. Disenada para cualquier vecino del edificio con credenciales validas.

## API

- **URL:** `https://api.edificioelite.com/api` (produccion, hardcodeada)
- **Auth:** JWT via `POST /auth/login` con `{email, password}` → `{token, user}`
- **Datos:** `GET /consumo-actual` con header `Authorization: Bearer <token>`

### Response de `/consumo-actual`

```json
{
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
  "power_w": 1200
}
```

## Arquitectura

```
custom_components/elite_climate/
├── __init__.py
├── manifest.json
├── config_flow.py
├── const.py
├── coordinator.py
├── sensor.py
├── binary_sensor.py
└── translations/
    └── en.json
```

### Data Flow

1. **Setup** — `POST /auth/login` con email/password configurados → guarda token JWT
2. **Polling cada 5 minutos** — `GET /consumo-actual` con `Authorization: Bearer <token>`
3. **Token expiry** — si 401, re-login automatico y reintenta la peticion
4. **Update** — el `DataUpdateCoordinator` actualiza todas las entidades con los valores del JSON

### Config Flow (UI)

Solo dos campos:
- **Email** (string, required)
- **Password** (string, required, password field)

## Entidades

### Device: "Climatizacion"

| Entity ID | Tipo | Unidad | Campo API | device_class | state_class |
|---|---|---|---|---|---|
| `last_update` | sensor | - | `timestamp` | timestamp | - |
| `kwh_calor` | sensor | kWh | `kwh_calor` | energy | measurement |
| `kwh_frio` | sensor | kWh | `kwh_frio` | energy | measurement |
| `kwh_calor_abs` | sensor | kWh | `kwh_calor_abs` | energy | total_increasing |
| `kwh_frio_abs` | sensor | kWh | `kwh_frio_abs` | energy | total_increasing |
| `kwh_calor_mes_inicio` | sensor | kWh | `kwh_calor_mes_inicio` | energy | total |
| `kwh_frio_mes_inicio` | sensor | kWh | `kwh_frio_mes_inicio` | energy | total |
| `temp_impulsion` | sensor | °C | `temp_impulsion` | temperature | measurement |
| `temp_retorno` | sensor | °C | `temp_retorno` | temperature | measurement |
| `power_w` | sensor | W | `power_w` | power | measurement |
| `is_running` | binary_sensor | - | `power_w > 0` | running | - |

### Device: "Agua"

| Entity ID | Tipo | Unidad | Campo API | device_class | state_class |
|---|---|---|---|---|---|
| `m3_acs` | sensor | m³ | `m3_acs` | water | measurement |
| `kwh_acs` | sensor | kWh | `kwh_acs` | energy | measurement |
| `m3_acs_abs` | sensor | m³ | `m3_acs_abs` | water | total_increasing |
| `m3_acs_mes_inicio` | sensor | m³ | `m3_acs_mes_inicio` | water | total |

Futuro: cuando exista contador de agua fria, se anaden entidades al device "Agua" con sufijo `_agua_fria`.

## HACS

- Repositorio: `github.com/EdificioElite/elite-home-assistant`
- Incluir `hacs.json` con `"name": "Elite Climate"` y `"render_readme": true`
- README con estilo visual (badges, logo si aplica, instrucciones de instalacion, captura del config flow, tabla de entidades). Tomar como referencia integraciones populares de HACS con muchas estrellas.

## Versionado y CI/CD

### Semver

- Version inicial: `0.1.0`
- `0.x.y` mientras este en desarrollo, `1.0.0` cuando sea funcional y estable
- Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`) en espanol

### Ramas

Una sola rama `main`. PRs de features se mergean directamente a `main`.

Flujo: `feat/*` → PR → `main`. Para release: ejecutar manualmente el workflow.

### GitHub Actions Workflows

**CI (`ci.yml`)** — en cada push y PR a `main`:
- `hassfest`: validar `manifest.json`, `strings.json`, etc.
- Lint: `ruff check custom_components/`
- Test: `pytest` (si hay tests)

**Release (`release.yml`)** — `workflow_dispatch` manual con input desplegable:
- **Input:** `version_bump` → `patch` | `minor` | `major`
- Genera changelog de conventional commits desde el ultimo tag
- Bump version en `manifest.json` y `const.py`
- Crea tag `vX.Y.Z`
- Crea GitHub Release con el changelog
- HACS detecta automaticamente la nueva version via el tag

## Edge Cases / Error Handling

- **API caida:** ultimo valor conocido retenido, coordinator intenta de nuevo en 5 min
- **401 Unauthorized:** re-login automatico, reintenta la peticion
- **Response null (sin datos):** no actualizar entidades, mantener valores previos
- **Timeout / network error:** loggear warning, reintentar en el siguiente ciclo
- **Credenciales invalidas en config flow:** mostrar error en la UI, no permitir continuar
