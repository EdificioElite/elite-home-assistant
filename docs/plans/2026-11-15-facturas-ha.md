# Facturas en Home Assistant — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Exponer las facturas mensuales de la vivienda en Home Assistant como un device `Facturación` con 12 sensores, sin tocar la API.

**Architecture:** Se extrae un `EliteApiClient` compartido (login + GET con re-login en 401). `EliteClimateCoordinator` y el nuevo `EliteInvoicesCoordinator` (refresco cada 6 h) lo reutilizan. `hass.data[DOMAIN][entry_id]` pasa a un dict con `client`, `climate` e `invoices`.

**Tech Stack:** Python 3.14, Home Assistant custom component, aiohttp, pytest, pytest-homeassistant-custom-component, ruff.

**Spec:** `docs/specs/2026-11-15-facturas-ha-design.md`

---

## Task 0: Rama de trabajo

- [ ] **Step 1: Crear rama desde main**

```bash
git switch main
git pull --ff-only
git switch -c feat/facturas-home-assistant
```

---

## Task 1: Cliente API compartido

**Files:**
- Create: `custom_components/edificio_elite/api.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Escribir los tests que fallan**

Create `tests/test_api.py`:

```python
"""Tests for the Edificio Elite shared API client."""

from unittest.mock import MagicMock

import pytest
from aiohttp import ClientError
from homeassistant.helpers.update_coordinator import UpdateFailed


class MockResponse:
    """Mock aiohttp response with async context manager protocol."""

    def __init__(self, status, json_data=None, text_data=None):
        self.status = status
        self._json_data = json_data
        self._text_data = text_data

    async def json(self):
        return self._json_data

    async def text(self):
        return self._text_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


async def test_login_success(hass, mock_api_session):
    """Login stores the token and identifies Home Assistant as source."""
    from custom_components.edificio_elite.api import EliteApiClient

    mock_session = MagicMock()
    mock_session.post.return_value = MockResponse(200, {"token": "jwt-123"})
    mock_api_session.return_value = mock_session

    client = EliteApiClient(hass, email="test@example.com", password="pass")
    await client.async_login()

    assert client.token == "jwt-123"
    _, kwargs = mock_session.post.call_args
    assert kwargs["json"]["source"] == "home-assistant"


async def test_login_failure_raises(hass, mock_api_session):
    """A rejected login raises UpdateFailed."""
    from custom_components.edificio_elite.api import EliteApiClient

    mock_session = MagicMock()
    mock_session.post.return_value = MockResponse(401, None, "bad credentials")
    mock_api_session.return_value = mock_session

    client = EliteApiClient(hass, email="test@example.com", password="wrong")
    with pytest.raises(UpdateFailed):
        await client.async_login()


async def test_get_returns_json(hass, mock_api_session):
    """GET returns the decoded JSON body."""
    from custom_components.edificio_elite.api import EliteApiClient

    mock_session = MagicMock()
    mock_session.get.return_value = MockResponse(200, {"kwh_calor": 1.5})
    mock_api_session.return_value = mock_session

    client = EliteApiClient(hass, email="test@example.com", password="pass")
    client._token = "jwt-123"

    result = await client.async_get("/consumo-actual")
    assert result["kwh_calor"] == 1.5


async def test_get_401_relogins_and_retries(hass, mock_api_session):
    """A 401 triggers one re-login and one retry."""
    from custom_components.edificio_elite.api import EliteApiClient

    mock_session = MagicMock()
    mock_session.post.return_value = MockResponse(200, {"token": "new-token"})
    mock_session.get.side_effect = [
        MockResponse(401, None, "expired"),
        MockResponse(200, {"power_w": 100}),
    ]
    mock_api_session.return_value = mock_session

    client = EliteApiClient(hass, email="test@example.com", password="pass")
    client._token = "expired"

    result = await client.async_get("/consumo-actual")
    assert result["power_w"] == 100
    assert client.token == "new-token"


