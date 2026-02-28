"""Constants for the Govee Cloud integration."""

DOMAIN = "govee_cloud"

# API endpoints (official Govee Developer API)
API_BASE_URL = "https://openapi.api.govee.com"
DEVICES_ENDPOINT = f"{API_BASE_URL}/router/api/v1/user/devices"
DEVICE_STATE_ENDPOINT = f"{API_BASE_URL}/router/api/v1/device/state"

# Update interval
UPDATE_INTERVAL = 300  # 5 minutes
