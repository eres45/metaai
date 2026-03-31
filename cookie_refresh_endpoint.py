"""
Add this to main.py to allow updating cookies via API endpoint
This way you don't need to manually update environment variables in Render
"""

# Add this import at the top of main.py
import os
import json

# Add these endpoints to main.py

@app.post("/admin/update-cookies")
async def update_cookies(
    cookies_json: str = Query(..., description="New storage_state JSON")
):
    """
    Update cookies without redeploying.
    Send the new storage_state JSON as a query parameter.
    
    Example:
    POST /admin/update-cookies?cookies_json={"cookies":[...]}
    """
    try:
        # Validate JSON
        storage_state = json.loads(cookies_json)
        
        # Update environment variable (for current session)
        os.environ["STORAGE_STATE"] = cookies_json
        
        # Optionally save to file for persistence
        with open("storage_state.json", "w") as f:
            json.dump(storage_state, f, indent=2)
        
        return {
            "success": True,
            "message": "Cookies updated successfully",
            "cookies_count": len(storage_state.get("cookies", []))
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/admin/cookie-status")
async def cookie_status():
    """Check current cookie status and when they might expire."""
    storage_json = os.environ.get("STORAGE_STATE")
    
    if not storage_json:
        return {
            "cookies_loaded": False,
            "message": "No cookies found"
        }
    
    try:
        storage_state = json.loads(storage_json)
        cookies = storage_state.get("cookies", [])
        
        return {
            "cookies_loaded": True,
            "cookies_count": len(cookies),
            "cookie_names": [c.get("name") for c in cookies],
            "storage_state_length": len(storage_json),
            "note": "Cookies typically expire after days/weeks. Monitor for 'login required' errors."
        }
    except:
        return {
            "cookies_loaded": False,
            "error": "Failed to parse STORAGE_STATE"
        }
