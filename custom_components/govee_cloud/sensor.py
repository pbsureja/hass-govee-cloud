"""Sensor platform for Govee Cloud integration."""

import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    api_client = data["api_client"]

    entities = []
    for device in coordinator.data:
        device_id = device.get("device")
        sensor_data = api_client.extract_device_data(device.get("state", {}))

        if sensor_data.get("temperature") is not None:
            entities.append(
                GoveeTemperatureSensor(
                    coordinator, api_client, device_id, device, config_entry
                )
            )

        if sensor_data.get("humidity") is not None:
            entities.append(
                GoveeHumiditySensor(
                    coordinator, api_client, device_id, device, config_entry
                )
            )

        if sensor_data.get("battery") is not None:
            entities.append(
                GoveeBatterySensor(
                    coordinator, api_client, device_id, device, config_entry
                )
            )

    async_add_entities(entities)


class GoveeBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Govee sensors."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        api_client,
        device_id: str,
        device_info: Dict[str, Any],
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.api_client = api_client
        self.device_id = device_id
        self.device_info_dict = device_info
        self.config_entry = config_entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.device_id)},
            name=self.device_info_dict.get("deviceName", "Govee Sensor"),
            manufacturer="Govee",
            model=self.device_info_dict.get("sku"),
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success and self._get_device() is not None

    def _get_device(self) -> Optional[Dict[str, Any]]:
        """Get device data from coordinator."""
        for device in self.coordinator.data:
            if device.get("device") == self.device_id:
                return device
        return None

    def _get_sensor_data(self) -> Dict[str, Any]:
        """Get sensor data for this device."""
        device = self._get_device()
        if device is None:
            return {}
        return self.api_client.extract_device_data(device.get("state", {}))


class GoveeTemperatureSensor(GoveeBaseSensor):
    """Temperature sensor for Govee device."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        api_client,
        device_id: str,
        device_info: Dict[str, Any],
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, api_client, device_id, device_info, config_entry)
        self._attr_name = (
            f"{device_info.get('deviceName', 'Govee Sensor')} Temperature"
        )
        self._attr_unique_id = f"{device_id}_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor."""
        sensor_data = self._get_sensor_data()
        return sensor_data.get("temperature")


class GoveeHumiditySensor(GoveeBaseSensor):
    """Humidity sensor for Govee device."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        api_client,
        device_id: str,
        device_info: Dict[str, Any],
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the humidity sensor."""
        super().__init__(coordinator, api_client, device_id, device_info, config_entry)
        self._attr_name = (
            f"{device_info.get('deviceName', 'Govee Sensor')} Humidity"
        )
        self._attr_unique_id = f"{device_id}_humidity"
        self._attr_device_class = SensorDeviceClass.HUMIDITY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor."""
        sensor_data = self._get_sensor_data()
        return sensor_data.get("humidity")


class GoveeBatterySensor(GoveeBaseSensor):
    """Battery sensor for Govee device."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        api_client,
        device_id: str,
        device_info: Dict[str, Any],
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the battery sensor."""
        super().__init__(coordinator, api_client, device_id, device_info, config_entry)
        self._attr_name = (
            f"{device_info.get('deviceName', 'Govee Sensor')} Battery"
        )
        self._attr_unique_id = f"{device_id}_battery"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> Optional[int]:
        """Return the state of the sensor."""
        sensor_data = self._get_sensor_data()
        return sensor_data.get("battery")
