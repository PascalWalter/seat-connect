# SEAT Connect Home Assistant Integration

[![HACS][hacs-badge]][hacs-url]
[![Home Assistant][ha-badge]][ha-url]

Home Assistant custom integration for SEAT Connect, providing full access to your SEAT vehicle through the official SEAT Connect API.

## Features

### Sensors
- **Battery state of charge** - Current battery level (%)
- **Electric range** - Estimated electric range (km)
- **Fuel level** - Current fuel level (%)
- **Fuel range** - Estimated fuel range (km)
- **Total range** - Combined electric + fuel range (km)
- **Charging power** - Current charging power (kW)
- **Charging state** - Current charging status
- **Charging time remaining** - Time until fully charged (min)
- **Target SoC** - Target state of charge (%)
- **Odometer** - Total kilometers driven
- **Climate target temperature** - Set climate temperature (°C)
- **Average speed** - Average driving speed (km/h)
- **Average consumption** - Electric (kWh/100km) and fuel (L/100km)

### Binary Sensors
- **Charging plug connected** - Is the charging cable plugged in
- **Charging plug locked** - Is the charging cable locked
- **External power** - Is external power available
- **Charging active** - Is the vehicle currently charging
- **All doors closed** - Are all doors closed
- **Individual doors** - Front left/right, rear left/right, trunk, hood
- **All windows closed** - Are all windows closed
- **Individual windows** - Front left/right, rear left/right, sunroof
- **Climatisation active** - Is climate control running
- **Window heating** - Front and rear window heating status
- **Vehicle locked** - Is the vehicle locked

### Controls
- **Lock/Unlock** - Remote lock and unlock vehicle
- **Climate control** - Start/stop pre-conditioning
- **Charging control** - Start/stop charging, set charge limit
- **Honk & Flash** - Activate horn and/or lights
- **Force refresh** - Request immediate vehicle status update

### Device Tracker
- **Vehicle position** - GPS location of your vehicle

## Installation

### HACS (Recommended)
1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as category
6. Click "Add"
7. Search for "SEAT Connect" and install it
8. Restart Home Assistant

### Manual Installation
1. Download the latest release from GitHub
2. Extract and copy the `seat_connect` folder to `custom_components/` in your Home Assistant config directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "SEAT Connect"
4. Enter your SEAT Connect credentials:
   - **Email**: Your SEAT ID email address
   - **Password**: Your SEAT ID password
   - **S-PIN** (optional): Required for unlock operations

## Services

The integration provides the following services:

| Service | Description |
|---------|-------------|
| `seat_connect.lock` | Lock the vehicle |
| `seat_connect.unlock` | Unlock the vehicle (requires S-PIN) |
| `seat_connect.start_climate` | Start pre-conditioning |
| `seat_connect.stop_climate` | Stop pre-conditioning |
| `seat_connect.start_charging` | Start charging |
| `seat_connect.stop_charging` | Stop charging |
| `seat_connect.honk` | Activate horn |
| `seat_connect.flash` | Flash lights |
| `seat_connect.trigger_request` | Request vehicle status update |
| `seat_connect.set_charge_limit` | Set target state of charge |
| `seat_connect.set_charge_current` | Set max charge current (reduced/max) |

### Example Service Call

```yaml
service: seat_connect.start_climate
data:
  vin: WVWZZZXXXXXXXXXXXXX
```

## Supported Vehicles

This integration supports SEAT vehicles with SEAT Connect capabilities:
- SEAT Leon (2020+)
- SEAT Ateca (2020+)
- SEAT Tarraco (2019+)
- SEAT Born (all)
- CUPRA Formentor
- CUPRA Leon
- CUPRA Born

## Requirements

- Home Assistant 2024.1.0 or newer
- Active SEAT Connect subscription
- SEAT ID account

## Troubleshooting

### Common Issues

**"Invalid authentication"**
- Verify your email and password are correct
- Try logging into the SEAT Connect app to confirm credentials

**"No vehicles found"**
- Make sure your vehicle is registered in SEAT Connect
- Check that your subscription is active

**"Cannot connect"**
- Check your internet connection
- SEAT Connect servers may be temporarily unavailable

### Debug Logging

Add to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.seat_connect: debug
```

## Privacy & Security

- Credentials are stored securely in Home Assistant
- Communication with SEAT servers uses HTTPS
- The S-PIN is required for security-sensitive operations (unlock)

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration is not affiliated with, endorsed by, or connected to SEAT S.A. or Volkswagen AG. Use at your own risk.

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[hacs-url]: https://hacs.xyz
[ha-badge]: https://img.shields.io/badge/Home%20Assistant-2024.1+-blue.svg
[ha-url]: https://www.home-assistant.io/
