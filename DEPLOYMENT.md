# Deployment Guide - Physical AI Textbook

This guide covers deploying the complete Physical AI Textbook platform.

## Architecture Overview

- **Frontend**: Docusaurus static site → GitHub Pages (free)
- **Backend**: FastAPI API → Render (free tier)
- **Database**: Neon PostgreSQL (free tier)
- **Vector DB**: Qdrant Cloud (free tier)
- **LLM**: Google Gemini (free) or OpenAI (paid)

---

## Step 1: Set Up External Services

### 1.1 Neon PostgreSQL (Database)

1. Go to [neon.tech](https://neon.tech) and sign up
2. Create a new project
3. Copy the connection string (looks like `postgresql://user:pass@host/db?sslmode=require`)
4. Save this as `DATABASE_URL`

### 1.2 Qdrant Cloud (Vector Database)

1. Go to [cloud.qdrant.io](https://cloud.qdrant.io) and sign up
2. Create a free cluster
3. Copy the cluster URL (e.g., `https://xxx-xxx.aws.cloud.qdrant.io`)
4. Generate an API key from the cluster dashboard
5. Save these as `QDRANT_URL` and `QDRANT_API_KEY`

### 1.3 LLM Provider (Choose One)

**Option A: Google Gemini (FREE - Recommended)**
1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Create an API key
3. Save as `GEMINI_API_KEY`
4. Set `LLM_PROVIDER=gemini`

**Option B: OpenAI (Paid)**
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create an API key
3. Save as `OPENAI_API_KEY`
4. Set `LLM_PROVIDER=openai`

---

## Step 2: Deploy Backend to Koyeb (Free, No Card Required)

### 2.1 Create Koyeb Account

1. Go to [koyeb.com](https://www.koyeb.com)
2. Sign up with your GitHub account (recommended)

### 2.2 Create Web Service

1. Click **"Create App"**
2. Select **"GitHub"** as deployment method
3. Connect your GitHub account if not already connected
4. Select repository: `farazahmed7530/physical-ai-textbook`
5. Configure the service:

| Setting | Value |
|---------|-------|
| App name | `physical-ai-textbook-api` |
| Branch | `main` |
| Root directory | `backend` |
| Builder | `Buildpack` |
| Run command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Instance type | `Free` (nano) |
| Region | Washington, D.C. (or closest to you) |

### 2.3 Add Environment Variables

In Koyeb dashboard, go to **Environment variables** section and add:

```
GEMINI_API_KEY=<your-gemini-key>
LLM_PROVIDER=gemini
DATABASE_URL=<your-neon-url>
QDRANT_URL=<your-qdrant-url>
QDRANT_API_KEY=<your-qdrant-key>
JWT_SECRET=<generate-a-random-string>
CORS_ORIGINS=https://farazahmed7530.github.io
PORT=8000
```

**Generate JWT_SECRET:**
```bash
openssl rand -hex 32
```

### 2.4 Deploy

1. Click **"Deploy"**
2. Wait for build to complete (2-5 minutes)
3. Koyeb will auto-deploy on every push to main branch

### 2.5 Note Your Backend URL

After deployment, Koyeb gives you a URL like:
```
https://physical-ai-textbook-api-<your-username>.koyeb.app
```

Save this - you'll need it for the frontend.

---

## Step 3: Deploy Frontend to GitHub Pages

### 3.1 Update Frontend Config

Edit `textbook/docusaurus.config.ts`:

```typescript
const config: Config = {
  // ... other config
  url: 'https://yourusername.github.io',
  baseUrl: '/your-repo-name/',
  organizationName: 'yourusername',
  projectName: 'your-repo-name',
  // ...
};
```

### 3.2 Update API Endpoint

Update the API endpoint in your frontend components to point to your Render backend URL.

Edit `textbook/src/components/ChatWidget/ChatProvider.tsx` and similar files:
```typescript
const API_URL = 'https://physical-ai-textbook-api.onrender.com';
```

### 3.3 Enable GitHub Pages

1. Go to your GitHub repo → **Settings** → **Pages**
2. Source: **GitHub Actions**
3. The `deploy-pages.yml` workflow will handle deployment

---

## Step 4: Configure GitHub Secrets (Optional)

Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**

### Repository Secrets (For CI tests)

| Secret Name | Value |
|-------------|-------|
| `GEMINI_API_KEY` | Your Gemini key (if using) |
| `DATABASE_URL` | Your Neon connection string |
| `QDRANT_URL` | Your Qdrant cluster URL |
| `QDRANT_API_KEY` | Your Qdrant API key |

**Note:** Koyeb handles deployment automatically - no deploy hooks needed!

---

## Step 5: Initialize Database

Run the database migrations:

```bash
cd backend

# Set environment variables
export DATABASE_URL="your-neon-connection-string"

# Run migrations
python -c "
import asyncio
from migrations.runner import run_migrations
asyncio.run(run_migrations())
"
```

---

## Step 6: Index Content

Index your textbook content into Qdrant:

```bash
cd backend

# Set environment variables
export DATABASE_URL="your-neon-connection-string"
export QDRANT_URL="your-qdrant-url"
export QDRANT_API_KEY="your-qdrant-key"
export OPENAI_API_KEY="your-openai-key"  # or GEMINI_API_KEY

# Run indexer
python scripts/index_content.py
```

---

## Step 7: Deploy!

Push to main branch to trigger deployment:

```bash
git add .
git commit -m "Configure deployment"
git push origin main
```

GitHub Actions will:
1. Run tests
2. Deploy backend to Render
3. Build and deploy frontend to GitHub Pages

---

## Verification

### Check Backend Health
```bash
curl https://physical-ai-textbook-api.onrender.com/health
```

### Check Frontend
Visit: `https://yourusername.github.io/your-repo-name/`

---

## Troubleshooting

### Backend not responding
- Check Render logs in dashboard
- Verify environment variables are set
- Free tier sleeps after 15 min - first request takes ~30 sec

### CORS errors
- Ensure `CORS_ORIGINS` includes your GitHub Pages URL
- Format: `https://yourusername.github.io`

### Database connection errors
- Verify `DATABASE_URL` is correct
- Check Neon dashboard for connection limits

### Chat not working
- Verify Qdrant is indexed with content
- Check LLM API key is valid
- Review backend logs for errors

---

## Cost Summary (Free Tier)

| Service | Free Tier Limits |
|---------|------------------|
| Koyeb | 1 service, 512MB RAM, no sleep! |
| Neon | 0.5 GB storage, 1 project |
| Qdrant Cloud | 1 GB storage, 1 cluster |
| GitHub Pages | Unlimited for public repos |
| Gemini | 15 RPM, 1M tokens/day |

This setup is completely free for learning/demo purposes!