async def test_get_401_after_retry_raises(hass, mock_api_session):
    """A second 401 is not retried again."""
    from custom_components.edificio_elite.api import EliteApiClient

    mock_session = MagicMock()
    mock_session.post.return_value = MockResponse(200, {"token": "new-token"})
    mock_session.get.return_value = MockResponse(401, None, "nope")
    mock_api_session.return_value = mock_session

    client = EliteApiClient(hass, email="test@example.com", password="pass")
    client._token = "expired"

    with pytest.raises(UpdateFailed):
        await client.async_get("/consumo-actual")


async def test_get_network_error_propagates(hass, mock_api_session):
    """Network errors propagate so coordinators can keep previous data."""
    from custom_components.edificio_elite.api import EliteApiClient

    mock_session = MagicMock()
    mock_session.get.side_effect = ClientError("boom")
    mock_api_session.return_value = mock_session

    client = EliteApiClient(hass, email="test@example.com", password="pass")
    client._token = "jwt-123"

    with pytest.raises(ClientError):
        await client.async_get("/consumo-actual")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'custom_components.edificio_elite.api'`

- [ ] **Step 3: Implement the client**

Create `custom_components/edificio_elite/api.py`:

```python
"""Shared API client for the Edificio Elite integration."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)


class EliteApiClient:
    """Authenticated client shared by all coordinators of one config entry."""

    def __init__(self, hass: HomeAssistant, email: str, password: str) -> None:
        """Initialize the client with the configured credentials."""
        self._session = async_get_clientsession(hass)
        self._email = email
        self._password = password
        self._token: str | None = None

    @property
    def token(self) -> str | None:
        """Return the current JWT token, if any."""
        return self._token

    async def async_login(self) -> None:
        """Authenticate and store the JWT token."""
        try:
            async with self._session.post(
                f"{API_BASE_URL}/auth/login",
                json={
                    "email": self._email,
                    "password": self._password,
                    "source": "home-assistant",
                },
            ) as resp:
                if resp.status == 429:
                    text = await resp.text()
                    _LOGGER.warning("Login rate-limited by API: %s", text)
                    raise UpdateFailed(
                        "Login temporarily blocked (rate limit), will retry"
                    )
                if resp.status in (401, 403):
                    text = await resp.text()
                    _LOGGER.error(
                        "Login rejected (status %s): %s", resp.status, text
                    )
                    raise UpdateFailed(
                        f"Login failed with status {resp.status}: {text}"
                    )
                if resp.status != 200:
                    text = await resp.text()
                    _LOGGER.error(
                        "Login failed with unexpected status %s: %s",
                        resp.status,
                        text,
                    )
                    raise UpdateFailed(
                        f"Login failed with status {resp.status}: {text}"
                    )
                data = await resp.json()
                self._token = data["token"]
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Login error: {err}") from err

    async def async_get(self, path: str, _retried: bool = False) -> Any:
        """Perform an authenticated GET, re-logging in once on 401."""
        if self._token is None:
            await self.async_login()

        headers = {"Authorization": f"Bearer {self._token}"}
        async with self._session.get(
            f"{API_BASE_URL}{path}", headers=headers
        ) as resp:
            if resp.status == 401:
                if _retried:
                    raise UpdateFailed("Authentication failed after re-login")
                self._token = None
                await self.async_login()
                return await self.async_get(path, _retried=True)
            if resp.status != 200:
                raise UpdateFailed(f"API returned status {resp.status}")
            return await resp.json()
```

- [ ] **Step 4: Update the shared session fixture**

Modify `tests/conftest.py`: replace the `mock_api_session` and `coordinator` fixtures with:

```python
@pytest.fixture
def mock_api_session():
    """Mock aiohttp client session used by the API client."""
    with patch(
        "custom_components.edificio_elite.api.async_get_clientsession"
    ) as mock_session:
        yield mock_session


@pytest.fixture
def api_client(hass, mock_api_session):
    """Create an API client with a mocked session."""
    from custom_components.edificio_elite.api import EliteApiClient

    return EliteApiClient(hass, email="test@example.com", password="testpass")


@pytest.fixture
def coordinator(hass, api_client):
    """Create a climate coordinator backed by the mocked client."""
    from custom_components.edificio_elite.coordinator import EliteClimateCoordinator

    return EliteClimateCoordinator(hass, api_client)
```

- [ ] **Step 5: Run the new tests to verify they pass**

Run: `pytest tests/test_api.py -v`
Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
git add custom_components/edificio_elite/api.py tests/test_api.py tests/conftest.py
git commit -m "feat: add shared Elite API client"
```

---

## Task 2: Refactorizar el coordinator de clima para usar el cliente

**Files:**
- Modify: `custom_components/edificio_elite/coordinator.py`
- Modify: `tests/test_coordinator.py`

- [ ] **Step 1: Reescribir los tests del coordinator**

Replace `tests/test_coordinator.py` with:

```python
"""Tests for Edificio Elite climate coordinator."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientError
from homeassistant.helpers.update_coordinator import UpdateFailed

