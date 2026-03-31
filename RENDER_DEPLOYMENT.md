# 🚀 Deploy to Render - Complete Guide

## Prerequisites

✅ You already have:
- Working API locally
- `storage_state.json` with valid cookies
- All files in the repository

---

## Step-by-Step Deployment

### 1. Push to GitHub

```bash
cd metaai
git init
git add .
git commit -m "Initial commit - Meta AI API"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/metaai.git
git push -u origin main
```

### 2. Create Render Account

1. Go to https://render.com
2. Sign up with GitHub
3. Authorize Render to access your repositories

### 3. Create New Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Select the `metaai` repository

### 4. Configure Service

**Basic Settings:**
- **Name:** `meta-ai-api` (or your choice)
- **Region:** Choose closest to you
- **Branch:** `main`
- **Runtime:** `Docker`
- **Plan:** `Standard` ($7/month) or `Free` (sleeps after 15 min)

**Advanced Settings:**
- **Docker Command:** (leave default, uses Dockerfile CMD)
- **Health Check Path:** `/health`

### 5. Set Environment Variables

This is the CRITICAL step! Click **"Environment"** tab and add:

**Variable Name:** `STORAGE_STATE`

**Value:** Copy the ENTIRE content of your `storage_state.json` file:

```json
{"cookies":[{"name":"datr","value":"da2paY4EnxHlKzo5Hb3EfoRb","domain":".meta.ai","path":"/","expires":-1,"httpOnly":true,"secure":true,"sameSite":"None"},{"name":"ecto_1_sess","value":"4e1e56cf-c9fd-4032-856a-d9acf4f1acfd.v1%3AjqmFOJHz0y0rtzBBNcVmRjM-IANBEojXNJManhUTUfcQxKFpw-mrNPLmfJDfNDTNCOGwkBCHzgJDAFDeB7f0KVwekF68naBS0vtHm8Y7zG95QDw-Xx8wyCIkp5rq5kzAA6QT2u68p5dKj99lt82ouxQisVh00T4HEWwR6qxhAllb87xq1rPiGuiXL45ontxorbqvSYpwqKbSiTPEkaxnFUeuDUoQAjhqX7kBdIxZhTigfeVRszvTmojOWHjAXATQXmYZD-M90o1LJWrY51Ln-9CqM3cbHE5E1HuoxENAIamo1qwKhotjmnkAypmXqLnPNMcwyC6E7EmCbFAwjXVxnisjNthGTx2FEDnLx1xvl-28KK0e_BLdyeeO_kjlCqDCgsSpRsaYVHT8YPzfdgEekf0n7HdOqxCmDztXPTIUHq_iViHBCV7mGB-W9ZJufL5e-keZE0d7SVdbG1HG3ThyMsApaO-iND3UTkDCFBs9ueS0IIfPFFmaXajRp71PthcO%3Ap3W_F9dC6TI-5zTo%3A7XX_RsYuAdX-HKVsfCc4gg.v162v3JxpBTp5vlVQykwX3r20pbTgvgRpCBkm3nQnvo","domain":".meta.ai","path":"/","expires":-1,"httpOnly":true,"secure":true,"sameSite":"None"}]}
```

**Important:** 
- Paste it as ONE LINE (no line breaks)
- Include the entire JSON structure
- Don't add quotes around it

### 6. Add Persistent Disk (Optional but Recommended)

1. Go to **"Disks"** tab
2. Click **"Add Disk"**
3. **Name:** `meta-data`
4. **Mount Path:** `/app/data`
5. **Size:** 1GB (free) or more

This keeps your downloaded images/videos even after restarts.

### 7. Deploy!

1. Click **"Create Web Service"**
2. Wait 5-10 minutes for build
3. Watch the logs for any errors

---

## Verify Deployment

Once deployed, you'll get a URL like: `https://meta-ai-api.onrender.com`

### Test Health Check
```bash
curl https://meta-ai-api.onrender.com/health
```

