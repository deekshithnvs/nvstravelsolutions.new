# 🚀 Deployment Guide - NVS Vendor Management Portal

This guide will help you deploy your Vendor Management Portal to **Render.com** for **FREE**.

---

## 📋 Prerequisites

1. **GitHub Account** - [Sign up here](https://github.com/signup) if you don't have one
2. **Render.com Account** - [Sign up here](https://render.com/register) (free, no credit card required)
3. Your code must be pushed to GitHub

---

## 🔧 Step 1: Push Your Code to GitHub

### 1.1 Check Git Status
```bash
cd "c:\code\Vendor management portal\Site\site2\nvstravelsolutions.new"
git status
```

### 1.2 Add All Files
```bash
git add .
```

### 1.3 Commit Changes
```bash
git commit -m "Add Render.com deployment configuration"
```

### 1.4 Push to GitHub
```bash
git push origin main
```

> **Note**: If you get an error, your branch might be called `master` instead of `main`. Try:
> ```bash
> git push origin master
> ```

---

## 🌐 Step 2: Deploy to Render.com

### 2.1 Sign Up / Log In
1. Go to [https://render.com](https://render.com)
2. Click **"Get Started for Free"**
3. Sign up with your **GitHub account** (easiest option)

### 2.2 Create a New Web Service
1. Click **"New +"** button in the top right
2. Select **"Web Service"**
3. Connect your GitHub repository:
   - Click **"Connect account"** if not already connected
   - Find and select your repository: `nvstravelsolutions.new`
   - Click **"Connect"**

### 2.3 Configure the Web Service

Fill in the following settings:

| Field | Value |
|-------|-------|
| **Name** | `nvs-vendor-portal` (or any name you prefer) |
| **Region** | Choose closest to you (e.g., Singapore, Oregon) |
| **Branch** | `main` (or `master` if that's your branch name) |
| **Runtime** | **Python 3** |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | **Free** |

### 2.4 Add Environment Variables

Scroll down to **"Environment Variables"** section and add:

| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.11.0` |
| `DATABASE_URL` | `sqlite:///./nvs_portal.db` |
| `SECRET_KEY` | `your-secret-key-here-change-this-in-production` |

> **Important**: Generate a secure SECRET_KEY. You can use this Python command:
> ```python
> import secrets
> print(secrets.token_urlsafe(32))
> ```

### 2.5 Deploy!

1. Click **"Create Web Service"** at the bottom
2. Render will start building and deploying your app
3. Wait 2-5 minutes for the deployment to complete
4. You'll see a URL like: `https://nvs-vendor-portal.onrender.com`

---

## ✅ Step 3: Verify Deployment

### 3.1 Open Your Site
Click on the URL provided by Render (e.g., `https://nvs-vendor-portal.onrender.com`)

### 3.2 Initialize Database
Your app should automatically create the database on first run. If you need to run the production setup script:

1. Go to Render dashboard → Your service
2. Click **"Shell"** tab on the left
3. Run:
   ```bash
   python prepare_production.py
   ```

### 3.3 Test Login
Use the default admin credentials:
- **Email**: `admin@nvstravels.com`
- **Password**: `NVSadmin2026!`

> **Security**: Change this password immediately after first login!

---

## 🔍 Troubleshooting

### Issue: "Application failed to respond"
**Solution**: Check the logs in Render dashboard → Logs tab. Common issues:
- Missing environment variables
- Database connection errors
- Port binding issues (make sure start command uses `$PORT`)

### Issue: Static files not loading
**Solution**: Render automatically serves static files. Make sure your `static` folder is in the repository.

### Issue: Database resets on every deploy
**Solution**: Render's free tier has ephemeral storage. For persistent database, you need to:
1. Use Render's PostgreSQL database (free tier available)
2. Update your `DATABASE_URL` environment variable
3. Modify your code to use PostgreSQL instead of SQLite

---

## 🎯 Next Steps

### Enable PostgreSQL (Recommended for Production)

1. In Render dashboard, click **"New +"** → **"PostgreSQL"**
2. Name it `nvs-portal-db` and select **Free** tier
3. Click **"Create Database"**
4. Copy the **Internal Database URL**
5. Go back to your Web Service → Environment
6. Update `DATABASE_URL` with the PostgreSQL URL
7. Update `requirements.txt` - ensure `psycopg2-binary` is included (already there!)
8. Redeploy

### Custom Domain (Optional)
1. Go to your Web Service settings
2. Click **"Custom Domain"**
3. Follow instructions to add your domain

### Auto-Deploy on Git Push
Render automatically deploys when you push to GitHub! Just:
```bash
git add .
git commit -m "Your changes"
git push origin main
```

---

## 📞 Support

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com
- **FastAPI Docs**: https://fastapi.tiangolo.com

---

## 🎉 Success!

Your Vendor Management Portal is now live and accessible from anywhere in the world!

**Your Live URL**: `https://your-service-name.onrender.com`

---

### ⚠️ Important Notes

1. **Free Tier Limitations**:
   - Service spins down after 15 minutes of inactivity
   - First request after inactivity may take 30-60 seconds (cold start)
   - 750 hours/month free (enough for 24/7 uptime)

2. **Security**:
   - Change default admin password immediately
   - Use strong SECRET_KEY in production
   - Enable HTTPS (automatic on Render)

3. **Database**:
   - SQLite works but data is ephemeral (resets on redeploy)
   - Use PostgreSQL for persistent data (free tier available)