SAMPLE_DATA = {
    "timestamp": "2026-05-13T20:00:00.000Z",
    "kwh_calor": 1.234,
    "kwh_frio": 0.567,
    "m3_acs": 0.123,
    "power_w": 1200,
    "modo": "calefaccion",
}


def make_coordinator(hass, return_value=None, side_effect=None):
    """Create a climate coordinator with a mocked API client."""
    from custom_components.edificio_elite.coordinator import EliteClimateCoordinator

    client = MagicMock()
    if side_effect is not None:
        client.async_get = AsyncMock(side_effect=side_effect)
    else:
        client.async_get = AsyncMock(return_value=return_value)
    return EliteClimateCoordinator(hass, client)


async def test_fetch_consumo_actual_success(hass):
    """The coordinator returns the API payload."""
    coord = make_coordinator(hass, return_value=SAMPLE_DATA)
    result = await coord._fetch_consumo_actual()
    assert result["kwh_calor"] == 1.234
    assert result["power_w"] == 1200


async def test_fetch_null_data_keeps_previous(hass):
    """A null payload keeps the previous data."""
    coord = make_coordinator(hass, return_value=None)
    coord.data = {"power_w": 500}
    result = await coord._fetch_consumo_actual()
    assert result["power_w"] == 500


async def test_fetch_null_data_without_previous_raises(hass):
    """A null payload without previous data raises UpdateFailed."""
    coord = make_coordinator(hass, return_value=None)
    with pytest.raises(UpdateFailed):
        await coord._fetch_consumo_actual()


async def test_fetch_network_error_keeps_previous(hass):
    """A network error keeps the previous data."""
    coord = make_coordinator(hass, side_effect=ClientError("Connection refused"))
    coord.data = {"power_w": 800}
    result = await coord._fetch_consumo_actual()
    assert result["power_w"] == 800


async def test_fetch_update_failed_propagates(hass):
    """UpdateFailed from the client is not swallowed."""
    coord = make_coordinator(hass, side_effect=UpdateFailed("bad status"))
    coord.data = {"power_w": 800}
    with pytest.raises(UpdateFailed):
        await coord._fetch_consumo_actual()


