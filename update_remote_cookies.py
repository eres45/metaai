"""
Script to update cookies on your deployed Render service without manual dashboard access.
Run this locally when cookies expire.
"""
import json
import requests
import sys

# Your Render service URL
RENDER_URL = "https://metaai-1xpj.onrender.com"

def update_cookies():
    """Update cookies on the remote server."""
    
    # Read local storage_state.json
    try:
        with open('storage_state.json', 'r') as f:
            storage_state = json.load(f)
    except FileNotFoundError:
        print("❌ Error: storage_state.json not found!")
        print("Run 'py setup_cookies.py' first to generate it.")
        sys.exit(1)
    
    # Convert to single-line JSON
    cookies_json = json.dumps(storage_state, separators=(',', ':'))
    
    print("=" * 80)
    print("🔄 Updating cookies on Render...")
    print("=" * 80)
    print(f"Service: {RENDER_URL}")
    print(f"Cookies: {len(storage_state.get('cookies', []))} cookies")
    print()
    
    # Send update request
    try:
        response = requests.post(
            f"{RENDER_URL}/admin/update-cookies",
            params={"cookies_json": cookies_json},
            timeout=30
        )
        
        result = response.json()
        
        if result.get("success"):
            print("✅ SUCCESS! Cookies updated on server")
            print(f"   Cookies loaded: {result.get('cookies_count')}")
            print()
            print("Your API should now work with the new cookies!")
        else:
            print("❌ FAILED to update cookies")
            print(f"   Error: {result.get('error')}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        sys.exit(1)
    
    print("=" * 80)


def check_status():
    """Check current cookie status on server."""
    print("=" * 80)
    print("🔍 Checking cookie status on Render...")
    print("=" * 80)
    
    try:
        response = requests.get(f"{RENDER_URL}/admin/cookie-status", timeout=10)
        status = response.json()
        
        print(f"Cookies loaded: {status.get('cookies_loaded')}")
        print(f"Cookies count: {status.get('cookies_count')}")
        print(f"Cookie names: {status.get('cookie_names')}")
        print(f"Storage length: {status.get('storage_state_length')} characters")
        print()
        print(f"Note: {status.get('note', '')}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    
    print("=" * 80)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        check_status()
    else:
        print()
        print("This script will update cookies on your Render deployment.")
        print()
        print("Steps:")
        print("1. Login to Meta AI in your browser")
        print("2. Run 'py setup_cookies.py' to extract fresh cookies")
        print("3. Run this script to push them to Render")
        print()
        
        response = input("Continue? (y/n): ")
        if response.lower() == 'y':
            update_cookies()
        else:
            print("Cancelled.")
