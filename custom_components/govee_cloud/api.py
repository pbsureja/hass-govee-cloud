"""Govee Cloud API client using the official Developer API."""

import logging
import uuid
from typing import Any, Dict, List, Optional

import requests
from homeassistant.core import HomeAssistant

from .const import DEVICES_ENDPOINT, DEVICE_STATE_ENDPOINT

_LOGGER = logging.getLogger(__name__)

# Capabilities that indicate a sensor device
SENSOR_CAPABILITIES = {"sensorTemperature", "sensorHumidity"}


class GoveeAPI:
    """Govee Cloud API client."""

    def __init__(self, hass: HomeAssistant, api_key: str):
        """Initialize the API client."""
        self.hass = hass
        self._api_key = api_key

    def _headers(self) -> Dict[str, str]:
        """Return common request headers."""
        return {
            "Content-Type": "application/json",
            "Govee-API-Key": self._api_key,
        }

    def get_devices(self) -> List[Dict]:
        """Get list of devices with sensor capabilities."""
        response = requests.get(DEVICES_ENDPOINT, headers=self._headers())
        response.raise_for_status()
        data = response.json()

        if data.get("code") != 200:
            msg = data.get("message", str(data))
            raise ValueError(f"Govee API error: {msg}")

        devices = data.get("data", [])

        # Filter to devices that have sensor capabilities
        sensor_devices = []
        for device in devices:
            caps = {c.get("instance") for c in device.get("capabilities", [])}
            if caps & SENSOR_CAPABILITIES:
                sensor_devices.append(device)

        _LOGGER.debug("Found %d sensor devices", len(sensor_devices))
        return sensor_devices

    def get_device_state(self, sku: str, device_id: str) -> Dict[str, Any]:
        """Get current state of a device."""
        payload = {
            "requestId": str(uuid.uuid4()),
            "payload": {
                "sku": sku,
                "device": device_id,
            },
        }

        response = requests.post(
            DEVICE_STATE_ENDPOINT, headers=self._headers(), json=payload
        )
        response.raise_for_status()
        data = response.json()

        if data.get("code") != 200:
            msg = data.get("message", str(data))
            _LOGGER.warning("Failed to get state for %s: %s", device_id, msg)
            return {}

        return data.get("payload", {})

    def extract_device_data(self, state_payload: Dict) -> Dict[str, Any]:
        """Extract sensor data from device state capabilities."""
        capabilities = state_payload.get("capabilities", [])

        result: Dict[str, Any] = {
            "temperature": None,
            "humidity": None,
            "battery": None,
            "online": None,
        }

        for cap in capabilities:
            instance = cap.get("instance")
            state = cap.get("state", {})
            value = state.get("value")

            if instance == "sensorTemperature" and value is not None:
                # API returns temperature in hundredths of a degree Celsius
                result["temperature"] = round(value / 100.0, 1)
            elif instance == "sensorHumidity" and value is not None:
                # API returns humidity in hundredths of a percent
                result["humidity"] = round(value / 100.0, 1)
            elif instance == "battery" and value is not None:
                result["battery"] = value
            elif instance == "online" and value is not None:
                result["online"] = value

        return result