async def test_update_data_calls_fetch(hass):
    """_async_update_data delegates to _fetch_consumo_actual."""
    coord = make_coordinator(hass, return_value=SAMPLE_DATA)
    result = await coord._async_update_data()
    assert result["power_w"] == 1200
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_coordinator.py -v`
Expected: FAIL with `TypeError` because `EliteClimateCoordinator` still expects `email`/`password`.

- [ ] **Step 3: Implement the refactor**

Replace `custom_components/edificio_elite/coordinator.py` with:

```python
"""DataUpdateCoordinator for the Edificio Elite integration."""

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EliteApiClient
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class EliteClimateCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator that fetches climate and water data every 5 minutes."""

    def __init__(self, hass: HomeAssistant, client: EliteApiClient) -> None:
        """Initialize the coordinator with the shared API client."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        """Fetch current consumption data from the API."""
        return await self._fetch_consumo_actual()

    async def _fetch_consumo_actual(self) -> dict:
        """Fetch current consumption, keeping previous data on soft errors."""
        try:
            data = await self.client.async_get("/consumo-actual")
        except UpdateFailed:
            raise
        except Exception as err:
            if self.data is not None:
                _LOGGER.warning(
                    "Error fetching data, keeping previous values: %s", err
                )
                return self.data
            raise UpdateFailed(f"Fetch error: {err}") from err

        if data is None:
            if self.data is not None:
                _LOGGER.debug("API returned null, keeping previous data")
                return self.data
            raise UpdateFailed("No data available from API")
        return data
```

- [ ] **Step 4: Run the tests**

Run: `pytest tests/test_coordinator.py tests/test_api.py -v`
Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add custom_components/edificio_elite/coordinator.py tests/test_coordinator.py
git commit -m "refactor: use shared API client in climate coordinator"
```

---

## Task 3: Constantes y definiciones de los sensores de facturación

**Files:**
- Modify: `custom_components/edificio_elite/const.py`

- [ ] **Step 1: Añadir constantes y definiciones**

Append to `custom_components/edificio_elite/const.py`:

```python
DEVICE_FACTURACION = "facturacion"
INVOICE_SCAN_INTERVAL = 6 * 60 * 60
DASHBOARD_URL = "https://www.edificioelite.com/"

FACTURACION_SENSORS = [
    {
        "key": "importe_total",
        "name": "Última factura: importe total",
        "field": "importe_total",
        "device_class": "monetary",
        "state_class": None,
        "unit": "EUR",
        "icon": "mdi:receipt-text",
        "invoice_attributes": True,
    },
    {
        "key": "importe_acumulado",
        "name": "Importe acumulado facturado",
        "field": "importe_acumulado",
        "device_class": "monetary",
        "state_class": "total",
        "unit": "EUR",
        "icon": "mdi:cash-multiple",
    },
    {
        "key": "importe_fijo",
        "name": "Importe fijo",
        "field": "importe_fijo",
        "device_class": "monetary",
        "state_class": None,
        "unit": "EUR",
        "icon": "mdi:cash",
    },
    {
        "key": "importe_calor",
        "name": "Importe calefacción",
        "field": "importe_calor",
        "device_class": "monetary",
        "state_class": None,
        "unit": "EUR",
        "icon": "mdi:cash",
    },
    {
        "key": "importe_frio",
        "name": "Importe refrigeración",
        "field": "importe_frio",
        "device_class": "monetary",
        "state_class": None,
        "unit": "EUR",
        "icon": "mdi:cash",
    },
    {
        "key": "importe_acs",
        "name": "Importe ACS",
        "field": "importe_acs",
        "device_class": "monetary",
        "state_class": None,
        "unit": "EUR",
        "icon": "mdi:cash",
    },
    {
        "key": "kwh_calor",
        "name": "Energía calefacción (periodo)",
        "field": "kwh_calor",
        "device_class": "energy",
        "state_class": None,
        "unit": "kWh",
        "icon": None,
    },
    {
        "key": "kwh_frio",
        "name": "Energía refrigeración (periodo)",
        "field": "kwh_frio",
        "device_class": "energy",
        "state_class": None,
        "unit": "kWh",
        "icon": None,
    },
    {
        "key": "kwh_acs",
        "name": "Energía ACS (periodo)",
        "field": "kwh_acs",
        "device_class": "energy",
        "state_class": None,
        "unit": "kWh",
        "icon": None,
    },
    {
        "key": "m3_acs",
        "name": "Consumo ACS (periodo)",
        "field": "m3_acs",
        "device_class": "water",
        "state_class": None,
        "unit": "m³",
        "icon": "mdi:water",
    },
    {
        "key": "periodo_inicio",
        "name": "Inicio del periodo",
        "field": "fecha_factura_inicio",
        "device_class": "timestamp",
        "state_class": None,
        "unit": None,
        "icon": "mdi:calendar-start",
    },
    {
        "key": "periodo_fin",
        "name": "Fin del periodo",
        "field": "fecha_factura_fin",
        "device_class": "timestamp",
        "state_class": None,
        "unit": None,
        "icon": "mdi:calendar-end",
    },
]
```

- [ ] **Step 2: Sanity check (sin tests aún)**

Run: `ruff check custom_components/edificio_elite/const.py`
Expected: `All checks passed!`

- [ ] **Step 3: Commit**

```bash
git add custom_components/edificio_elite/const.py
git commit -m "feat: add invoice sensor definitions"
```

---

## Task 4: Coordinator de facturas

**Files:**
- Create: `custom_components/edificio_elite/invoices.py`
- Test: `tests/test_invoices.py`

- [ ] **Step 1: Escribir los tests que fallan**

Create `tests/test_invoices.py`:

```python
"""Tests for the Edificio Elite invoices coordinator."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientError
from homeassistant.helpers.update_coordinator import UpdateFailed

