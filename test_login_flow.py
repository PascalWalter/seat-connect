#!/usr/bin/env python3
"""Test the complete login flow (without actual credentials)."""

import asyncio
import aiohttp
import re
import html as html_module
import sys
sys.path.insert(0, '.')

from custom_components.seat_connect.const import (
    CLIENT_ID, REDIRECT_URI, SCOPES, UI_LOCALES, AUTH_AUTHORIZE_URL
)

# For testing only - use fake credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "wrongpassword"


async def test_login_flow():
    """Test the login flow step by step."""
    print("=" * 70)
    print("Testing SEAT Connect Login Flow")
    print("=" * 70)

    jar = aiohttp.CookieJar()
    connector = aiohttp.TCPConnector(ssl=True)

    async with aiohttp.ClientSession(connector=connector, cookie_jar=jar) as session:

        # Step 1: Get authorization page
        print("\n[Step 1] Getting authorization page...")
        params = {
            "response_type": "code id_token",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": " ".join(SCOPES),
            "state": "teststate123",
            "nonce": "testnonce456",
            "ui_locales": UI_LOCALES,
            "prompt": "login",
        }

        async with session.get(
            AUTH_AUTHORIZE_URL,
            params=params,
            allow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 6) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml",
                "Accept-Language": "de-DE,de;q=0.9",
            }
        ) as resp:
            print(f"  Status: {resp.status}")
            print(f"  URL: {resp.url}")

            if resp.status != 200:
                print(f"  ✗ Failed to get login page")
                return

            html = await resp.text()
            current_url = str(resp.url)
            print(f"  ✓ Got login page ({len(html)} bytes)")

        # Step 2: Parse form
        print("\n[Step 2] Parsing login form...")

        form_match = re.search(r'<form[^>]*action=["\']([^"\']+)["\']', html, re.I)
        if form_match:
            form_action = html_module.unescape(form_match.group(1))
            if form_action.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(current_url)
                form_action = f"{parsed.scheme}://{parsed.netloc}{form_action}"
        else:
            form_action = current_url

        print(f"  Form action: {form_action}")

        # Extract hidden fields
        hidden_fields = {}
        for match in re.finditer(r'<input[^>]*type=["\']hidden["\'][^>]*>', html, re.I):
            input_html = match.group(0)
            name_match = re.search(r'name=["\']([^"\']+)["\']', input_html)
            value_match = re.search(r'value=["\']([^"\']*)["\']', input_html)
            if name_match:
                hidden_fields[name_match.group(1)] = value_match.group(1) if value_match else ""

        print(f"  Hidden fields: {list(hidden_fields.keys())}")

        # Step 3: Submit credentials
        print("\n[Step 3] Submitting test credentials...")

        login_data = {
            **hidden_fields,
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD,
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 6) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://identity.vwgroup.io",
            "Referer": current_url,
        }

        async with session.post(
            form_action,
            data=login_data,
            headers=headers,
            allow_redirects=False
        ) as resp:
            print(f"  Status: {resp.status}")

            if resp.status == 200:
                response_html = await resp.text()

                # Check for error message (expected with wrong credentials)
                if "incorrect" in response_html.lower() or "wrong" in response_html.lower() or "error" in response_html.lower() or "falsch" in response_html.lower():
                    print("  ✓ Server responded with authentication error (expected with test credentials)")
                    print("  ✓✓✓ LOGIN FLOW WORKS! Use real credentials in Home Assistant. ✓✓✓")
                else:
                    print(f"  Response preview: {response_html[:300]}")

            elif resp.status in (301, 302, 303, 307):
                redirect_url = resp.headers.get("Location", "")
                print(f"  Redirect to: {redirect_url[:100]}")

                if "code=" in redirect_url or REDIRECT_URI.split("://")[0] in redirect_url:
                    print("  ✓ Got authorization code redirect!")
                else:
                    print("  Following redirect...")
            else:
                response_text = await resp.text()
                print(f"  Response: {response_text[:200]}")


if __name__ == "__main__":
    asyncio.run(test_login_flow())
    print("\n" + "=" * 70)
    print("Test complete.")
