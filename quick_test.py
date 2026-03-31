"""Quick test to see if the API is actually working on Render"""
import requests
import time

BASE_URL = "https://metaai-1xpj.onrender.com"

print("Testing Meta AI API on Render...")
print("=" * 60)

# Test 1: Health
print("\n1. Health Check...")
r = requests.get(f"{BASE_URL}/health")
print(f"   Status: {r.status_code}")
print(f"   Response: {r.json()}")

# Test 2: Cookie Status
print("\n2. Cookie Status...")
r = requests.get(f"{BASE_URL}/admin/cookie-status")
print(f"   Status: {r.status_code}")
print(f"   Response: {r.json()}")

# Test 3: Image Generation (with timeout)
print("\n3. Image Generation (this may take 60-120 seconds)...")
print("   Waiting...")
start = time.time()
try:
    r = requests.post(
        f"{BASE_URL}/generate/images",
        params={"prompt": "A cat", "num_images": 1, "download": "true"},
        timeout=180  # 3 minutes
    )
    elapsed = time.time() - start
    print(f"   Completed in {elapsed:.1f}s")
    print(f"   Status: {r.status_code}")
    result = r.json()
    print(f"   Success: {result.get('success')}")
    print(f"   Images: {len(result.get('image_urls', []))}")
    if result.get('image_urls'):
        print(f"   First URL: {result['image_urls'][0][:80]}...")
except requests.Timeout:
    print("   ❌ TIMEOUT after 180 seconds")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

print("\n" + "=" * 60)
