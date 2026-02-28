"""Config flow for Govee Cloud integration."""

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .api import GoveeAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect."""
    api_client = GoveeAPI(hass, data[CONF_EMAIL], data[CONF_PASSWORD])

    # Test authentication by getting devices using executor
    devices = await hass.async_add_executor_job(api_client.get_devices)

    return {"title": f"Govee Cloud ({data[CONF_EMAIL]})", "num_devices": len(devices)}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Govee Cloud."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_EMAIL, description="Email Address"): str,
                        vol.Required(CONF_PASSWORD, description="Password"): str,
                    }
                ),
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except ValueError as err:
            _LOGGER.error("Govee authentication failed: %s", err)
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_EMAIL,
                        default=user_input.get(CONF_EMAIL, ""),
                        description="Email Address",
                    ): str,
                    vol.Required(
                        CONF_PASSWORD,
                        default=user_input.get(CONF_PASSWORD, ""),
                        description="Password",
                    ): str,
                }
            ),
            errors=errors,
        )
