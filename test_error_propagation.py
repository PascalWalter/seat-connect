#!/usr/bin/env python3
"""Test error propagation through the API layers."""

import asyncio
import aiohttp
import logging
import sys

# Setup logging to see what's happening
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, '.')

from custom_components.seat_connect.api import (
    SeatApiClient,
    SeatApiAuthError,
    SeatApiError,
    SeatApiCommunicationError
)

async def test_error_propagation():
    """Test that errors propagate correctly."""
    print("=" * 60)
    print("Testing Error Propagation")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        client = SeatApiClient(
            session=session,
            username="test@example.com",
            password="wrongpassword",
        )

        try:
            print("\nCalling async_get_vehicle_data()...")
            await client.async_get_vehicle_data()
            print("ERROR: Should have raised an exception!")

        except SeatApiAuthError as e:
            print(f"\n✓ Got SeatApiAuthError: {e}")
            print("  -> This maps to 'invalid_auth' in config flow")
            return "invalid_auth"

        except SeatApiCommunicationError as e:
            print(f"\n✓ Got SeatApiCommunicationError: {e}")
            print("  -> This maps to 'cannot_connect' in config flow")
            return "cannot_connect"

        except SeatApiError as e:
            print(f"\n✓ Got SeatApiError: {e}")
            print("  -> This maps to 'cannot_connect' in config flow")
            return "cannot_connect"

        except aiohttp.ClientError as e:
            print(f"\n✓ Got aiohttp.ClientError: {e}")
            print("  -> This maps to 'cannot_connect' in config flow")
            return "cannot_connect"

        except Exception as e:
            print(f"\n✗ Got unexpected exception: {type(e).__name__}: {e}")
            print("  -> This maps to 'unknown' in config flow")
            return "unknown"

    return None


if __name__ == "__main__":
    result = asyncio.run(test_error_propagation())
    print("\n" + "=" * 60)
    print(f"Expected config_flow error: {result}")
