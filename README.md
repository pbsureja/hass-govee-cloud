# Govee Cloud – Home Assistant Integration

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pbsureja&repository=hass-govee-cloud&category=integration)

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-blue.svg?style=flat-square)](https://hacs.xyz/) [![GitHub issues](https://img.shields.io/github/issues/pbsureja/hass-govee-cloud?style=flat-square)](https://github.com/pbsureja/hass-govee-cloud/issues)

This custom integration connects Govee cloud-connected thermometers to Home Assistant, providing temperature, humidity, and battery level data.

## Features

- Temperature sensor (`°C` or `°F`)
- Humidity sensor (`%`)
- Battery level sensor (`%`)
- Device info and automatic cloud polling every 5 minutes

## Installation

### **Quick install with My Home Assistant**

1. Click the badge at the top of this README.
2. Your Home Assistant will open with the repository pre-selected in HACS.
3. Follow the prompts to install and then restart Home Assistant.

### **HACS (custom repository)**

1. In HACS, go to **Integrations → Custom repositories** and add this repository URL (`https://github.com/pbsureja/hass-govee-cloud`) as **Integration**.
2. Search for "Govee Cloud" in HACS and install it.
3. Restart Home Assistant.

### **Manual**

Copy the `custom_components/govee_cloud/` folder into your Home Assistant `custom_components/` directory and restart Home Assistant.

## Configuration

1. Go to **Settings** > **Devices & Services** in Home Assistant.
2. Click **Add Integration** and search for "Govee Cloud".
3. Enter your Govee cloud email and password when prompted.

## Entities Created

| Entity ID suffix | Description | Unit |
|------------------|-------------|------|
| `temperature`    | Temperature | °C   |
| `humidity`       | Humidity    | %    |
| `battery`        | Battery     | %    |

## Known Limitations

- Requires a Govee cloud account (no local/Bluetooth support).
- Currently only supports the Govee H5111 Thermometer/Hygrometer.

## Troubleshooting

If you see a "Cannot connect" error, double-check your credentials and network.
To enable debug logging, add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.govee_cloud: debug
```

## Contributing

Pull requests are welcome! Please follow the code style enforced by `ruff`.
