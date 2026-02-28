"""The Govee Cloud integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import GoveeAPI
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Govee Cloud from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    api_client = GoveeAPI(hass=hass, api_key=entry.data[CONF_API_KEY])

    async def async_update_data():
        """Fetch data from API endpoint."""
        devices = await hass.async_add_executor_job(api_client.get_devices)

        # Fetch state for each device
        results = []
        for device in devices:
            sku = device.get("sku", "")
            device_id = device.get("device", "")
            state = await hass.async_add_executor_job(
                api_client.get_device_state, sku, device_id
            )
            results.append({
                "device": device_id,
                "sku": sku,
                "deviceName": device.get("deviceName", ""),
                "state": state,
            })

        return results

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="govee_cloud",
        update_method=async_update_data,
        update_interval=timedelta(seconds=UPDATE_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api_client": api_client,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
