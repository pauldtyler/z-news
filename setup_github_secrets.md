# GitHub Secrets Setup Guide

## 🔑 Adding Your Anthropic API Key to GitHub Secrets

Your Anthropic API key from `.env` file: `[COPY FROM YOUR .env FILE]`

### Step-by-Step Instructions:

1. **Go to your GitHub repository:**
   ```
   https://github.com/pauldtyler/z-news
   ```

2. **Navigate to Settings:**
   - Click on the "Settings" tab (top right of repository page)

3. **Access Secrets and Variables:**
   - In the left sidebar, click "Secrets and variables"
   - Click "Actions"

4. **Add Repository Secret:**
   - Click "New repository secret"
   - Name: `ANTHROPIC_API_KEY`
   - Secret: `[PASTE YOUR API KEY FROM .env FILE HERE]`
   - Click "Add secret"

## ✅ Verification Steps

After adding the secret:

1. **Test the workflow manually:**
   - Go to "Actions" tab in your GitHub repo
   - Find "Daily News Collection and Summary Generation"
   - Click "Run workflow" → "Run workflow"

2. **Check the workflow run:**
   - It should start running and complete successfully
   - Look for green checkmarks
   - Check the logs for any errors

## 🚀 Next: Deploy to Vercel

Once GitHub secrets are set up:

1. **Install Vercel CLI (if needed):**
   ```bash
   npm install -g vercel
   ```

2. **Deploy to Vercel:**
   ```bash
   cd /Users/paultyler/Documents/development/z-news
   vercel --prod
   ```

3. **Or connect GitHub to Vercel:**
   - Go to https://vercel.com/dashboard
   - Click "Add New" → "Project"
   - Import your GitHub repository
   - Vercel will auto-deploy on every push

## 📋 Your API Endpoints (after Vercel deployment)

```
https://your-vercel-app.vercel.app/daily-summary
https://your-vercel-app.vercel.app/status
https://your-vercel-app.vercel.app/healthcheck
```

## 🔄 How It Works

1. **GitHub Actions runs daily at 8 AM UTC (midnight PST)**
2. **Collects news data slowly and safely**
3. **Generates `daily_summary.json`**
4. **Commits JSON back to repository**
5. **Vercel auto-deploys the updated API**
6. **Your website gets instant responses from the JSON data**

Ready to proceed with GitHub secrets setup!