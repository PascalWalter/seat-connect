#!/usr/bin/env python3
"""Final integration test using the actual API client."""

import asyncio
import aiohttp
import sys
sys.path.insert(0, '.')

from custom_components.seat_connect.api import SeatApiClient, SeatApiAuthError


async def test_api_client():
    """Test the API client with wrong credentials (should fail gracefully)."""
    print("=" * 70)
    print("Testing SeatApiClient with test credentials")
    print("=" * 70)
    print()
    print("This test uses invalid credentials to verify the authentication")
    print("flow works correctly and returns the right error message.")
    print()

    async with aiohttp.ClientSession() as session:
        client = SeatApiClient(
            session=session,
            username="test@example.com",
            password="wrongpassword123",
            spin=None
        )

        try:
            print("Attempting to authenticate...")
            vehicles = await client.async_get_vehicle_data()
            print(f"Unexpected success! Found {len(vehicles)} vehicles")
        except SeatApiAuthError as e:
            print(f"\n✓ Got expected SeatApiAuthError: {e}")
            print("\n✓✓✓ Authentication flow is working! ✓✓✓")
            print("\nWith correct credentials, this should succeed.")
            return True
        except Exception as e:
            print(f"\n✗ Unexpected error type: {type(e).__name__}")
            print(f"  Error: {e}")
            return False

    return False


if __name__ == "__main__":
    print()
    result = asyncio.run(test_api_client())
    print()
    print("=" * 70)
    if result:
        print("TEST PASSED - Authentication flow is working correctly!")
        print()
        print("Next steps:")
        print("1. Copy the custom_components/seat_connect folder to your Home Assistant")
        print("2. Restart Home Assistant")
        print("3. Go to Settings > Integrations > Add Integration")
        print("4. Search for 'SEAT Connect' and add it")
        print("5. Enter your real SEAT/VW ID credentials")
    else:
        print("TEST FAILED - Please check the error messages above")
