"""
Cookie extractor from Playwright browser session.
Extracts cookies needed for MetaAI SDK.
"""
import json
import os
from pathlib import Path


def extract_cookies_from_session(session_dir: str = "./meta_session"):
    """
    Extract cookies from Playwright's persistent session storage.
    MetaAI SDK needs: datr, abra_sess, ecto_1_sess
    """
    cookies = {}
    
    # Playwright stores cookies in a SQLite database
    cookie_db = Path(session_dir) / "Cookies"
    
    if not cookie_db.exists():
        print(f"Cookie database not found at {cookie_db}")
        return None
    
    try:
        import sqlite3
        conn = sqlite3.connect(str(cookie_db))
        cursor = conn.cursor()
        
        # Query cookies for meta.ai
        cursor.execute("""
            SELECT name, value, host_key 
            FROM cookies 
            WHERE host_key LIKE '%meta.ai%' OR host_key LIKE '%.meta.ai%'
        """)
        
        for row in cursor.fetchall():
            name, value, host = row
            if name in ['datr', 'abra_sess', 'ecto_1_sess']:
                cookies[name] = value
                print(f"Found cookie: {name}")
        
        conn.close()
        
        # Check if we got the essential cookies
        if 'datr' in cookies and 'abra_sess' in cookies:
            print(f"✅ Successfully extracted {len(cookies)} cookies")
            return cookies
        else:
            print("⚠️  Missing essential cookies. Make sure you're logged in.")
            return None
            
    except Exception as e:
        print(f"Error extracting cookies: {e}")
        return None


def save_cookies(cookies: dict, filepath: str = "meta_cookies.json"):
    """Save cookies to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(cookies, f, indent=2)
    print(f"Cookies saved to {filepath}")


def load_cookies(filepath: str = "meta_cookies.json"):
    """Load cookies from JSON file."""
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r') as f:
        return json.load(f)


if __name__ == "__main__":
    cookies = extract_cookies_from_session()
    if cookies:
        save_cookies(cookies)
    else:
        print("Failed to extract cookies")
