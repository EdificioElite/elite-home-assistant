"""DataUpdateCoordinator for the Edificio Elite integration."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EliteApiClient
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class EliteClimateCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator that fetches climate and water data every 5 minutes."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: EliteApiClient,
        entry: ConfigEntry | None = None,
    ) -> None:
        """Initialize the coordinator with the shared API client and entry."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
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
