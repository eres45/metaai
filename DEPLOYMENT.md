# Meta AI Generation API - Deployment Guide

## Quick Summary

**Best Hosting Option: Render**
- Free tier available
- Docker support (can run Chromium)
- Persistent disks for downloads
- Easy GitHub integration

## Deployment Options

### 1. Render (Recommended) ⭐⭐⭐⭐⭐

**Pros:**
- ✅ Docker support with Chromium
- ✅ Persistent disks (1GB free, more paid)
- ✅ Free tier for testing
- ✅ Auto-deploy from GitHub
- ✅ Built-in HTTPS

**Cons:**
- Free tier sleeps after 15 min inactivity
- Standard plan ($7/month) for always-on

**Deploy to Render:**
1. Push code to GitHub
2. Go to https://dashboard.render.com
3. Click "New Web Service"
4. Connect your GitHub repo
5. Select "Docker" as runtime
6. Set environment variables if needed
7. Deploy!

**Files needed:**
- `Dockerfile` (already created)
- `render.yaml` (Blueprint config)

---

### 2. Railway ⭐⭐⭐⭐⭐

**Pros:**
- ✅ Easy Docker deploy
- ✅ Good free tier ($5 credit)
- ✅ Simple GitHub integration
- ✅ Automatic HTTPS

**Cons:**
- Free credit runs out quickly
- Paid plans from $5/month

**Deploy to Railway:**
1. Push code to GitHub
2. Go to https://railway.app
3. New Project → Deploy from GitHub repo
4. Railway auto-detects Dockerfile
5. Deploy!

**Files needed:**
- `Dockerfile`
- `railway.json` (config)

---

### 3. Fly.io ⭐⭐⭐⭐

**Pros:**
- ✅ Global edge deployment
- ✅ Persistent volumes
- ✅ Generous free tier
- ✅ Good for production

**Cons:**
- More complex setup
- Learning curve

**Deploy to Fly.io:**
```bash
# Install flyctl
brew install flyctl  # macOS
# or download from https://fly.io/docs/hands-on/install-flyctl/

# Login
fly auth login

# Launch app
fly launch

# Create persistent volume
fly volumes create meta_data --size 5

# Deploy
fly deploy
```

---

### 4. VPS (DigitalOcean/Linode) ⭐⭐⭐⭐

**Pros:**
- ✅ Full control
- ✅ Cheap ($5-10/month)
- ✅ Can run anything

**Cons:**
- Manual setup required
- Security/maintenance is your responsibility

**Setup on VPS:**
```bash
# SSH to your server
ssh root@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Clone repo
git clone https://github.com/yourusername/meta-ai-api.git
cd meta-ai-api

# Build and run
docker build -t meta-ai-api .
docker run -d -p 8000:8000 -v meta-data:/app/data meta-ai-api
```

---

## Not Recommended

### ❌ Cloudflare Workers
- Cannot run Chromium/Playwright
- Execution time limited to 50ms-30s
- No persistent file system

### ❌ Vercel/Netlify
- Serverless functions only
- Cannot run browsers
- Execution timeout too short

### ❌ Google Colab
- Not designed for hosting APIs
- Sessions timeout
- No persistent endpoints

---

## Pre-Deployment Checklist

- [ ] GitHub repo created
- [ ] `Dockerfile` in root
- [ ] `requirements.txt` complete
- [ ] `/health` endpoint working
- [ ] Tested locally with `docker build` + `docker run`
- [ ] Meta AI cookies valid (fresh login)
- [ ] No hardcoded paths (use environment variables)

---

## Post-Deployment

### Verify deployment:
```bash
curl https://your-app.onrender.com/health
```

### Test generation:
```bash
# Test images
curl -X POST "https://your-app.onrender.com/generate/images?prompt=test&num_images=1"

# Test videos
curl -X POST "https://your-app.onrender.com/generate/video?prompt=test"
```

### Important Notes:
1. **First request will be slow** (cold start + browser launch)
2. **Keep browser session warm** by making requests every few minutes
3. **Monitor disk usage** for downloads
4. **Set up health checks** to monitor uptime

---

## Cost Estimates

| Platform | Free Tier | Paid (Always-On) | Storage |
|----------|-----------|------------------|---------|
| Render | Yes (sleeps) | $7/month | 1GB free |
| Railway | $5 credit | ~$5-10/month | Shared |
| Fly.io | Yes | Pay per usage | 3GB free |
| VPS (DO) | No | $6/month | 25GB SSD |

---

## Recommendation

**For testing:** Render or Railway free tier
**For production:** Render Standard ($7/mo) or VPS ($5-10/mo)
**For scale:** Fly.io or AWS/GCP with load balancing

---

## Troubleshooting

### "Browser not found" error:
- Make sure `playwright install chromium` runs in Dockerfile
- Check Docker build logs

### "Session expired" error:
- Re-login to Meta AI locally
- Copy new cookies to server
- Or use headful mode once to login

### Downloads not persisting:
- Check disk/volume is mounted correctly
- Verify paths in code match mount paths

### Slow first request:
- Normal due to browser startup
- Consider keeping instance warm
- Or upgrade to always-on plan

---

## Need Help?

1. Check logs: `docker logs <container-id>`
2. Test locally first: `docker build -t test . && docker run -p 8000:8000 test`
3. Verify Meta AI login works in browser
4. Check platform-specific docs:
   - Render: https://render.com/docs
   - Railway: https://docs.railway.app
   - Fly.io: https://fly.io/docs
