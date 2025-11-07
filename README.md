# Home Assistant Seat Connect

Custom component that integrates the My SEAT (SEAT Connect) cloud APIs into Home Assistant.

## Features
- OAuth2 Authorization Code flow via Home Assistant Application Credentials
- High frequency updates using `DataUpdateCoordinator` (default 90s, configurable)
- Sensors: battery state of charge, range, charging power, charging state
- Binary sensors: plug connection, doors/windows open
- Lock entity for remote locking/unlocking
- Climate entity to start or stop pre-conditioning when the API exposes the capability
- Services: `seat_connect.lock`, `seat_connect.unlock`, `seat_connect.start_climate`, `seat_connect.stop_climate`
- Robust `aiohttp` client with retries, exponential backoff, and rate-limit awareness
- Fully typed code base with ruff, mypy, and pytest automation via GitHub Actions

## Installation
1. Copy `custom_components/seat_connect` into your Home Assistant `config/custom_components` directory or add this repository as a custom repository in HACS.
2. Restart Home Assistant.
3. Add the integration via **Settings → Devices & Services → Add Integration → SEAT Connect**. Provide the VINs you wish to expose and authorize through the My SEAT OAuth2 login page.

## Configuration Options
- Update interval in seconds (default 90). Configurable through the integration options.

## Development
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
ruff check .
mypy custom_components/seat_connect
```

## License
MIT
