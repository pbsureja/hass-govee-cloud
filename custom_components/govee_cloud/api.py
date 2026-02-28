"""Govee Cloud API client."""

import json
import logging
import os
import time
from typing import Dict, List, Optional

import jwt
import requests
from homeassistant.core import HomeAssistant

from .const import DEVICES_ENDPOINT, LOGIN_ENDPOINT, THERMOMETER_SKU

_LOGGER = logging.getLogger(__name__)


class GoveeAPI:
    """Govee Cloud API client."""

    def __init__(self, hass: HomeAssistant, email: str, password: str):
        """Initialize the API client."""
        self.hass = hass
        self.email = email
        self.password = password
        self._token = None
        self._token_file = os.path.join(hass.config.config_dir, ".govee_token.json")

    def govee_temp_value(self, api_value: int) -> float:
        """Extract temperature value from Govee API in Celsius."""
        celsius = api_value / 100.0
        return round(celsius, 1)

    def _load_token(self) -> Optional[str]:
        """Load JWT token from file if it exists and is not expired."""
        if not os.path.exists(self._token_file):
            _LOGGER.debug("No cached token found")
            return None

        try:
            with open(self._token_file, "r") as f:
                data = json.load(f)

            token = data.get("token")
            if not token:
                return None

            # Decode JWT to check expiration
            decoded = jwt.decode(token, options={"verify_signature": False})
            exp = decoded.get("exp")

            if exp and exp > time.time():
                _LOGGER.info(
                    "Using cached token (expires: %s)",
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(exp)),
                )
                return token
            else:
                _LOGGER.info("Cached token expired, will need to re-authenticate")
                return None

        except Exception as err:
            _LOGGER.debug("Error loading cached token: %s", err)
            return None

    def _save_token(self, token: str) -> None:
        """Save JWT token to file."""
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            exp = decoded.get("exp")
            exp_str = (
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(exp))
                if exp
                else "unknown"
            )

            fd = os.open(self._token_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as f:
                json.dump({"token": token}, f)
            _LOGGER.info("Token cached successfully (expires: %s)", exp_str)
        except Exception as err:
            _LOGGER.error("Failed to cache token: %s", err)

    def _login(self) -> str:
        """Login to Govee API and return token."""
        _LOGGER.info("Authenticating with Govee API")

        session = requests.Session()
        session.headers.update(
            {
                "sysVersion": "12",
                "country": "US",
                "appVersion": "7.0.30",
                "clientId": "53b5cfa4c9726a27",
                "clientType": "0",
                "timezone": "America/New_York",
                "Accept-Language": "en",
                "envId": "0",
                "iotVersion": "0",
                "Content-Type": "application/json; charset=UTF-8",
                "User-Agent": "okhttp/4.12.0",
            }
        )

        timestamp = int(time.time() * 1000)
        login_data = {
            "client": "53b5cfa4c9726a27",
            "code1": "",
            "email": self.email,
            "password": self.password,
            "key": "",
            "view": 0,
            "transaction": str(timestamp),
        }

        session.headers["timestamp"] = str(timestamp)

        response = session.post(LOGIN_ENDPOINT, json=login_data)
        response.raise_for_status()

        token = response.json()["client"]["token"]
        self._save_token(token)
        _LOGGER.info("Successfully authenticated with Govee API")
        return token

    def _ensure_authenticated(self) -> None:
        """Ensure we have a valid authentication token."""
        if self._token is None:
            self._token = self._load_token()

        if self._token is None:
            self._token = self._login()

    def get_devices(self) -> List[Dict]:
        """Get list of thermometer devices."""
        self._ensure_authenticated()

        session = requests.Session()
        session.headers.update(
            {
                "sysVersion": "12",
                "country": "US",
                "appVersion": "7.0.30",
                "clientId": "53b5cfa4c9726a27",
                "clientType": "0",
                "timezone": "America/New_York",
                "Accept-Language": "en",
                "envId": "0",
                "iotVersion": "0",
                "Content-Type": "application/json; charset=UTF-8",
                "User-Agent": "okhttp/4.12.0",
                "Authorization": f"Bearer {self._token}",
            }
        )

        response = session.get(DEVICES_ENDPOINT)
        response.raise_for_status()
        data = response.json()

        if (status := data.get("status")) and status == 401:
            _LOGGER.warning("Token expired, re-authenticating")
            self._token = None
            self._ensure_authenticated()
            session.headers["Authorization"] = f"Bearer {self._token}"
            response = session.get(DEVICES_ENDPOINT)
            response.raise_for_status()
            data = response.json()

        # Filter for thermometer devices
        devices = data.get("data", {}).get("devices", [])
        thermometers = [d for d in devices if d.get("sku") == THERMOMETER_SKU]

        _LOGGER.debug("Found %d thermometer devices", len(thermometers))
        return thermometers

    def extract_device_data(self, device: Dict) -> Dict:
        """Extract temperature and other data from device."""
        device_ext = device.get("deviceExt", {})
        last_device_data_str = device_ext.get("lastDeviceData", "{}")
        last_device_data = json.loads(last_device_data_str)

        temp_raw = last_device_data.get("tem")
        temperature = self.govee_temp_value(temp_raw) if temp_raw is not None else None

        return {
            "temperature": temperature,
            "humidity": last_device_data.get("hum", 0) / 100.0
            if last_device_data.get("hum")
            else None,
            "battery": json.loads(device_ext.get("deviceSettings", "{}")).get(
                "battery"
            ),
            "online": last_device_data.get("online", False),
            "last_update": last_device_data.get("lastTime"),
        }
