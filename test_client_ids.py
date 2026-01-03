#!/usr/bin/env python3
"""Test different Client IDs to find one that works."""

import asyncio
import aiohttp

# Known Client IDs from VW Group apps
CLIENT_IDS = [
    # SEAT Connect
    ("SEAT Connect (new)", "9dcc70f0-8e79-423a-a3fa-4065d99088b4@apps_vw-dilab_com"),
    ("SEAT Connect (old)", "50f215ac-4f68-4c4b-b9f3-45e21de01986@apps_vw-dilab_com"),

    # Cupra Connect
    ("Cupra Connect", "3c756d46-f1ba-4d78-9f9a-cff0d5292d51@apps_vw-dilab_com"),

    # Volkswagen
    ("VW We Connect ID", "a24fba63-34b3-4d43-b181-942111e6bda8@apps_vw-dilab_com"),
    ("VW ID", "0fa5ae01-ebc0-4901-a2aa-4dd60572f977@apps_vw-dilab_com"),
    ("VW Connect", "7f045eee-7003-4379-9968-9355ed2adb06@apps_vw-dilab_com"),

    # Skoda
    ("Skoda Connect", "7f045eee-7003-4379-9968-9355ed2adb06@apps_vw-dilab_com"),

    # Generic/Test
    ("VW Web", "33d881c3-9844-4c7b-8c88-5b3ce5455fb1@apps_vw-dilab_com"),

    # SEAT/Cupra more recent
    ("SEAT ID", "eb98d9c2-6ee6-4557-8934-0f51e6ce8f74@apps_vw-dilab_com"),
    ("SEAT Connect 2024", "1bb1b tried-4c4b-b9f3-45e21de01986@apps_vw-dilab_com"),
]


async def test_client_id(name: str, client_id: str) -> tuple[str, str, int]:
    """Test if a client_id works."""
    auth_url = "https://identity.vwgroup.io/oidc/v1/authorize"
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": "seatconnect://identity-kit/login",
        "scope": "openid profile",
        "state": "test123",
        "nonce": "test456",
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                auth_url,
                params=params,
                allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=10),
                headers={
                    "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                }
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    if "emailPasswordForm" in html or "email" in html.lower():
                        return (name, client_id, 200)
                return (name, client_id, resp.status)
        except Exception as e:
            return (name, client_id, -1)


async def main():
    """Test all client IDs."""
    print("Testing VW Group Client IDs for SEAT Connect...")
    print("=" * 70)

    tasks = [test_client_id(name, cid) for name, cid in CLIENT_IDS]
    results = await asyncio.gather(*tasks)

    working = []
    for name, client_id, status in results:
        status_str = "✓ WORKS" if status == 200 else f"✗ {status}"
        print(f"{status_str:12} | {name:25} | {client_id[:50]}")
        if status == 200:
            working.append((name, client_id))

    print("\n" + "=" * 70)
    if working:
        print(f"\n✓ Found {len(working)} working Client ID(s):")
        for name, cid in working:
            print(f"  - {name}: {cid}")
    else:
        print("\n✗ No working Client IDs found.")
        print("\nTrying with different redirect URIs...")


if __name__ == "__main__":
    asyncio.run(main())
