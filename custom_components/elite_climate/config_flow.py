"""Config flow for Elite Climate integration."""

from typing import Any

import voluptuous as vol
from aiohttp import ClientError

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_BASE_URL, DOMAIN


class EliteClimateConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Elite Climate."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                async with session.post(
                    f"{API_BASE_URL}/auth/login",
                    json={
                        "email": user_input[CONF_EMAIL],
                        "password": user_input[CONF_PASSWORD],
                    },
                ) as resp:
                    if resp.status == 200:
                        email_lower = user_input[CONF_EMAIL].lower()
                        await self.async_set_unique_id(email_lower)
                        self._abort_if_unique_id_configured()
                        return self.async_create_entry(
                            title=email_lower, data=user_input
                        )
                    if resp.status in (401, 403):
                        errors["base"] = "invalid_auth"
                    else:
                        errors["base"] = "cannot_connect"
            except ClientError:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
