"""Invoice coordinator for the Edificio Elite integration."""

import logging
import math
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
    """Convert a value to a finite float, returning None otherwise."""
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


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
        sum(
            (_to_float(invoice.get("importe_total")) or 0 for invoice in invoices),
            0.0,
        ),
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
