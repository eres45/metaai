# 🍪 Cookie Management Guide

## How Often Do Cookies Expire?

Meta AI cookies typically last **1-4 weeks** depending on:
- Your Meta account settings
- Session activity
- Security policies

You'll know cookies expired when you see:
- `"success": false` in API responses
- `"login required"` errors in logs
- Empty `image_urls` or `video_urls` arrays

---

## Two Ways to Update Cookies

### Method 1: Automatic Update via API (Recommended) ⭐

This method lets you update cookies WITHOUT touching the Render dashboard!

**Step 1:** Get fresh cookies locally
```bash
# Login to Meta AI in your browser first
py setup_cookies.py
```

**Step 2:** Push to Render automatically
```bash
py update_remote_cookies.py
```

That's it! The script will:
- Read your local `storage_state.json`
- Send it to your Render service
- Update cookies without redeploying

**Check cookie status anytime:**
```bash
py update_remote_cookies.py status
```

Or via curl:
```bash
curl https://metaai-1xpj.onrender.com/admin/cookie-status
```

---

### Method 2: Manual Update via Render Dashboard

**Step 1:** Get fresh cookies
```bash
py setup_cookies.py
py get_env_value.py
```

**Step 2:** Update on Render
1. Go to https://dashboard.render.com
2. Select your service
3. Go to "Environment" tab
4. Update `STORAGE_STATE` variable
5. Save (service will redeploy)

---

## When to Update Cookies

### Signs You Need Fresh Cookies:

✅ **Check these endpoints:**
```bash
# Health check (should always work)
curl https://metaai-1xpj.onrender.com/health

# Cookie status
curl https://metaai-1xpj.onrender.com/admin/cookie-status

# Test generation
curl -X POST "https://metaai-1xpj.onrender.com/generate/images?prompt=test&num_images=1"
```

❌ **If you see:**
- `"success": false`
- `"cookies_loaded": false`
- `"login required"` in error messages
- Empty results

→ Time to update cookies!

---

## Complete Cookie Refresh Workflow

### Every 1-4 Weeks (When Cookies Expire):

**1. Login to Meta AI**
   - Open browser
   - Go to https://www.meta.ai
   - Login with your account
   - Generate a test image to confirm login works

**2. Extract Fresh Cookies**
   ```bash
   cd metaai
   py setup_cookies.py
   ```
   This creates a new `storage_state.json` with fresh cookies

**3. Update Render Service**
   ```bash
   py update_remote_cookies.py
   ```
   This pushes the new cookies to your deployed service

**4. Test the API**
   ```bash
   curl -X POST "https://metaai-1xpj.onrender.com/generate/images?prompt=A+cat&num_images=1"
   ```

**Total time:** ~2 minutes

---

## Automation Ideas

### Option 1: Scheduled Cookie Refresh

Create a scheduled task (Windows Task Scheduler, cron, etc.) to:
1. Check cookie status weekly
2. Alert you when cookies are about to expire
3. Remind you to refresh

### Option 2: Monitoring Script

```python
# monitor_cookies.py
import requests
import time

RENDER_URL = "https://metaai-1xpj.onrender.com"

while True:
    # Test generation
    response = requests.post(
        f"{RENDER_URL}/generate/images",
        params={"prompt": "test", "num_images": 1}
    )
    
    result = response.json()
    
    if not result.get("success"):
        print("⚠️ ALERT: Cookies may have expired!")
        print("Run: py update_remote_cookies.py")
        # Send email/notification here
    else:
        print("✅ Cookies still valid")
    
    # Check every 24 hours
    time.sleep(86400)
```

### Option 3: Webhook Notifications

Add to your API to send you a notification when cookies fail:
- Email alert
- Discord webhook
- Slack notification
- SMS via Twilio

---

## API Endpoints for Cookie Management

### Check Cookie Status
```bash
GET /admin/cookie-status
```

**Response:**
```json
{
  "cookies_loaded": true,
  "cookies_count": 2,
  "cookie_names": ["datr", "ecto_1_sess"],
  "storage_state_length": 924,
  "note": "Cookies typically expire after days/weeks..."
}
```

### Update Cookies
```bash
POST /admin/update-cookies?cookies_json={"cookies":[...]}
```

**Response:**
```json
{
  "success": true,
  "message": "Cookies updated successfully",
  "cookies_count": 2
}
```

---

## Troubleshooting

### "Cookies not updating"
- Make sure you're logged into Meta AI in your browser
- Run `py setup_cookies.py` to extract fresh cookies
- Verify `storage_state.json` was created
- Check the file has 2 cookies (datr and ecto_1_sess)

### "Still getting login errors after update"
- Wait 1-2 minutes after updating (service needs to restart)
- Try the update again
- Check if Meta AI requires 2FA or additional verification
- Try logging out and back into Meta AI

### "Script can't connect to Render"
- Check your internet connection
- Verify the Render URL is correct
- Make sure the service is running (not sleeping)
- Check Render dashboard for any errors

---

## Best Practices

✅ **Do:**
- Keep `meta_cookies.json` and `storage_state.json` in `.gitignore`
- Update cookies proactively (don't wait for failures)
- Test after updating cookies
- Monitor your API regularly

❌ **Don't:**
- Share your cookies publicly (they're like passwords!)
- Commit cookies to public GitHub repos
- Use expired cookies (they won't work)
- Forget to test after updating

---

## Summary

**Frequency:** Update cookies every 1-4 weeks (when they expire)

**Quick Update:**
```bash
py setup_cookies.py
py update_remote_cookies.py
```

**Time Required:** ~2 minutes

**Automation:** Use the API endpoint to update without Render dashboard access

**Monitoring:** Check `/admin/cookie-status` regularly

---

## Need Help?

If cookies keep expiring quickly:
1. Check if Meta AI has security restrictions on your account
2. Try using a different browser
3. Ensure you're fully logged in (not just visiting the site)
4. Consider using a dedicated Meta account for the API

Your API will work perfectly as long as cookies are fresh! 🚀
