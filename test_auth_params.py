#!/usr/bin/env python3
"""Test with additional VW Group required parameters."""

import asyncio
import aiohttp
import json

AUTH_URL = "https://identity.vwgroup.io/oidc/v1/authorize"

# Try different parameter combinations
TEST_CONFIGS = [
    {
        "name": "SEAT with ui_locales",
        "params": {
            "response_type": "code",
            "client_id": "50f215ac-4f68-4c4b-b9f3-45e21de01986@apps_vw-dilab_com",
            "redirect_uri": "seatconnect://identity-kit/login",
            "scope": "openid profile",
            "state": "test123",
            "nonce": "test456",
            "ui_locales": "de-DE de",
        }
    },
    {
        "name": "SEAT with prompt and ui_locales",
        "params": {
            "response_type": "code",
            "client_id": "50f215ac-4f68-4c4b-b9f3-45e21de01986@apps_vw-dilab_com",
            "redirect_uri": "seatconnect://identity-kit/login",
            "scope": "openid profile mbb cars",
            "state": "test123",
            "nonce": "test456",
            "ui_locales": "de-DE",
            "prompt": "login",
        }
    },
    {
        "name": "VW ID with ui_locales",
        "params": {
            "response_type": "code",
            "client_id": "a24fba63-34b3-4d43-b181-942111e6bda8@apps_vw-dilab_com",
            "redirect_uri": "weconnect://authenticated",
            "scope": "openid profile",
            "state": "test123",
            "nonce": "test456",
            "ui_locales": "de-DE de",
        }
    },
    {
        "name": "VW ID response_type=code id_token",
        "params": {
            "response_type": "code id_token",
            "client_id": "a24fba63-34b3-4d43-b181-942111e6bda8@apps_vw-dilab_com",
            "redirect_uri": "weconnect://authenticated",
            "scope": "openid profile address cars email birthdate badge mbb phone nickname dealers nationalIdentifier",
            "state": "test123",
            "nonce": "test456",
            "ui_locales": "de-DE de",
            "prompt": "login",
            "response_mode": "fragment",
        }
    },
    {
        "name": "Try We Connect ID client",
        "params": {
            "response_type": "code id_token",
            "client_id": "0fa5ae01-ebc0-4901-a2aa-4dd60572f977@apps_vw-dilab_com",
            "redirect_uri": "weconnect://authenticated",
            "scope": "openid profile address phone email birthdate cars mbb dealers nationalIdentifier",
            "state": "test123",
            "nonce": "test456",
            "ui_locales": "de-DE de",
        }
    },
    {
        "name": "We Connect ID Production",
        "params": {
            "response_type": "code id_token",
            "client_id": "9496332b-ea03-4091-a224-8c746b885068@apps_vw-dilab_com",
            "redirect_uri": "weconnect://authenticated",
            "scope": "openid profile nickname birthdate address phone email cars mbb dealers nationalIdentifier",
            "state": "test123",
            "nonce": "test456",
            "ui_locales": "de-DE de",
            "prompt": "login",
        }
    },
    {
        "name": "SEAT Mii Electric",
        "params": {
            "response_type": "code",
            "client_id": "50f215ac-4f68-4c4b-b9f3-45e21de01986@apps_vw-dilab_com",
            "redirect_uri": "seat-mii-electric://oauth-callback",
            "scope": "openid",
            "state": "test123",
            "nonce": "test456",
        }
    },
]


async def test_config(config: dict) -> None:
    """Test a configuration."""
    print(f"\n{'='*60}")
    print(f"Testing: {config['name']}")
    print(f"{'='*60}")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                AUTH_URL,
                params=config["params"],
                allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=15),
                headers={
                    "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                }
            ) as resp:
                print(f"Status: {resp.status}")
                print(f"URL: {str(resp.url)[:100]}...")

                if resp.status == 200:
                    html = await resp.text()

                    # Check for login form
                    if "emailPasswordForm" in html:
                        print("✓✓✓ LOGIN FORM FOUND! ✓✓✓")
                        # Extract form action
                        import re
                        action_match = re.search(r'action=["\']([^"\']+)["\']', html)
                        if action_match:
                            print(f"Form action: {action_match.group(1)[:80]}")
                    elif "identifier" in html.lower() or "email" in html.lower():
                        print("✓ Some form of login page")
                        print(f"Content preview: {html[:500]}")
                    elif "error" in html.lower():
                        print("✗ Error page")
                        # Try to extract error
                        import re
                        error_match = re.search(r'"error[^"]*"[^:]*:\s*"([^"]+)"', html)
                        if error_match:
                            print(f"Error: {error_match.group(1)}")
                        else:
                            print(f"Content: {html[:300]}")
                    else:
                        print(f"Unknown page (length={len(html)})")
                        print(f"Preview: {html[:400]}")

                elif resp.status == 400:
                    error_data = await resp.text()
                    try:
                        err = json.loads(error_data)
                        print(f"Error: {err.get('error_description', err)}")
                    except:
                        print(f"Response: {error_data[:200]}")
                elif resp.status == 401:
                    print("Unauthorized - Invalid client")
                else:
                    print(f"Response: {await resp.text()[:200]}")

        except Exception as e:
            print(f"Exception: {type(e).__name__}: {e}")


async def main():
    """Test all configurations."""
    print("Testing VW Group OAuth2 with additional parameters...")

    for config in TEST_CONFIGS:
        await test_config(config)
        await asyncio.sleep(0.5)  # Rate limiting

    print("\n" + "=" * 60)
    print("Tests complete.")


if __name__ == "__main__":
    asyncio.run(main())
