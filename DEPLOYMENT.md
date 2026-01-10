# 🚀 Deployment Guide - Receipt Scanner

Complete guide to deploy your Receipt Scanner app securely.

## 🔒 Security Features Added

### Backend Security
- ✅ **Rate Limiting**: 50 requests/minute per IP (prevents API abuse)
- ✅ **Input Sanitization**: Removes dangerous characters from user input
- ✅ **File Validation**: Max 10MB images, validates file type
- ✅ **Request Validation**: Checks all receipt data for malicious payloads
- ✅ **CORS Protection**: Environment-based allowed origins
- ✅ **Pagination Limits**: Max 100 items per request

### What This Protects:
- ❌ DDoS attacks (rate limiting)
- ❌ SQL/NoSQL injection (input sanitization)
- ❌ XSS attacks (character filtering)
- ❌ File upload abuse (size/type validation)
- ❌ Unauthorized origins (CORS)

---

## 📦 Deployment Options

### Option 1: Vercel (Frontend) + Railway (Backend) - Recommended for Hackathon

**Best for:** Quick deployment, free tier, easy setup

#### Frontend on Vercel (Free)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Receipt Scanner"
   git branch -M main
   git remote add origin https://github.com/yourusername/receipt-scanner.git
   git push -u origin main
   ```

2. **Deploy to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "Import Project"
   - Connect your GitHub repo
   - Set **Root Directory**: `frontend`
   - Add Environment Variables:
     ```
     NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
     ```
   - Click "Deploy"
   - Done! Your frontend is live at `https://your-app.vercel.app`

#### Backend on Railway (Free $5 credit)

1. **Prepare for deployment**
   - Create `railway.json` (see below)
   - Create `Procfile` (see below)