Expected response:
```json
{"status":"ok","service":"Meta AI Generation API"}
```

### Test Image Generation
```bash
curl -X POST "https://meta-ai-api.onrender.com/generate/images?prompt=A+cat+in+space&num_images=2&download=true"
```

### Test Video Generation
```bash
curl -X POST "https://meta-ai-api.onrender.com/generate/video?prompt=A+dancing+robot&download=true"
```

---

## Important Notes

### ⚠️ Cookie Expiration
Meta AI cookies expire after some time. When you see authentication errors:

1. Login to Meta AI in your browser again
2. Run `py setup_cookies.py` locally to regenerate `storage_state.json`
3. Update the `STORAGE_STATE` environment variable in Render dashboard
4. Redeploy or restart the service

### 🐌 First Request is Slow
- First request takes 30-60 seconds (cold start + browser launch)
- Subsequent requests are faster
- Free tier: Service sleeps after 15 min inactivity
- Standard tier: Always running, faster responses

### 💾 Downloads
- Images/videos are saved to `/app/data/downloads/` if disk is mounted
- Without persistent disk, downloads are lost on restart
- Use the `/list-downloads` endpoint to see what's available

### 🔒 Security Recommendations
1. Add API key authentication (not included by default)
2. Rate limiting to prevent abuse
3. CORS configuration if using from web apps
4. Monitor usage and costs

---

## Troubleshooting

### Build Fails
**Error:** "Playwright browser not found"
- Check Dockerfile has `RUN playwright install chromium`
- Verify all system dependencies are installed

**Error:** "Requirements not found"
- Make sure `requirements.txt` is in the root directory
- Check file is committed to Git

### Runtime Errors
**Error:** "No cookies loaded"
- Verify `STORAGE_STATE` environment variable is set
- Check the JSON is valid (use a JSON validator)
- Make sure there are no extra quotes or line breaks

**Error:** "Login required"
- Cookies expired - get fresh cookies from Meta AI
- Update `STORAGE_STATE` in Render dashboard

### Slow Performance
- Upgrade from Free to Standard plan ($7/month)
- Free tier sleeps after 15 min inactivity
- Consider using a VPS for better performance

---

## Cost Breakdown

### Free Tier
- ✅ 750 hours/month
- ✅ Sleeps after 15 min inactivity
- ✅ 1GB persistent disk
- ⚠️ Slow cold starts (30-60s)

### Standard Tier ($7/month)
- ✅ Always running
- ✅ Faster responses
- ✅ 1GB disk included
- ✅ No cold starts

### Additional Costs
- Extra disk space: $0.25/GB/month
- Bandwidth: Usually included

---

## Alternative: Railway Deployment

If Render doesn't work, try Railway:

1. Go to https://railway.app
2. New Project → Deploy from GitHub
3. Select your repository
4. Add environment variable: `STORAGE_STATE` (same as above)
5. Deploy!

Railway auto-detects the Dockerfile and deploys.

---

## Quick Setup Script

Create this file locally to quickly get your STORAGE_STATE value:

```bash
# get_storage_state.sh
cat storage_state.json | tr -d '\n' | tr -d ' '
```

Run it:
```bash
bash get_storage_state.sh
```

Copy the output and paste it as the `STORAGE_STATE` environment variable in Render.

---

## Success Checklist

- [ ] Repository pushed to GitHub
- [ ] Render account created
- [ ] Web service created with Docker runtime
- [ ] `STORAGE_STATE` environment variable set
- [ ] Service deployed successfully
- [ ] Health check returns 200 OK
- [ ] Image generation works
- [ ] Video generation works

---

## Next Steps

Once deployed:
1. Test all endpoints thoroughly
2. Monitor logs for errors
3. Set up monitoring/alerts
4. Consider adding authentication
5. Document your API for users
6. Share your API URL!

**Your API will be live at:** `https://your-service-name.onrender.com`

🎉 Congratulations! Your Meta AI API is now deployed and accessible from anywhere!