INVOICES = [
    {
        "id_factura": "2026-10-01",
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
        "tiene_pdf": True,
    },
    {
        "id_factura": "2026-09-01",
        "importe_total": 100.0,
        "fecha_factura_inicio": "2026-09-01T00:00:00.000Z",
        "fecha_factura_fin": "2026-09-30T00:00:00.000Z",
    },
]


def make_coordinator(hass, return_value=None, side_effect=None):
    """Create an invoices coordinator with a mocked API client."""
    from custom_components.edificio_elite.invoices import EliteInvoicesCoordinator

    client = MagicMock()
    if side_effect is not None:
        client.async_get = AsyncMock(side_effect=side_effect)
    else:
        client.async_get = AsyncMock(return_value=return_value)
    return EliteInvoicesCoordinator(hass, client)


async def test_build_invoice_data_latest_and_sum():
    """Latest invoice is exposed plus the accumulated total."""
    from custom_components.edificio_elite.invoices import build_invoice_data

    data = build_invoice_data(INVOICES)
    assert data["id_factura"] == "2026-10-01"
    assert data["importe_total"] == 87.45
    assert data["importe_acumulado"] == 187.45
    assert data["num_facturas"] == 2


async def test_build_invoice_data_coerces_string_numbers():
    """Numeric columns may arrive as strings; they are coerced to float."""
    from custom_components.edificio_elite.invoices import build_invoice_data

    data = build_invoice_data(
        [{"importe_total": "87.45", "kwh_calor": "120", "m3_acs": "2.4"}]
    )
    assert data["importe_total"] == 87.45
    assert data["kwh_calor"] == 120.0
    assert data["m3_acs"] == 2.4
    assert data["importe_acumulado"] == 87.45


async def test_build_invoice_data_empty():
    """No invoices yields zero accumulation and no latest fields."""
    from custom_components.edificio_elite.invoices import build_invoice_data

    data = build_invoice_data([])
    assert data["importe_acumulado"] == 0
    assert data["num_facturas"] == 0
    assert data.get("importe_total") is None


async def test_refresh_success(hass):
    """A successful refresh builds the invoice data."""
    coord = make_coordinator(hass, return_value=INVOICES)
    result = await coord._async_update_data()
    assert result["id_factura"] == "2026-10-01"
    assert result["importe_acumulado"] == 187.45


async def test_refresh_network_error_keeps_previous(hass):
    """A network error keeps the previous data."""
    coord = make_coordinator(hass, side_effect=ClientError("boom"))
    coord.data = {"importe_total": 50.0}
    result = await coord._async_update_data()
    assert result["importe_total"] == 50.0


async def test_refresh_network_error_without_previous_raises(hass):
    """A network error without previous data raises UpdateFailed."""
    coord = make_coordinator(hass, side_effect=ClientError("boom"))
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()


async def test_refresh_unexpected_response_keeps_previous(hass):
    """A non-list response keeps the previous data."""
    coord = make_coordinator(hass, return_value={"not": "a list"})
    coord.data = {"importe_total": 50.0}
    result = await coord._async_update_data()
    assert result["importe_total"] == 50.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_invoices.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'custom_components.edificio_elite.invoices'`

- [ ] **Step 3: Implement the coordinator**

Create `custom_components/edificio_elite/invoices.py`:

```python
"""Invoice coordinator for the Edificio Elite integration."""

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EliteApiClient
from .const import DOMAIN, INVOICE_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