2. **Deploy to Railway**
   - Go to [railway.app](https://railway.app)
   - Click "Start a New Project"
   - Click "Deploy from GitHub repo"
   - Select your repository
   - Click "Add variables" and add:
     ```
     MONGODB_URI=your_mongodb_connection_string
     GEMINI_API_KEY=your_gemini_api_key
     ENVIRONMENT=production
     ```
   - Railway will auto-detect Python and deploy
   - Copy the public URL (e.g., `https://your-backend.up.railway.app`)

3. **Update CORS**
   - In `backend/security.py`, update production origins:
   ```python
   return [
       "https://your-app.vercel.app",
   ]
   ```
   - Redeploy

---

### Option 2: Render (Both Frontend + Backend) - Free Tier

**Best for:** Everything in one place

#### Backend on Render

1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect GitHub repo
4. Settings:
   - **Name**: receipt-scanner-backend
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Environment Variables:
   ```
   MONGODB_URI=your_mongodb_connection_string
   GEMINI_API_KEY=your_gemini_api_key
   ENVIRONMENT=production
   ```
6. Click "Create Web Service"

#### Frontend on Render

1. Click "New +" → "Static Site"
2. Connect same GitHub repo
3. Settings:
   - **Name**: receipt-scanner-frontend
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `out`
4. Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://receipt-scanner-backend.onrender.com
   ```
5. Create `next.config.js` export:
   ```javascript
   module.exports = {
     output: 'export',
     images: { unoptimized: true }
   }
   ```

---

### Option 3: Heroku (Classic) - $7/month

1. Install Heroku CLI
2. Create `Procfile`:
   ```
   web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
3. Deploy:
   ```bash
   heroku create receipt-scanner-backend
   heroku config:set MONGODB_URI="your_uri"
   heroku config:set GEMINI_API_KEY="your_key"
   heroku config:set ENVIRONMENT="production"
   git push heroku main
   ```

---

## 📄 Required Deployment Files

### 1. `railway.json` (for Railway)
Create in project root:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "cd backend && pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 2. `Procfile` (for Heroku/Railway)
Create in project root:
```
web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 3. `vercel.json` (for Vercel)
Create in `frontend/`:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://your-backend.up.railway.app/api/:path*"
    }
  ]
}
```

---

## 🔐 Environment Variables Checklist

### Backend (.env - **DO NOT COMMIT**)
```env
MONGODB_URI=mongodb+srv://...
GEMINI_API_KEY=AIza...
ELEVENLABS_API_KEY=... (optional)
ENVIRONMENT=production
```

### Frontend (.env.local - **DO NOT COMMIT**)
```env
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

---

## 🛡️ Security Best Practices

### 1. Protect API Keys
- ✅ Never commit `.env` files
- ✅ Use environment variables in deployment platforms
- ✅ Rotate keys if exposed
- ✅ Use separate keys for dev/prod

### 2. Update CORS Origins
In `backend/security.py`:
```python
def get_cors_origins(environment: str) -> list:
    if environment == "production":
        return [
            "https://your-actual-domain.vercel.app",
            "https://www.yourdomain.com",
        ]
    else:
        return ["http://localhost:3000"]
```

### 3. Add MongoDB Network Access
In MongoDB Atlas:
- Go to "Network Access"
- For hackathon: Allow `0.0.0.0/0` (anywhere)
- For production: Add specific deployment IPs

### 4. Monitor Rate Limits
Current limits in `backend/security.py`:
```python
RATE_LIMIT = 50  # requests per minute per IP
```

Adjust based on expected traffic.

---

## 🧪 Test Before Deploying

### 1. Test Security Features
```bash
# Test rate limiting (should fail after 50 requests)
for i in {1..60}; do curl http://localhost:8000/api/dashboard/stats; done

# Test file size limit (should reject >10MB)
# Test image validation (should reject non-images)
```

### 2. Test CORS
```bash
# Should work from allowed origin
curl -H "Origin: http://localhost:3000" http://localhost:8000/

# Should fail from random origin
curl -H "Origin: http://evil-site.com" http://localhost:8000/
```

### 3. Test Environment Variables
```bash
# Backend should show "production" when deployed
curl https://your-backend.com/ | grep environment
```

---

## 📊 Post-Deployment Monitoring

### Check Backend Health
```bash
curl https://your-backend.com/health
# Should return: {"status": "healthy", "timestamp": "..."}
```

### Check API Docs
Visit: `https://your-backend.com/docs`

### Monitor Logs
- **Vercel**: Dashboard → Your Project → Deployments → Logs
- **Railway**: Project → Deployments → View Logs
- **Render**: Dashboard → Web Service → Logs

---

## 🚨 Troubleshooting

### Issue: CORS Error
**Fix**: Update `backend/security.py` with your frontend URL

### Issue: MongoDB Connection Failed
**Fix**: Check MongoDB Network Access allows deployment IPs

### Issue: 429 Rate Limit Error
**Fix**: Adjust `RATE_LIMIT` in `backend/security.py` or wait 1 minute

### Issue: Frontend Can't Reach Backend
**Fix**: Check `NEXT_PUBLIC_API_URL` environment variable

---

## 💰 Cost Breakdown

| Service | Free Tier | Paid |
|---------|-----------|------|
| **Vercel** (Frontend) | ✅ 100GB bandwidth | $20/mo Pro |
| **Railway** (Backend) | ✅ $5 credit | $5/mo usage |
| **Render** (Both) | ✅ 750 hrs/mo | $7/mo instance |
| **MongoDB Atlas** | ✅ 512MB storage | $9/mo M10 |
| **Gemini API** | ✅ Free tier | Pay per use |

**Total for Hackathon**: **$0** (all free tiers!)

---

## ✅ Deployment Checklist

Before deploying:
- [ ] All code committed to GitHub
- [ ] `.env` files NOT committed (check `.gitignore`)
- [ ] MongoDB Atlas cluster created
- [ ] MongoDB allows network access
- [ ] Gemini API key obtained
- [ ] Security features tested locally
- [ ] CORS origins updated for production
- [ ] Environment variables ready

After deploying:
- [ ] Frontend loads at deployed URL
- [ ] Backend `/health` endpoint responds
- [ ] Upload receipt works end-to-end
- [ ] No console errors
- [ ] Accessibility features work
- [ ] Rate limiting works

---

## 🎯 Quick Deploy for DeltaHacks (5 minutes)

**Fastest path:**

1. Push to GitHub
2. Deploy frontend to Vercel (auto-detects Next.js)
3. Deploy backend to Railway (add env vars)
4. Update CORS in `backend/security.py`
5. Test at your Vercel URL

Done! 🚀

---

## 📚 Additional Resources

- [Vercel Docs](https://vercel.com/docs)
- [Railway Docs](https://docs.railway.app)
- [Render Docs](https://render.com/docs)
- [MongoDB Atlas Docs](https://docs.atlas.mongodb.com)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)

---

**Good luck with your deployment!** 🎉
