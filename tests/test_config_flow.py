"""Tests for Elite Climate config flow."""

from unittest.mock import MagicMock

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant


class MockResponse:
    def __init__(self, status, json_data=None):
        self.status = status
        self._json_data = json_data

    async def json(self):
        return self._json_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


async def test_config_flow_success(hass: HomeAssistant) -> None:
    """Test the full config flow with valid credentials."""
    from custom_components.elite_climate.const import DOMAIN

    mock_resp = MockResponse(200)
    mock_session = MagicMock()
    mock_session.post.return_value = mock_resp

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "custom_components.elite_climate.config_flow.async_get_clientsession",
            lambda hass: mock_session,
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "secret"},
        )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "test@example.com"
    assert result["data"][CONF_EMAIL] == "test@example.com"
    assert result["data"][CONF_PASSWORD] == "secret"


async def test_config_flow_invalid_auth(hass: HomeAssistant) -> None:
    """Test config flow with invalid credentials."""
    from custom_components.elite_climate.const import DOMAIN

    mock_resp = MockResponse(401)
    mock_session = MagicMock()
    mock_session.post.return_value = mock_resp

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "custom_components.elite_climate.config_flow.async_get_clientsession",
            lambda hass: mock_session,
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_EMAIL: "bad@example.com", CONF_PASSWORD: "wrong"},
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}
