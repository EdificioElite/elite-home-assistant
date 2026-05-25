"""Tests for Edificio Elite config flow."""

from unittest.mock import MagicMock, patch

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
    """Test config flow with valid credentials."""
    from custom_components.edificio_elite.config_flow import EliteClimateConfigFlow

    mock_resp = MockResponse(200)
    mock_session = MagicMock()
    mock_session.post.return_value = mock_resp

    hass.config_entries.async_entry_for_domain_unique_id.return_value = None

    with patch(
        "custom_components.edificio_elite.config_flow.async_get_clientsession",
        return_value=mock_session,
    ):
        flow = EliteClimateConfigFlow()
        flow.hass = hass
        flow.context = {}

        result = await flow.async_step_user(
            {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "secret"}
        )

    assert result["type"] == "create_entry"
    assert result["title"] == "test@example.com"
    assert result["data"][CONF_EMAIL] == "test@example.com"
    assert result["data"][CONF_PASSWORD] == "secret"

    mock_session.post.assert_called_once()
    _, kwargs = mock_session.post.call_args
    assert kwargs["json"]["source"] == "home-assistant"


async def test_config_flow_invalid_auth(hass: HomeAssistant) -> None:
    """Test config flow with invalid credentials."""
    from custom_components.edificio_elite.config_flow import EliteClimateConfigFlow

    mock_resp = MockResponse(401)
    mock_session = MagicMock()
    mock_session.post.return_value = mock_resp

    with patch(
        "custom_components.edificio_elite.config_flow.async_get_clientsession",
        return_value=mock_session,
    ):
        flow = EliteClimateConfigFlow()
        flow.hass = hass

        result = await flow.async_step_user(
            {CONF_EMAIL: "bad@example.com", CONF_PASSWORD: "wrong"}
        )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_auth"}