NUMERIC_FIELDS = (
    "importe_total",
    "importe_fijo",
    "kwh_calor",
    "kwh_frio",
    "kwh_acs",
    "m3_acs",
    "importe_calor",
    "importe_frio",
    "importe_variable_acs",
    "importe_acs",
)


def _to_float(value: Any) -> float | None:
    """Convert a value to float, returning None when not possible."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_invoice_data(invoices: list[dict]) -> dict:
    """Build the coordinator payload from the invoice list.

    The API returns invoices ordered by start date descending, so the first
    element is the most recent one.
    """
    latest = dict(invoices[0]) if invoices else {}
    for field in NUMERIC_FIELDS:
        if field in latest:
            latest[field] = _to_float(latest[field])

    latest["importe_acumulado"] = round(
        sum(_to_float(invoice.get("importe_total")) or 0 for invoice in invoices),
        2,
    )
    latest["num_facturas"] = len(invoices)
    return latest


class EliteInvoicesCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator that fetches invoices every 6 hours."""

    def __init__(self, hass: HomeAssistant, client: EliteApiClient) -> None:
        """Initialize the coordinator with the shared API client."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_facturas",
            update_interval=timedelta(seconds=INVOICE_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        """Fetch invoices, keeping previous data on soft errors."""
        try:
            invoices = await self.client.async_get("/facturas")
        except UpdateFailed:
            raise
        except Exception as err:
            if self.data is not None:
                _LOGGER.warning(
                    "Error fetching invoices, keeping previous values: %s", err
                )
                return self.data
            raise UpdateFailed(f"Invoice fetch error: {err}") from err

        if not isinstance(invoices, list):
            if self.data is not None:
                _LOGGER.warning("Unexpected invoices response, keeping previous data")
                return self.data
            raise UpdateFailed("Unexpected invoices response")

        return build_invoice_data(invoices)
```

- [ ] **Step 4: Run the tests**

Run: `pytest tests/test_invoices.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add custom_components/edificio_elite/invoices.py tests/test_invoices.py
git commit -m "feat: add invoices coordinator"
```

---

## Task 5: Cablear `__init__.py` y adaptar las plataformas

**Files:**
- Modify: `custom_components/edificio_elite/__init__.py`
- Modify: `custom_components/edificio_elite/sensor.py`
- Modify: `custom_components/edificio_elite/binary_sensor.py`

- [ ] **Step 1: Reescribir `__init__.py`**

Replace `custom_components/edificio_elite/__init__.py` with:

```python
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
```

- [ ] **Step 2: Adaptar `binary_sensor.py`**

Modify the coordinator lookup in `custom_components/edificio_elite/binary_sensor.py`:

```python
    coordinator: EliteClimateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "climate"
    ]
```

- [ ] **Step 3: Adaptar `sensor.py` (lookup, mapas y atributos)**

Modify `custom_components/edificio_elite/sensor.py`:

1. Add to the `.const` import: `DASHBOARD_URL`, `DEVICE_FACTURACION`, `FACTURACION_SENSORS`.
2. Add to `DEVICE_CLASS_MAP`:

```python
    "monetary": SensorDeviceClass.MONETARY,
```

3. Add to `UNIT_MAP`:

```python
    "EUR": "EUR",
```

4. Replace the beginning of `async_setup_entry` (the coordinator lookup) with:

```python
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: EliteClimateCoordinator = entry_data["climate"]
    invoices_coordinator = entry_data["invoices"]
```

5. Add the invoice loop just before `async_add_entities(entities)`:

```python
    for sensor_def in FACTURACION_SENSORS:
        entities.append(
            EliteClimateSensor(
                coordinator=invoices_coordinator,
                device_id=DEVICE_FACTURACION,
                device_name="Facturación",
                sensor_def=sensor_def,
            )
        )
```

6. Add this property to `EliteClimateSensor` (after `native_value`):

```python
    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return invoice detail attributes for the total invoice sensor."""
        if not self._sensor_def.get("invoice_attributes"):
            return None
        data = self.coordinator.data or {}
        return {
            "id_factura": data.get("id_factura"),
            "periodo": data.get("fecha_factura_inicio"),
            "periodo_fin": data.get("fecha_factura_fin"),
            "tiene_pdf": data.get("tiene_pdf"),
            "num_facturas": data.get("num_facturas"),
            "importe_variable_acs": data.get("importe_variable_acs"),
            "dashboard_url": DASHBOARD_URL,
        }
