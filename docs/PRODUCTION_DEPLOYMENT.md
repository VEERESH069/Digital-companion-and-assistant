# Production Deployment Guide

## 📋 Pre-Requisites

- Python 3.11+
- Git & GitHub account
- Render.com account
- OpenAI API key
- Cartesia API key

---

## 🚀 LOCAL TESTING & SETUP

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your actual API keys
# IMPORTANT: Never commit .env to Git!
```

**Required values in `.env`:**
```
OPENAI_API_KEY=sk-your-openai-key
CARTESIA_API_KEY=your-cartesia-key
API_KEY=your-secure-api-key
DATABASE_URL=sqlite:///./conversations.db  # Local SQLite
FLASK_ENV=development
```

### 3. Initialize Database

```bash
# Database tables are auto-created on first run
# Or manually:
python -c "from database import init_db; db = init_db(); print('Database initialized')"
```

### 4. Run API Server Locally

```bash
# Start Flask development server
python api.py

# Or with Gunicorn (production-like):
gunicorn -w 2 -b 0.0.0.0:5000 api:app
```

Server will be available at: `http://localhost:5000`

### 5. Test Frontend

```bash
# Open in browser:
# File: frontend.html
# Or serve locally:
python -m http.server 8000
# Then visit: http://localhost:8000/frontend.html
```

### 6. Test API Endpoints

```bash
# Health check
curl http://localhost:5000/health

# Get API info
curl http://localhost:5000/api/info

# Create new session
curl -X POST http://localhost:5000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "P123456", "language": "en"}'

# Send message (replace SESSION_ID)
curl -X POST http://localhost:5000/api/sessions/SESSION_ID/messages \
  -H "Content-Type: application/json" \
  -d '{"role": "user", "content": "I have a toothache", "turn_number": 1}'

# Get conversation history
curl http://localhost:5000/api/sessions/SESSION_ID/messages

# Export as JSON
curl http://localhost:5000/api/sessions/SESSION_ID/export

# End session
curl -X PUT http://localhost:5000/api/sessions/SESSION_ID \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

---

## 📦 PROJECT STRUCTURE

```
Pre-Visit-real-time-voice-agent/
├── api.py                          # Flask API server ✨ NEW
├── models.py                       # Database models ✨ NEW
├── database.py                     # Database layer ✨ NEW
├── frontend.html                   # Web UI ✨ NEW
├── requirements.txt                # Dependencies (UPDATED)
├── Dockerfile                      # Production container (UPDATED)
├── render.yaml                     # Render deployment config ✨ NEW
├── .env.example                    # Environment template (UPDATED)
├── .github/
│   └── workflows/
│       └── deploy.yml              # CI/CD pipeline ✨ NEW
├── previsit_agent/
│   ├── pdf.py                      # PDF generation (MODIFIED - disabled)
│   ├── conversation.py             # Conversation management
│   ├── llm.py                      # LLM engine
│   ├── tts.py                      # Text-to-speech
│   └── ...
└── docs/
    └── PRODUCTION_DEPLOYMENT.md    # This file
```

---

## 🌐 RENDER DEPLOYMENT

### Step 1: Push to GitHub

```bash
git add .
git commit -m "feat: production-ready web deployment"
git push origin main
```

### Step 2: Create Render Service

1. Go to [render.com](https://render.com)
2. Sign up / Log in
3. Create new **Web Service**
4. Connect GitHub repository
5. Select this repository

### Step 3: Configure Service

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
gunicorn -w 2 -b 0.0.0.0:$PORT api:app
```

**Environment Variables:** (Set in Render Dashboard)
```
FLASK_ENV=production
OPENAI_API_KEY=sk-your-key
CARTESIA_API_KEY=your-key
API_KEY=your-secure-key
DATABASE_URL=sqlite:///./conversations.db
LLM_MODEL=gpt-4-turbo
CORS_ORIGINS=https://yourdomain.com
```

### Step 4: Add Environment Variables

