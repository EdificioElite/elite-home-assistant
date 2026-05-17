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
                json={"email": self._email, "password": self._password, "source": "home-assistant"},
            ) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"Login failed with status {resp.status}")
                data = await resp.json()
                self._token = data["token"]
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Login error: {err}") from err

    async def _fetch_consumo_actual(self, _reauthed: bool = False) -> dict:
        """Fetch current consumption data, handling 401 re-auth."""
        headers = {"Authorization": f"Bearer {self._token}"}
        try:
            async with self._session.get(
                f"{API_BASE_URL}/consumo-actual", headers=headers
            ) as resp:
                if resp.status == 401:
                    if not _reauthed:
                        self._token = None
                        await self._login()
                        return await self._fetch_consumo_actual(_reauthed=True)
                    raise UpdateFailed("Authentication failed after re-login")
                if resp.status != 200:
                    raise UpdateFailed(f"API returned status {resp.status}")
                data = await resp.json()
                if data is None:
                    if self.data is not None:
                        _LOGGER.debug("API returned null, keeping previous data")
                        return self.data
                    raise UpdateFailed("No data available from API")
                return data
        except UpdateFailed:
            raise
        except Exception as err:
            if self.data is not None:
                _LOGGER.warning("Error fetching data, keeping previous values: %s", err)
                return self.data
            raise UpdateFailed(f"Fetch error: {err}") from err