```

- [ ] **Step 4: Run the existing test suite**

Run: `pytest tests/ -v`
Expected: all passed (no test imports changed for sensors/binary sensors)

- [ ] **Step 5: Commit**

```bash
git add custom_components/edificio_elite/__init__.py custom_components/edificio_elite/sensor.py custom_components/edificio_elite/binary_sensor.py
git commit -m "feat: wire invoice coordinator and sensors"
```

---

## Task 6: Tests de los sensores de facturación

**Files:**
- Test: `tests/test_invoice_sensor.py`

- [ ] **Step 1: Escribir los tests**

Create `tests/test_invoice_sensor.py`:

```python
"""Tests for the Edificio Elite invoice sensors."""

from datetime import datetime
from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant


def make_sensor(coordinator, sensor_def):
    """Create an invoice sensor with a mocked coordinator."""
    from custom_components.edificio_elite.sensor import EliteClimateSensor

    return EliteClimateSensor(
        coordinator=coordinator,
        device_id="facturacion",
        device_name="Facturación",
        sensor_def=sensor_def,
    )


async def test_invoice_monetary_sensor(hass: HomeAssistant) -> None:
    """The total invoice sensor exposes value and detail attributes."""
    from custom_components.edificio_elite.const import FACTURACION_SENSORS

    sensor_def = next(
        s for s in FACTURACION_SENSORS if s["key"] == "importe_total"
    )
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {
        "importe_total": 87.45,
        "id_factura": "2026-10-01",
        "fecha_factura_inicio": "2026-10-01T00:00:00.000Z",
        "fecha_factura_fin": "2026-10-31T00:00:00.000Z",
        "tiene_pdf": True,
        "num_facturas": 3,
        "importe_variable_acs": 12.4,
    }
    coordinator.async_add_listener = MagicMock()

    sensor = make_sensor(coordinator, sensor_def)

    assert sensor.native_value == 87.45
    assert sensor.available is True
    attrs = sensor.extra_state_attributes
    assert attrs["id_factura"] == "2026-10-01"
    assert attrs["num_facturas"] == 3
    assert attrs["dashboard_url"] == "https://www.edificioelite.com/"


async def test_invoice_period_sensor_parses_timestamp(
    hass: HomeAssistant,
) -> None:
    """Period-end sensor returns a datetime."""
    from custom_components.edificio_elite.const import FACTURACION_SENSORS

    sensor_def = next(s for s in FACTURACION_SENSORS if s["key"] == "periodo_fin")
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"fecha_factura_fin": "2026-10-31T00:00:00.000Z"}
    coordinator.async_add_listener = MagicMock()

    sensor = make_sensor(coordinator, sensor_def)

    assert isinstance(sensor.native_value, datetime)
    assert sensor.native_value.month == 10


async def test_invoice_sensor_empty_data(hass: HomeAssistant) -> None:
    """An empty invoice list yields zero accumulated and no failure."""
    from custom_components.edificio_elite.const import FACTURACION_SENSORS

    sensor_def = next(
        s for s in FACTURACION_SENSORS if s["key"] == "importe_acumulado"
    )
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"importe_acumulado": 0, "num_facturas": 0}
    coordinator.async_add_listener = MagicMock()

    sensor = make_sensor(coordinator, sensor_def)

    assert sensor.native_value == 0
    assert sensor.available is True


async def test_non_invoice_sensor_has_no_invoice_attributes(
    hass: HomeAssistant,
) -> None:
    """Only the total invoice sensor carries invoice detail attributes."""
    from custom_components.edificio_elite.const import FACTURACION_SENSORS

    sensor_def = next(s for s in FACTURACION_SENSORS if s["key"] == "importe_fijo")
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {"importe_fijo": 20.0}
    coordinator.async_add_listener = MagicMock()

    sensor = make_sensor(coordinator, sensor_def)

    assert sensor.native_value == 20.0
    assert sensor.extra_state_attributes is None
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_invoice_sensor.py -v`
Expected: 4 passed

- [ ] **Step 3: Commit**

```bash
git add tests/test_invoice_sensor.py
git commit -m "test: cover invoice sensors"
```

---

## Task 7: Documentación

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`

