#!/usr/bin/env python3
"""Debug the login submission in detail."""

import asyncio
import aiohttp
import re
import html as html_module
import json
import sys
sys.path.insert(0, '.')

from custom_components.seat_connect.const import (
    CLIENT_ID, REDIRECT_URI, SCOPES, UI_LOCALES, AUTH_AUTHORIZE_URL
)


async def debug_login():
    """Debug the login submission."""
    print("=" * 70)
    print("Debugging Login Submission")
    print("=" * 70)

    jar = aiohttp.CookieJar()
    connector = aiohttp.TCPConnector(ssl=True)

    async with aiohttp.ClientSession(connector=connector, cookie_jar=jar) as session:

        # Step 1: Get login page
        print("\n[1] Getting login page...")
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
            html = await resp.text()
            current_url = str(resp.url)
            print(f"  URL: {current_url}")

        # Save full HTML for analysis
        with open("/tmp/login_page.html", "w") as f:
            f.write(html)
        print("  Saved to /tmp/login_page.html")

        # Look for all forms
        print("\n[2] Analyzing forms...")
        forms = re.findall(r'<form[^>]*>(.*?)</form>', html, re.I | re.DOTALL)
        print(f"  Found {len(forms)} form(s)")

        # Check for action attribute
        action_match = re.search(r'<form[^>]*action=["\']([^"\']*)["\']', html, re.I)
        if action_match:
            print(f"  Form action: {action_match.group(1)}")
        else:
            print("  No form action found - form likely submits via JavaScript")

        # Look for JavaScript submit handlers
        print("\n[3] Looking for JavaScript submission logic...")

        # Auth0 typically uses usernamepassword/login endpoint
        if "/usernamepassword/login" in html:
            print("  Found /usernamepassword/login endpoint!")

        # Look for fetch/XHR patterns
        api_patterns = [
            (r'/co/authenticate', 'Auth0 co/authenticate'),
            (r'/usernamepassword/login', 'Auth0 usernamepassword/login'),
            (r'"/u/login"', 'u/login endpoint'),
            (r'action:\s*["\']([^"\']+)["\']', 'JS action'),
        ]

        for pattern, name in api_patterns:
            match = re.search(pattern, html, re.I)
            if match:
                print(f"  Found {name}: {match.group(0)[:60]}")

        # Extract state parameter from URL
        print("\n[4] Extracting state parameter...")
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(current_url)
        url_params = parse_qs(parsed_url.query)
        state = url_params.get('state', [''])[0]
        print(f"  State from URL: {state[:50]}...")

        # Try Auth0-style JSON submission
        print("\n[5] Trying Auth0-style JSON submission...")

        # The form at /u/login typically expects form-encoded POST
        # But Auth0 may also have a JSON API

        login_data = {
            "username": "test@example.com",
            "password": "wrongpassword",
            "state": state,
        }

        # Try form-encoded POST to current URL
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://identity.vwgroup.io",
            "Referer": current_url,
        }

        # The login URL should be the same /u/login with state
        async with session.post(
            current_url,
            data=login_data,
            headers=headers,
            allow_redirects=False
        ) as resp:
            print(f"  POST to {current_url[:60]}...")
            print(f"  Status: {resp.status}")
            print(f"  Headers: {dict(resp.headers)}")

            response_text = await resp.text()

            if resp.status == 302:
                print(f"  Redirect: {resp.headers.get('Location', 'N/A')}")
            else:
                print(f"  Response length: {len(response_text)}")

                # Check for error
                if "wrong" in response_text.lower() or "incorrect" in response_text.lower():
                    print("  ✓ Got authentication error (expected)")
                elif "error" in response_text.lower():
                    # Try to find specific error
                    error_match = re.search(r'"error"[:\s]*"([^"]+)"', response_text)
                    if error_match:
                        print(f"  Error: {error_match.group(1)}")


if __name__ == "__main__":
    asyncio.run(debug_login())
