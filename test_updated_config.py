#!/usr/bin/env python3
"""Test the updated configuration."""

import asyncio
import aiohttp
import sys
sys.path.insert(0, '.')

from custom_components.seat_connect.const import (
    CLIENT_ID, REDIRECT_URI, SCOPES, UI_LOCALES, AUTH_AUTHORIZE_URL
)

async def test_config():
    """Test the updated OAuth configuration."""
    print("Testing updated SEAT Connect OAuth configuration...")
    print("=" * 60)
    print(f"Client ID: {CLIENT_ID}")
    print(f"Redirect URI: {REDIRECT_URI}")
    print(f"Scopes: {' '.join(SCOPES)}")
    print(f"UI Locales: {UI_LOCALES}")
    print("=" * 60)

    params = {
        "response_type": "code id_token",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": "test123",
        "nonce": "test456",
        "ui_locales": UI_LOCALES,
        "prompt": "login",
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                AUTH_AUTHORIZE_URL,
                params=params,
                allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=15),
                headers={
                    "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 6) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "de-DE,de;q=0.9",
                }
            ) as resp:
                print(f"\nStatus: {resp.status}")
                print(f"Final URL: {str(resp.url)[:100]}...")

                if resp.status == 200:
                    html = await resp.text()

                    if "email" in html.lower() or "identifier" in html.lower() or "login" in html.lower():
                        print("\n✓✓✓ SUCCESS! Login page received! ✓✓✓")

                        # Try to find the form
                        import re
                        form_match = re.search(r'<form[^>]*action=["\']([^"\']+)["\']', html, re.I)
                        if form_match:
                            print(f"Form action found: {form_match.group(1)[:80]}")

                        # Check for input fields
                        if "email" in html.lower():
                            print("Email input field: ✓")
                        if "password" in html.lower():
                            print("Password input field: ✓")

                        return True
                    else:
                        print(f"\n✗ Unexpected page content")
                        print(f"Preview: {html[:500]}")
                else:
                    text = await resp.text()
                    print(f"\n✗ HTTP {resp.status}")
                    print(f"Response: {text[:300]}")

        except Exception as e:
            print(f"\n✗ Error: {type(e).__name__}: {e}")

    return False


if __name__ == "__main__":
    result = asyncio.run(test_config())
    print("\n" + "=" * 60)
    if result:
        print("Configuration is working! Try adding the integration in Home Assistant.")
    else:
        print("Configuration needs adjustment.")
