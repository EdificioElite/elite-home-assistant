"""Shared API client for the Edificio Elite integration."""

import asyncio
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
        self._login_lock = asyncio.Lock()

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
                    text = (await resp.text())[:200]
                    _LOGGER.warning("Login rate-limited by API: %s", text)
                    raise UpdateFailed(
                        "Login temporarily blocked (rate limit), will retry"
                    )
                if resp.status in (401, 403):
                    text = (await resp.text())[:200]
                    _LOGGER.error(
                        "Login rejected (status %s): %s", resp.status, text
                    )
                    raise UpdateFailed(
                        f"Login failed with status {resp.status}: {text}"
                    )
                if resp.status != 200:
                    text = (await resp.text())[:200]
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

    async def _ensure_login(self) -> None:
        """Log in once, serializing concurrent callers."""
        if self._token is not None:
            return
        async with self._login_lock:
            if self._token is None:
                await self.async_login()

    async def async_get(self, path: str) -> Any:
        """Perform an authenticated GET.

        Raises:
            UpdateFailed: On HTTP or authentication errors.
            aiohttp.ClientError: Transport errors propagate so coordinators
                can keep previous data.
        """
        return await self._async_get(path)

    async def _async_get(self, path: str, retried: bool = False) -> Any:
        """Perform an authenticated GET, re-logging in once on 401."""
        await self._ensure_login()

        headers = {"Authorization": f"Bearer {self._token}"}
        async with self._session.get(
            f"{API_BASE_URL}{path}", headers=headers
        ) as resp:
            if resp.status == 401:
                if retried:
                    raise UpdateFailed("Authentication failed after re-login")
                self._token = None
                await self._ensure_login()
                return await self._async_get(path, retried=True)
            if resp.status != 200:
                raise UpdateFailed(f"API returned status {resp.status}")
            return await resp.json()
