# Deployment Guide for ForgeMind AI

## Overview
This document provides step-by-step instructions for deploying ForgeMind AI to production using:
- Frontend: Vercel (Static Site Hosting)
- Backend: Render.com (Container Deployment)
- External Services: Pinecone (Vector DB), Groq (LLM API)

## Prerequisites
1. Accounts on:
   - Vercel (vercel.com)
   - Render.com (render.com)
   - Pinecone.io (pinecone.io)
   - GroqCloud (groq.com)
2. GitHub account with the ForgeMind AI repository
3. Docker installed locally (for building/testing)
4. YOLO model file (`computer_vision/weights/best.pt`)

## Step 1: Prepare the Repository

### 1.1 Backup Original Files
```bash
cp main.py main.py.original
```

### 1.2 Modify main.py for API-only Backend
Remove frontend serving responsibilities:
- Remove static file mounting for `/static` (lines 59)
- Remove root endpoint serving `index.html` (lines 256-259)
- Keep `/results` mount for computer vision annotations

### 1.3 Create Frontend Directory for Vercel
```bash
mkdir -p frontend/templates frontend/static
cp templates/* frontend/templates/
cp static/* frontend/static/
```

### 1.4 Update Frontend JavaScript for Configurable Backend
Add API configuration to `frontend/static/app.js`:
- Add `API_BASE` variable and `apiUrl()` helper function
- Update all fetch calls to use `apiUrl(endpoint)` instead of hardcoded paths

### 1.5 Create Dockerfile for Backend
Create a `Dockerfile` in the project root for Render.com deployment.

### 1.6 Create .dockerignore
Create `.dockerignore` to optimize Docker builds.

### 1.7 Create Environment Variables Template
Create `.env.example` with required variables:
- `GROQ_API_KEY`
- `PINECONE_API_KEY`
- `PINECONE_INDEX` (optional)

## Step 2: Deploy Frontend to Vercel

### 2.1 Push Changes to GitHub
Ensure all changes are committed and pushed to your repository.

### 2.2 Import Project to Vercel
1. Go to vercel.com and click "New Project"
2. Import your GitHub repository
3. Vercel should automatically detect it's a static site
4. Configure build settings:
   - Framework: None (Static Site)
   - Root Directory: `frontend`
   - Build Command: `none` (or leave blank)
   - Output Directory: `frontend`
5. Add Environment Variables (if needed):
   - `FORGE_MIND_API_BASE`: Your backend URL (e.g., `https://your-backend.onrender.com`)
6. Click "Deploy"

### 2.3 Verify Frontend Deployment
Once deployed, visit your Vercel URL to ensure the frontend loads correctly.

## Step 3: Deploy Backend to Render.com

### 3.1 Prepare for Render.com
Ensure you have:
- `Dockerfile` in project root
- `.dockerignore` in project root
- All application code committed

### 3.2 Create New Web Service on Render.com
1. Go to render.com and click "New" → "Web Service"
2. Connect your GitHub repository
3. Configure the service:
   - Name: `forgemind-ai-backend` (or similar)
   - Region: Choose closest to your users
   - Branch: `main` (or your production branch)
   - Root Directory: `/` (project root)
   - Dockerfile Path: `./Dockerfile`
   - Environment: Docker
4. Click "Create Web Service"

### 3.3 Add Environment Variables
In the Render.com service dashboard, under "Environment":
- Add `GROQ_API_KEY` (from your .env file)
- Add `PINECONE_API_KEY` (from your .env file)
- Add `PINECONE_INDEX` (optional, defaults to "rag-documents")
- Under "Advanced" → "Environment", you can also set:
  - `PYTHONUNBUFFERED=1`
  - `PORT=8000`

### 3.4 Deploy the Service
Render.com will automatically:
1. Build the Docker image
2. Deploy the container
3. Start the application with `uvicorn main:app --host 0.0.0.0 --port 8000`

### 3.5 Verify Backend Deployment
Once deployed, check:
- Service logs for any errors
- Health endpoint: `https://your-service.onrender.com/status`
- API documentation: `https://your-service.onrender.com/docs` (if enabled)

## Step 4: Configure External Services

### 4.1 Pinecone Setup
1. Create an account at pinecone.io
2. Create a new index:
   - Name: `rag-documents` (or match your `PINECONE_INDEX` env var)
   - Dimension: 384 (for all-MiniLM-L6-v2 embeddings)
   - Metric: cosine
   - Spec: Serverless (AWS us-east-1 recommended)
3. Copy your API key to the environment variables

### 4.2 Groq Setup
1. Create an account at groq.com
2. Create an API key
3. Copy your API key to the environment variables
4. Verify the model `llama-3.3-70b-versatile` is available

## Step 5: Post-Deployment Verification

### 5.1 Test Core Functionality
1. Visit your frontend URL
2. Upload a test document (PDF/TXT)
3. Click "Build Index"
4. Ask a question via the chat interface
5. Verify you get a response with sources

### 5.2 Test Computer Vision Functionality
1. Use the camera or image upload feature
2. Upload an industrial diagram/P&ID
3. Verify detection results appear
4. Check that annotated images are served correctly
5. Verify detections are indexed in Pinecone

### 5.3 Monitor and Maintain
1. Set up monitoring for both services
```error rates and response times
2. Monitor Pinecone usage and costs
3. Monitor Groq API usage and costs
4. Set up logging for debugging if needed
5. Regularly update dependencies for security patches

## Troubleshooting

### Common Issues

#### Backend Fails to Start
- Check Render.com logs for Docker build errors
- Verify all dependencies in requirements.txt are available
- Check that YOLO model file exists at `computer_vision/weights/best.pt`
- Ensure port 8000 is exposed and bound to 0.0.0.0

#### Frontend Cannot Connect to Backend
- Verify `FORGE_MIND_API_BASE` is set correctly in Vercel env vars
- Check CORS settings in main.py (currently allows all origins)
- Ensure backend service is running and accessible
- Check browser console for fetch errors

#### Pinecone Connection Issues
- Verify API key is correct
- Check network connectivity to Pinecone
- Ensure index exists and has correct dimensions
- Verify environment variable naming

#### Groq API Issues
- Verify API key is correct and has sufficient quota
- Check that model `llama-3.3-70b-versatile` is available
- Verify network connectivity to Groq endpoints

## Performance Optimization

### Backend Optimization
1. Consider using GPU-enabled instances on Render for faster CV processing
   usage and optimize batch sizes if needed
3. Consider caching frequently accessed Pinecone queries
4. Monitor memory usage and adjust uvicorn worker count if needed

### Frontend Optimization
1. Vercel automatically optimizes static assets with caching
2. Consider lazy loading heavy libraries if needed
3. Optimize image sizes for upload if users report slowness

## Security Considerations
1. Never commit `.env` files to git - use `.env.example` instead
2. Use environment variables for all secrets
3. Consider rate limiting on public endpoints
4. Keep dependencies updated
5. Monitor for unusual activity in logs

## Cost Optimization Tips
1. Start with free tiers on Vercel and Render
2. Monitor Pinecone usage - consider deleting old indices
3. Groq charges per token - monitor usage if expecting high volume
4. Consider setting usage alerts on all services
5. For development, use local Docker compose to avoid costs
