"""
Extract cookies using Playwright from the browser session.
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def extract_cookies():
    """Extract cookies from browser session."""
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True
        )
        
        # Get all cookies
        cookies = await context.cookies()
        
        # Filter for meta.ai cookies
        meta_cookies = {}
        for cookie in cookies:
            if 'meta.ai' in cookie.get('domain', ''):
                print(f"Cookie: {cookie['name']} = {cookie['value'][:30]}... (domain: {cookie['domain']})")
                if cookie['name'] in ['datr', 'abra_sess', 'ecto_1_sess']:
                    meta_cookies[cookie['name']] = cookie['value']
        
        await context.close()
        
        return meta_cookies


def save_cookies(cookies: dict, filepath: str = "meta_cookies.json"):
    """Save cookies to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(cookies, f, indent=2)
    print(f"\nCookies saved to {filepath}")


if __name__ == "__main__":
    cookies = asyncio.run(extract_cookies())
    
    if cookies:
        print(f"\n✅ Found {len(cookies)} Meta AI cookies:")
        for name in cookies:
            print(f"  - {name}")
        save_cookies(cookies)
    else:
        print("\n⚠️ No Meta AI cookies found. You may need to log in again.")
