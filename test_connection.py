#!/usr/bin/env python3
"""Test script to verify Seat Connect API connectivity."""

import asyncio
import aiohttp
import sys

# API endpoints to test
ENDPOINTS = [
    ("VW Group Identity", "https://identity.vwgroup.io/.well-known/openid-configuration"),
    ("VW MSG API", "https://msg.volkswagen.de"),
    ("MAL API", "https://mal-1a.prd.ece.vwg-connect.com/api"),
    ("SEAT OLA API", "https://ola.prod.code.seat.cloud.vwgroup.com"),
    ("Mobile API", "https://mobileapi.apps.emea.vwapps.io"),
]


async def test_connectivity():
    """Test connectivity to various API endpoints."""
    print("Testing Seat Connect API connectivity...\n")

    async with aiohttp.ClientSession() as session:
        for name, url in ENDPOINTS:
            try:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers={"User-Agent": "SEAT/2.17.0 Android/14"}
                ) as resp:
                    print(f"✓ {name}: {url}")
                    print(f"  Status: {resp.status}")
                    if resp.status == 200:
                        content_type = resp.headers.get("content-type", "")
                        if "json" in content_type:
                            data = await resp.json()
                            if isinstance(data, dict):
                                print(f"  Keys: {list(data.keys())[:5]}")
            except aiohttp.ClientError as e:
                print(f"✗ {name}: {url}")
                print(f"  Error: {e}")
            except Exception as e:
                print(f"✗ {name}: {url}")
                print(f"  Error: {type(e).__name__}: {e}")
            print()


async def test_auth_endpoint():
    """Test the authorization endpoint."""
    print("\nTesting OAuth2 Authorization endpoint...")

    auth_url = "https://identity.vwgroup.io/oidc/v1/authorize"
    params = {
        "response_type": "code",
        "client_id": "9dcc70f0-8e79-423a-a3fa-4065d99088b4@apps_vw-dilab_com",
        "redirect_uri": "seatconnect://identity-kit/login",
        "scope": "openid profile mbb cars",
        "state": "test123",
        "nonce": "test456",
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                auth_url,
                params=params,
                allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=15),
                headers={
                    "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                }
            ) as resp:
                print(f"Status: {resp.status}")
                print(f"Final URL: {resp.url}")

                if resp.status == 200:
                    html = await resp.text()
                    if "emailPasswordForm" in html:
                        print("✓ Login form found!")
                    elif "error" in html.lower():
                        print("✗ Error page returned")
                        # Find error message
                        import re
                        error_match = re.search(r'error[^>]*>([^<]+)', html, re.I)
                        if error_match:
                            print(f"  Error: {error_match.group(1)}")
                    else:
                        print(f"  Page content preview: {html[:500]}")

        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("SEAT Connect API Connectivity Test")
    print("=" * 60)

    asyncio.run(test_connectivity())
    asyncio.run(test_auth_endpoint())

    print("\n" + "=" * 60)
    print("Test complete.")