Go to **Settings → Environment**:
- Add all required keys from `.env.example`
- Keep secrets (API keys) private
- Do NOT add `.env` file

### Step 5: Deploy

1. Click **Deploy**
2. Monitor build logs
3. Once deployed, your API is live at: `https://your-service-name.onrender.com`

### Step 6: Add Custom Domain (Optional)

Go to **Settings → Custom Domain**:
- Add your domain (e.g., `api.yourdomain.com`)
- Follow DNS setup instructions

---

## 🗄️ DATABASE

### SQLite (Free Tier - Default)
- File-based: `conversations.db`
- No setup needed
- Works immediately
- Limited to ~100MB

### PostgreSQL (Paid Tier)
```bash
# To switch to PostgreSQL:
# 1. In Render dashboard, create Postgres database
# 2. Copy connection string
# 3. Set DATABASE_URL in environment
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

---

## 📊 MONITORING & LOGS

### View Logs in Render

```bash
# In Render Dashboard → Logs
# Or via Render CLI:
render logs YOUR_SERVICE_NAME
```

### Check Health

```bash
curl https://your-service.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "ok",
  "version": "1.0.0"
}
```

---

## 🔍 TROUBLESHOOTING

### Issue: "ModuleNotFoundError: No module named 'api'"

**Solution:** Ensure `api.py` is in root directory, not in a subfolder.

### Issue: Database not initializing

**Solution:** Check logs for SQL errors:
```bash
# Verify database models
python -c "from models import Base; print(Base.metadata.tables.keys())"
```

### Issue: API keys not working

**Solution:** 
1. Check `.env` file has correct keys
2. Verify keys in Render environment variables
3. Test API key format (OpenAI keys start with `sk-`)

### Issue: CORS errors from frontend

**Solution:** Update `CORS_ORIGINS` in environment:
```
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Issue: Out of memory / Disk full

**Solution:** 
1. Clear old sessions: `db.clear_abandoned_sessions(hours=24)`
2. Upgrade to paid Render plan with more resources
3. Use PostgreSQL instead of SQLite

---

## 🔐 SECURITY CHECKLIST

- [ ] `.env` file NOT committed to Git
- [ ] API keys rotated regularly
- [ ] CORS origins restricted to your domains
- [ ] Non-root user in Docker (already configured)
- [ ] Health checks enabled
- [ ] Logging configured
- [ ] Database encryption enabled (if using PostgreSQL)
- [ ] Rate limiting configured (optional)

---

## 📈 SCALING CONSIDERATIONS

### Free Tier Limits
- 1 instance (no auto-scaling)
- 512 MB RAM
- 1 GB disk
- SQLite max ~100MB

### When to Upgrade
- > 100 concurrent sessions → **Starter plan** ($7/month)
- > 1000 requests/min → **Standard plan** ($25/month)
- Need persistent database → **PostgreSQL add-on** ($15/month)

---

## 🔄 CI/CD PIPELINE

### Automatic Deployment on Push to Main

The `.github/workflows/deploy.yml` workflow:

1. ✅ Runs tests on every push
2. ✅ Checks Python syntax
3. ✅ Verifies database models
4. ✅ Auto-deploys to Render on main branch
5. ✅ Notifies Slack (if configured)

### Manual Deployment

```bash
# If automatic deployment fails:
git push origin main  # Trigger workflow
# Or in Render dashboard: Settings → Deploy
```

---

## 📞 SUPPORT & RESOURCES

- **Render Docs:** https://render.com/docs
- **Flask Docs:** https://flask.palletsprojects.com/
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **OpenAI API Docs:** https://platform.openai.com/docs/

---

## 🎯 NEXT STEPS

1. **Local Testing** ✅ Test all endpoints locally
2. **Push to GitHub** → Commit and push code
3. **Deploy to Render** → Create service and deploy
4. **Monitor** → Check logs and health
5. **Scale** → Upgrade if needed

---

**Last Updated:** May 31, 2026
**Version:** 1.0.0
