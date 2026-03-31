"""
Helper script to get the STORAGE_STATE value for deployment.
This outputs the storage_state.json content in a single line format
suitable for environment variables.
"""
import json

# Read the storage state file
with open('storage_state.json', 'r') as f:
    storage_state = json.load(f)

# Convert to single-line JSON (no whitespace)
env_value = json.dumps(storage_state, separators=(',', ':'))

print("=" * 80)
print("STORAGE_STATE Environment Variable Value")
print("=" * 80)
print("\nCopy the text below and paste it as the STORAGE_STATE environment variable")
print("in your deployment platform (Render, Railway, etc.):\n")
print(env_value)
print("\n" + "=" * 80)
print(f"Length: {len(env_value)} characters")
print(f"Cookies: {len(storage_state.get('cookies', []))}")
print("=" * 80)
