# Facturas de vivienda en Home Assistant — Diseño

## Contexto

La integración `edificio_elite` solo consume `GET /consumo-actual` (consumo
instantáneo y contadores) cada 5 minutos. La API del dashboard ya expone las
facturas mensuales de la vivienda en `GET /api/facturas`, autenticada con el
mismo JWT. Este diseño añade esa información a Home Assistant como un device
`Facturación`.

## Objetivos

- Exponer la última factura de la vivienda y el importe acumulado facturado.
- Permitir automatizaciones (factura nueva, importe alto) y aportar coste real
  al Energy Dashboard.
- Sin cambios en la API ni en las credenciales del usuario.

## Fuera de alcance

- Descarga o exposición del PDF de la factura (solo se referencia).
- Una entidad por factura histórica (explosión de entidades).
- Sensores derivados (€/kWh, €/m³, días del periodo, coste diario, variación
  entre facturas). Se podrán añadir en el futuro si hay demanda.
- Cruce factura vs contador y estimación de la factura en curso.

## API

- **Endpoint:** `GET https://api.edificioelite.com/api/facturas`
- **Auth:** `Authorization: Bearer <token>` (mismo login que el resto).
- **Respuesta:** array ordenado por `fecha_factura_inicio` descendente. Cada
  elemento:

```json
{
  "id_factura": "2026-10-01",
  "periodo": "2026-10-01",
  "importe_total": 87.45,
  "importe_fijo": 20.0,
  "kwh_calor": 120,
  "kwh_frio": 8,
  "kwh_acs": 45,
  "m3_acs": 2.4,
  "importe_calor": 42.1,
  "importe_frio": 3.2,
  "importe_variable_acs": 12.4,
  "importe_acs": 22.15,
  "fecha_factura_inicio": "2026-10-01T00:00:00.000Z",
  "fecha_factura_fin": "2026-10-31T00:00:00.000Z",
  "tiene_pdf": true
}
```

- El rol `admin`/`directiva` admite `?piso=`, pero la integración **nunca** lo
  envía: siempre se consulta el piso del usuario autenticado.

## Arquitectura

```
custom_components/edificio_elite/
├── __init__.py          # crea cliente + 2 coordinators
├── api.py               # NUEVO: EliteApiClient (login + get + 401)
├── coordinator.py       # EliteClimateCoordinator (sin cambios funcionales)
├── invoices.py          # NUEVO: EliteInvoicesCoordinator (6 h)
├── const.py             # NUEVO: FACTURACION_SENSORS
├── sensor.py            # añade sensores de facturación
├── binary_sensor.py     # sin cambios
└── config_flow.py       # sin cambios
```

### Cliente compartido (`api.py`)

`EliteApiClient` centraliza autenticación y peticiones:

- `async_login()`: `POST /auth/login` con `{email, password, source:
  "home-assistant"}`. Guarda el token.
- `async_get(path)`: GET con Bearer; ante 401 hace re-login una vez y reintenta.
- Una única instancia por config entry, compartida por ambos coordinators.
  Evita dobles logins y unifica el manejo de 401/rate-limit.

`EliteClimateCoordinator` se refactoriza para usar el cliente (mismo
comportamiento y errores que ahora).

### Coordinators

| Coordinator | Endpoint | Intervalo |
|---|---|---|
| `EliteClimateCoordinator` | `/consumo-actual` | 5 min |
| `EliteInvoicesCoordinator` | `/facturas` | 6 h |

Los coordinadores reciben el `ConfigEntry` y lo pasan a
`DataUpdateCoordinator(config_entry=entry)` de forma explícita (evita el
ContextVar implícito, deprecado en HA y eliminado en 2026.8).

Los objetos compartidos se guardan tipados en `entry.runtime_data`:

```python
@dataclass
class EliteRuntimeData:
    client: EliteApiClient
    climate: EliteClimateCoordinator
    invoices: EliteInvoicesCoordinator
```

`__init__.py`, `sensor.py` y `binary_sensor.py` leen
`entry.runtime_data.{client,climate,invoices}`. Al descargar la entry, HA
elimina `runtime_data` automáticamente.

### Config flow

Sin cambios: email y password. No se añade options flow.

## Entidades — device "Facturación"

`identifiers: {(DOMAIN, "facturacion")}`, `name: "Facturación"`.
`unique_id` con prefijo `facturacion_`.

