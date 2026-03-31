"""Convert meta_cookies.json to STORAGE_STATE format and set environment variable."""
import json
import os

# Load cookies
with open('meta_cookies.json', 'r') as f:
    cookies_dict = json.load(f)

# Convert to Playwright storage state format
storage_state = {
    "cookies": []
}

for name, value in cookies_dict.items():
    storage_state["cookies"].append({
        "name": name,
        "value": value,
        "domain": ".meta.ai",
        "path": "/",
        "expires": -1,
        "httpOnly": True,
        "secure": True,
        "sameSite": "None"
    })

# Save to file for reference
with open('storage_state.json', 'w') as f:
    json.dump(storage_state, f, indent=2)

print(f"✅ Converted {len(storage_state['cookies'])} cookies to storage_state.json")
print(f"\nTo use these cookies, set the environment variable:")
print(f"\nWindows (CMD):")
print(f'set STORAGE_STATE={json.dumps(storage_state)}')
print(f"\nWindows (PowerShell):")
print(f'$env:STORAGE_STATE=\'{json.dumps(storage_state)}\'')
print(f"\nOr use the storage_state.json file directly in your code.")