- [ ] **Step 1: Actualizar `README.md`**

- Cambiar el bullet de entidades:

```markdown
- **34 entidades (31 sensores + 3 sensores binarios)** repartidos en cuatro dispositivos: Climatización, Agua Caliente Sanitaria, Agua Fría Sanitaria y Facturación
```

- Añadir tras la sección «Agua Fría Sanitaria»:

```markdown
### Facturación

Los datos se actualizan cada 6 horas.

| Sensor | Unidad | Descripción |
|---|---|---|
| Última factura: importe total | EUR | Importe total de la factura más reciente |
| Importe acumulado facturado | EUR | Suma de todas las facturas (válido para el Energy Dashboard) |
| Importe fijo | EUR | Parte fija de la última factura |
| Importe calefacción | EUR | Parte variable de calefacción |
| Importe refrigeración | EUR | Parte variable de refrigeración |
| Importe ACS | EUR | Parte de agua caliente sanitaria |
| Energía calefacción (periodo) | kWh | Energía de calefacción facturada en el periodo |
| Energía refrigeración (periodo) | kWh | Energía de refrigeración facturada en el periodo |
| Energía ACS (periodo) | kWh | Energía ACS facturada en el periodo |
| Consumo ACS (periodo) | m³ | Agua caliente facturada en el periodo |
| Inicio del periodo | — | Fecha de inicio del periodo facturado |
| Fin del periodo | — | Fecha de fin del periodo facturado |
```

- [ ] **Step 2: Actualizar `README.en.md`**

- Cambiar el bullet de entidades:

```markdown
- **34 entities (31 sensors + 3 binary sensors)** across four devices: Climate, DHW, Cold Water and Billing
```

- Añadir tras la sección «Agua Fría Sanitaria»:

```markdown
### Billing

Data is refreshed every 6 hours.

| Sensor | Unit | Description |
|---|---|---|
| Última factura: importe total | EUR | Total amount of the latest invoice |
| Importe acumulado facturado | EUR | Sum of all invoices (valid for the Energy Dashboard) |
| Importe fijo | EUR | Fixed part of the latest invoice |
| Importe calefacción | EUR | Variable heating part |
| Importe refrigeración | EUR | Variable cooling part |
| Importe ACS | EUR | Hot water part |
| Energía calefacción (periodo) | kWh | Heating energy billed in the period |
| Energía refrigeración (periodo) | kWh | Cooling energy billed in the period |
| Energía ACS (periodo) | kWh | DHW energy billed in the period |
| Consumo ACS (periodo) | m³ | Hot water billed in the period |
| Inicio del periodo | — | Billing period start date |
| Fin del periodo | — | Billing period end date |
```

- [ ] **Step 3: Commit**

```bash
git add README.md README.en.md
git commit -m "docs: document billing entities"
```

---

## Task 8: Verificación final

- [ ] **Step 1: Lint**

Run: `ruff check custom_components/`
Expected: `All checks passed!`

- [ ] **Step 2: Test suite completa**

Run: `pytest tests/ -v`
Expected: all passed

- [ ] **Step 3: Revisar el diff completo**

Run: `git diff main --stat`
Expected: `api.py`, `invoices.py`, `coordinator.py`, `const.py`, `sensor.py`, `binary_sensor.py`, `__init__.py`, tests, READMEs y `docs/specs/2026-11-15-facturas-ha-design.md`.

- [ ] **Step 4: Abrir PR**

```bash
git push -u origin feat/facturas-home-assistant
gh pr create --base main --title "feat: facturas de vivienda" --body "Añade el device Facturación con 12 sensores basados en GET /api/facturas (refresco cada 6 h). Incluye cliente API compartido y tests."
```

Esperar a que CI (ruff, pytest, hassfest) esté en verde antes de mergear.
