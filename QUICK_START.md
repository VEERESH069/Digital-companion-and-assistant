# Quick Start Guide for Colleagues

**Question: If my colleague clones this repo, will it work locally? And on Render?**

**Answer: ✅ YES to both!** Here's everything they need to do:

---

## 📋 For Your Colleague: Local Setup (5 minutes)

### Step 1: Clone & Enter Directory
```bash
git clone https://github.com/VEERESH069/Digital-companion-and-assistant.git
cd Pre-Visit-real-time-voice-agent
```

### Step 2: Create Virtual Environment
```bash
# Windows PowerShell
python -m venv venv
.venv\Scripts\Activate.ps1

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
```bash
# Copy template
cp .env.example .env

# Edit .env and add your keys:
# OPENAI_API_KEY=sk-... (get from https://platform.openai.com/api-keys)
# CARTESIA_API_KEY=... (get from https://console.cartesia.ai/)
```

### Step 5: Run the Server
```bash
python api.py
```

✅ **Server is running at:** http://localhost:5000  
✅ **Web interface at:** http://localhost:5000/frontend.html

### Step 6: Test It!
1. Open browser to `http://localhost:5000/frontend.html`
2. Enter Patient ID (e.g., "P123456")
3. Click "Start New Session"
4. Click "🎤 Record" button
5. Speak into microphone
6. AI responds with both text and audio

---

## 🚀 For Production: Deploy on Render (10 minutes)

### Prerequisites
- GitHub account (already done ✅)
- Render.com account (free, create at https://render.com)
- API keys in .env (from Step 4 above)

### Step 1: Set Up Render Project

1. **Go to Render.com** → Sign up or log in
2. **Create New Service** → Click "New +" → "Web Service"
3. **Connect Repository**
   - Select the GitHub repository: `Digital-companion-and-assistant`
   - Branch: `main`
   - Click "Connect"

### Step 2: Configure Deployment Settings

In Render dashboard, set:

| Setting | Value |
|---------|-------|
| **Name** | pre-visit-voice-agent-api |
| **Runtime** | Python 3 |
| **Region** | Oregon (or your preference) |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn -w 2 -b 0.0.0.0:$PORT api:app` |

### Step 3: Add Environment Variables

Click **Environment** and add these variables:

```
FLASK_ENV=production
PORT=5000
PYTHON_VERSION=3.11
OPENAI_API_KEY=sk-your-actual-key-here
CARTESIA_API_KEY=your-actual-cartesia-key
DATABASE_URL=sqlite:///./conversations.db
API_KEY=your-secure-api-key
LLM_MODEL=gpt-4-turbo
APP_VERSION=1.0.0
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

⚠️ **IMPORTANT:** 
- Use actual API keys (not placeholders)
- These are private on Render and won't be exposed

### Step 4: Deploy

Click **Create Web Service**

Render will:
1. ✅ Clone the repository
2. ✅ Install dependencies from `requirements.txt`
3. ✅ Initialize the database using `alembic`
4. ✅ Start the Flask server with Gunicorn
5. ✅ Give you a live URL (e.g., `https://pre-visit-voice-agent-api.onrender.com`)

### Step 5: Test on Render

```bash
# Check health
curl https://pre-visit-voice-agent-api.onrender.com/health

# Visit web interface
https://pre-visit-voice-agent-api.onrender.com/frontend.html
```

✅ **Your colleague can now:**
- Visit the web interface from anywhere
- Record audio with their microphone
- Get AI responses
- Full conversation stored in cloud database

---

## 🔄 Continuous Deployment (Auto-Deploy)

When you push to `main` branch on GitHub:

```bash
git push origin main
```

Render automatically:
1. Pulls latest code
2. Rebuilds the app
3. Deploys to production
4. **Zero downtime** (health checks ensure smooth restart)

---

## 📊 Architecture on Render

```
┌─────────────────────┐
│   Web Browser       │
│  (Frontend.html)    │
└──────────┬──────────┘
           │ HTTPS
           ▼
┌─────────────────────────────────────┐
│  Render.com (Your Live Domain)      │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Gunicorn (2 workers)        │   │
│  │ Flask API Server            │   │
│  │  • 10+ REST endpoints       │   │
│  │  • Audio processing         │   │
│  │  • LLM integration          │   │
│  │  • Database operations      │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ SQLite Database             │   │
│  │ (Conversations stored here) │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
           │ HTTPS
           ▼
┌─────────────────────────────────────┐
│  External APIs                      │
│  • OpenAI (GPT-4 + Whisper STT)    │
│  • Cartesia (TTS - Text to Speech) │
└─────────────────────────────────────┘
```

---

## ✅ Verification Checklist

### Local Testing
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] `.env` file created with API keys
- [ ] Server starts: `python api.py`
- [ ] Health check passes: `curl http://localhost:5000/health`
- [ ] Frontend loads: Open `http://localhost:5000/frontend.html`
- [ ] Can record and process audio
- [ ] 33 tests pass: `pytest tests/test_api.py -v`

### Production on Render
- [ ] Render project created and connected to GitHub
- [ ] Environment variables set in Render dashboard
- [ ] Build succeeds (check Render build logs)
- [ ] Health check passes: `curl https://your-render-url.onrender.com/health`
- [ ] Frontend loads: Visit `https://your-render-url.onrender.com/frontend.html`
- [ ] Auto-deployment works (push to main, watch it deploy)

---

## 🆘 Troubleshooting

### "API keys not working"
```
Solution: Check .env file has correct keys without extra spaces
OPENAI_API_KEY=sk-xxx (not OPENAI_API_KEY = sk-xxx)
```

### "Audio features not working"
```
Solution: Ensure CARTESIA_API_KEY is set and valid
Check browser console (F12) for errors
```

### "Render deployment fails"
```
1. Check Render build logs (Events tab)
2. Ensure render.yaml has correct start command
3. Verify all environment variables are set
4. Try rebuilding from Render dashboard
```

### "SQLite file not persisting on Render"
```
Note: Free tier Render instances restart frequently
Upgrade to paid tier or use PostgreSQL for production
See docs/PRODUCTION_DEPLOYMENT.md for PostgreSQL setup
```

---

## 📞 Support

**For Questions:**
- Check `docs/` folder for detailed guides
- Review `PRODUCTION_DEPLOYMENT.md` for advanced config
- See `TESTING.md` for running test suite

**Debugging:**
```bash
# See detailed logs
curl -v http://localhost:5000/health

# Test specific endpoint
curl -X POST http://localhost:5000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "TEST", "language": "en"}'
```

---

## 🎉 Summary

Your colleague can now:
1. Clone the repo ✅
2. Set up locally in 5 minutes ✅
3. Test everything works ✅
4. Deploy to Render with 1 click ✅
5. Share with a live URL ✅

**Total time to production: ~15 minutes** 🚀
