"""
Automatic cookie refresh service that runs in the background.
Refreshes cookies from storage_state.json every 30 minutes.
"""
import asyncio
import json
import os
from datetime import datetime

async def refresh_cookies():
    """Refresh cookies from storage_state.json file."""
    try:
        # Read the storage_state.json file
        if os.path.exists('storage_state.json'):
            with open('storage_state.json', 'r') as f:
                storage_state = json.load(f)
            
            # Update environment variable
            os.environ["STORAGE_STATE"] = json.dumps(storage_state)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Cookies refreshed from storage_state.json")
            print(f"   Loaded {len(storage_state.get('cookies', []))} cookies")
            return True
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ storage_state.json not found")
            return False
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error refreshing cookies: {e}")
        return False

async def auto_refresh_loop():
    """Run cookie refresh every 30 minutes."""
    print("=" * 60)
    print("🔄 Auto Cookie Refresh Service Started")
    print("=" * 60)
    print("Refreshing cookies every 30 minutes...")
    print()
    
    while True:
        await refresh_cookies()
        # Wait 30 minutes (1800 seconds)
        await asyncio.sleep(1800)

if __name__ == "__main__":
    asyncio.run(auto_refresh_loop())
