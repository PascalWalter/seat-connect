#!/usr/bin/env python3
"""Test Client ID + Redirect URI combinations."""

import asyncio
import aiohttp

# Client ID + Redirect URI combinations from actual apps
COMBINATIONS = [
    # SEAT Connect
    {
        "name": "SEAT Connect",
        "client_id": "50f215ac-4f68-4c4b-b9f3-45e21de01986@apps_vw-dilab_com",
        "redirect_uri": "seatconnect://identity-kit/login",
    },
    {
        "name": "SEAT Connect v2",
        "client_id": "9dcc70f0-8e79-423a-a3fa-4065d99088b4@apps_vw-dilab_com",
        "redirect_uri": "seatconnect://identity-kit/login",
    },
    # Cupra
    {
        "name": "Cupra Connect",
        "client_id": "3c756d46-f1ba-4d78-9f9a-cff0d5292d51@apps_vw-dilab_com",
        "redirect_uri": "cupraconnect://identity-kit/login",
    },
    # VW ID
    {
        "name": "VW ID",
        "client_id": "a24fba63-34b3-4d43-b181-942111e6bda8@apps_vw-dilab_com",
        "redirect_uri": "weconnect://authenticated",
    },
    {
        "name": "VW We Connect",
        "client_id": "7f045eee-7003-4379-9968-9355ed2adb06@apps_vw-dilab_com",
        "redirect_uri": "carnet://identity-kit/login",
    },
    # Skoda
    {
        "name": "Skoda Connect",
        "client_id": "7f045eee-7003-4379-9968-9355ed2adb06@apps_vw-dilab_com",
        "redirect_uri": "skodaconnect://oidc.login",
    },
    # SEAT with different URIs
    {
        "name": "SEAT myS",
        "client_id": "50f215ac-4f68-4c4b-b9f3-45e21de01986@apps_vw-dilab_com",
        "redirect_uri": "seat-mys://login-callback",
    },
    # Generic We Connect
    {
        "name": "We Connect Generic",
        "client_id": "0fa5ae01-ebc0-4901-a2aa-4dd60572f977@apps_vw-dilab_com",
        "redirect_uri": "weconnect://authenticated",
    },
    # Try with simpler scopes
    {
        "name": "SEAT minimal",
        "client_id": "50f215ac-4f68-4c4b-b9f3-45e21de01986@apps_vw-dilab_com",
        "redirect_uri": "seatconnect://identity-kit/login",
        "scope": "openid",
    },
]


async def test_combo(combo: dict) -> dict:
    """Test a client_id + redirect_uri combination."""
    auth_url = "https://identity.vwgroup.io/oidc/v1/authorize"
    params = {
        "response_type": "code",
        "client_id": combo["client_id"],
        "redirect_uri": combo["redirect_uri"],
        "scope": combo.get("scope", "openid profile"),
        "state": "test123",
        "nonce": "test456",
    }

    result = {**combo, "status": -1, "message": ""}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                auth_url,
                params=params,
                allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=15),
                headers={
                    "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 6) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "de-DE,de;q=0.9",
                }
            ) as resp:
                result["status"] = resp.status
                result["final_url"] = str(resp.url)

                if resp.status == 200:
                    html = await resp.text()
                    if "emailPasswordForm" in html or "identifier" in html.lower():
                        result["message"] = "LOGIN FORM FOUND!"
                    elif "error" in html.lower():
                        result["message"] = "Error page"
                    else:
                        result["message"] = f"Unknown page (len={len(html)})"
                elif resp.status == 401:
                    result["message"] = "Unauthorized (invalid client)"
                elif resp.status == 400:
                    text = await resp.text()
                    result["message"] = f"Bad request: {text[:100]}"
                else:
                    result["message"] = f"HTTP {resp.status}"

        except Exception as e:
            result["message"] = f"Error: {type(e).__name__}: {str(e)[:50]}"

    return result


async def main():
    """Test all combinations."""
    print("Testing VW Group OAuth2 Client configurations...")
    print("=" * 80)

    for combo in COMBINATIONS:
        result = await test_combo(combo)

        status_icon = "✓" if result["status"] == 200 and "LOGIN" in result.get("message", "") else "✗"
        print(f"\n{status_icon} {result['name']}")
        print(f"  Client: {result['client_id'][:50]}...")
        print(f"  Redirect: {result['redirect_uri']}")
        print(f"  Status: {result['status']} - {result['message']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
