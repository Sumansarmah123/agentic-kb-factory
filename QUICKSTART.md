# 🚀 Agentic KB Factory - Deployment Guide

## Prerequisites
- Google Cloud account with billing enabled
- Netlify account
- Node.js 18+

## 1. Deploy Backend (Google Cloud Shell)

```bash
git clone https://github.com/Sumansarmah123/agentic-kb-factory.git
cd agentic-kb-factory

gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

gcloud run deploy agentic-kb-backend \
  --source . \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars="GEMINI_API_KEY=YOUR_API_KEY,GCP_PROJECT_ID=YOUR_PROJECT_ID" \
  --memory=512Mi \
  --timeout=300 \
  --port=8080

# Get backend URL
gcloud run services describe agentic-kb-backend --region=us-central1 --format='value(status.url)'
```

## 2. Deploy Frontend (Netlify)

```bash
cd frontend
echo "VITE_API_BASE_URL=YOUR_BACKEND_URL" > .env.production
npm install
npm run build
npx netlify-cli deploy --prod --dir=dist
```

## 3. Test

Login credentials:
- Username: `Admin123`
- Password: `Hackathon123`

## Features
- Self-healing DOM extraction
- Model Armor security
- 7-agent fleet architecture
- Real-time activity feed
- OpenTelemetry observability

## GitHub
https://github.com/Sumansarmah123/agentic-kb-factory
