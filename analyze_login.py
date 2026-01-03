#!/usr/bin/env python3
"""Analyze the login page structure."""

import asyncio
import aiohttp
import re
import sys
sys.path.insert(0, '.')

from custom_components.seat_connect.const import (
    CLIENT_ID, REDIRECT_URI, SCOPES, UI_LOCALES, AUTH_AUTHORIZE_URL
)

async def analyze_login_page():
    """Analyze the structure of the login page."""
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
            html = await resp.text()
            final_url = str(resp.url)

            print("=" * 70)
            print("Login Page Analysis")
            print("=" * 70)
            print(f"Final URL: {final_url}")
            print(f"HTML length: {len(html)}")
            print()

            # Find all forms
            forms = re.findall(r'<form[^>]*>(.*?)</form>', html, re.I | re.DOTALL)
            print(f"Found {len(forms)} form(s)")

            # Find form with action
            form_actions = re.findall(r'<form[^>]*action=["\']([^"\']+)["\']', html, re.I)
            print(f"Form actions: {form_actions}")

            # Find all input fields
            inputs = re.findall(r'<input[^>]*>', html, re.I)
            print(f"\nFound {len(inputs)} input field(s):")
            for inp in inputs:
                name = re.search(r'name=["\']([^"\']+)["\']', inp)
                type_ = re.search(r'type=["\']([^"\']+)["\']', inp)
                id_ = re.search(r'id=["\']([^"\']+)["\']', inp)
                print(f"  - name={name.group(1) if name else 'N/A':20} type={type_.group(1) if type_ else 'N/A':15} id={id_.group(1) if id_ else 'N/A'}")

            # Check for JavaScript-based login
            if "fetch(" in html or "XMLHttpRequest" in html or "ajax" in html.lower():
                print("\n⚠️ Page may use JavaScript/AJAX for login!")

            # Look for API endpoints in JavaScript
            api_urls = re.findall(r'["\']/(api|usernamepassword|co/authenticate)[^"\']*["\']', html, re.I)
            if api_urls:
                print(f"\nAPI endpoints found: {api_urls}")

            # Check for Auth0 or similar
            if "auth0" in html.lower():
                print("\n⚠️ Auth0-based authentication detected!")

            # Look for state/csrf tokens
            state_match = re.search(r'state["\s]*[:=]["\s]*["\']([^"\']+)["\']', html)
            if state_match:
                print(f"\nState token: {state_match.group(1)[:50]}...")

            # Check the current URL structure
            print(f"\n\nLogin URL path: {final_url.split('?')[0]}")

            # Save HTML for manual inspection
            with open("/tmp/vw_login_page.html", "w") as f:
                f.write(html)
            print("\nFull HTML saved to /tmp/vw_login_page.html")

            # Print a section of the HTML around login
            email_pos = html.lower().find("email")
            if email_pos > 0:
                print(f"\nHTML around 'email' field:")
                print("-" * 50)
                print(html[max(0, email_pos-200):email_pos+500])


if __name__ == "__main__":
    asyncio.run(analyze_login_page())