| key | Nombre | Campo API | device_class | state_class | Unidad |
|---|---|---|---|---|---|
| `importe_total` | Última factura: importe total | `importe_total` | monetary | None | EUR |
| `importe_acumulado` | Importe acumulado facturado | suma `importe_total` | monetary | total | EUR |
| `importe_fijo` | Importe fijo | `importe_fijo` | monetary | None | EUR |
| `importe_calor` | Importe calefacción | `importe_calor` | monetary | None | EUR |
| `importe_frio` | Importe refrigeración | `importe_frio` | monetary | None | EUR |
| `importe_acs` | Importe ACS | `importe_acs` | monetary | None | EUR |
| `kwh_calor` | Energía calefacción (periodo) | `kwh_calor` | energy | None | kWh |
| `kwh_frio` | Energía refrigeración (periodo) | `kwh_frio` | energy | None | kWh |
| `kwh_acs` | Energía ACS (periodo) | `kwh_acs` | energy | None | kWh |
| `m3_acs` | Consumo ACS (periodo) | `m3_acs` | water | None | m³ |
| `periodo_inicio` | Inicio del periodo | `fecha_factura_inicio` | timestamp | — | — |
| `periodo_fin` | Fin del periodo | `fecha_factura_fin` | timestamp | — | — |

Notas:

- En la versión de Home Assistant del proyecto (`DEVICE_CLASS_STATE_CLASSES`),
  `monetary` **solo admite** `total`. Por eso:
  - Los importes por factura (no acumulados) usan `state_class: None`.
  - Solo `importe_acumulado` usa `total`, que es el que alimenta el Energy
    Dashboard.
- `importe_acumulado` usa `state_class: total` (no `total_increasing`) para
  tolerar correcciones retroactivas de facturas sin falsos resets.
- Los kWh/m³ son del periodo (delta), no acumulados: `state_class: None`,
  coherente con los sensores de consumo existentes.
- Las fechas se parsean de ISO 8601; si faltan o son inválidas, el valor es
  `None`.

### Atributos

En `importe_total`:

- `id_factura`
- `periodo` (fecha de inicio, ISO)
- `periodo_fin` (ISO)
- `tiene_pdf`
- `num_facturas`
- `importe_variable_acs`
- `dashboard_url`: `https://www.edificioelite.com/`

No se duplica el histórico en atributos.

## Flujo de datos

1. `async_setup_entry` crea el cliente, el coordinator de clima y el de
   facturas; el de clima hace `async_config_entry_first_refresh()`.
2. Las facturas se refrescan cada 6 h (y una vez al arrancar).
3. Con el array de facturas:
   - `última` = primer elemento (ya viene ordenado desc).
   - `acumulado` = suma de `importe_total` de todos los elementos.
   - Cada sensor toma su campo de `última`.
4. Los sensores de facturación escuchan a `EliteInvoicesCoordinator`; los de
   clima/binary al coordinator de clima.

## Errores y casos límite

- **Lista vacía** (vecino sin facturas): todos los valores `None` y
  `importe_acumulado = 0`, sin marcar la integración como fallida.
- **401** tras re-login: `UpdateFailed` (igual que ahora).
- **Error de red**: se conservan los datos previos; si no hay datos previos,
  `UpdateFailed`.
- **Campos nulos** en una factura: el sensor correspondiente queda `None`; el
  resto se expone igualmente.
- **División por cero**: no aplica en este alcance (sin derivados).

## Testing

Tests nuevos (pytest + `pytest-homeassistant-custom-component`):

- Parseo de `/facturas` → última factura mapeada a cada sensor.
- `importe_acumulado` = suma correcta con varias facturas.
- Lista vacía → `None`/`0`, sin excepción.
- 401 en `/facturas` → re-login y reintento.
- Fallo de red con datos previos → conserva datos.
- Fechas nulas → sensores de periodo `None`.
- Verificación de que `importe_acumulado` y los kWh/m³ tienen el
  `state_class` esperado.

Comandos:

```bash
ruff check custom_components/
pytest tests/ -v
```

## Compatibilidad

- Sin cambios en `manifest.json` (misma versión de integración; release-please
  decide el bump).
- Sin migración de config entries: los datos existentes (`email`, `password`)
  se reutilizan.
- Las entidades existentes no cambian de `unique_id`.
- Documentación: actualizar `README.md` con el nuevo device y las 12 entidades.
