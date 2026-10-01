# Quick Start: Deploy to Railway

This guide will have your TTS service running on Railway in 5 minutes.

## Prerequisites
- GitHub account
- Railway account (free tier available at https://railway.app)

## Step-by-Step Deployment

### 1. Prepare GitHub
Make sure your code is pushed to GitHub:
```bash
cd UnhelpfulGenie
git add .
git commit -m "Initial TTS service setup"
git push origin main
```

### 2. Go to Railway
- Open https://railway.app in your browser
- Sign in with your GitHub account (authorize if needed)

### 3. Create New Project
- Click the **"New Project"** button (top right)
- Select **"Deploy from GitHub repo"**
- Click **"Configure GitHub App"** if this is your first time
- Select the **UnhelpfulGenie** repository
- Click **"Deploy Now"**

### 4. Wait for Deployment
Railway will automatically:
- Detect the `Procfile`
- Install dependencies from `requirements.txt`
- Start your service

You'll see a log stream showing the build progress. Wait until you see "Listening on port..."

### 5. Get Your URL
Once deployed:
- Go to the **"Settings"** tab in Railway
- Copy the **Domain** URL (something like `https://unhelpfulgenie-prod.railway.app`)
- This is your service URL!

### 6. Test Your Service
Replace `YOUR_URL` with your actual URL and test:

```bash
# Health check
curl https://YOUR_URL/health

# Send text for synthesis
curl -X POST https://YOUR_URL/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from Railway!"}'

# Download latest audio
curl -X GET https://YOUR_URL/download -o latest.wav

# List files
curl -X GET https://YOUR_URL/list
```

## Update Your Arduino Code
In your Arduino sketch, replace:
```cpp
const char* serviceUrl = "https://your-railway-url.railway.app";
```

With your actual Railway URL.

## Monitoring & Logs
- Click **"Deployments"** to see your active service
- Click **"Logs"** to see real-time output
- Logs show all API requests and errors

## Common Issues

### Build fails with "ModuleNotFoundError"
- Railway runs on Linux with specific dependencies
- If pyttsx3 fails, try using gTTS instead (edit app.py)

### Audio files disappear after redeploy
- Railway uses ephemeral storage (files deleted on redeploy)
- Solution: Use an external storage service or save to database

### Service slow on first request
- First request wakes up the free tier dyno
- This is normal; subsequent requests are faster

## Updating Your Code
To update your service:
1. Make changes locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update TTS settings"
   git push origin main
   ```
3. Railway auto-detects the push and redeploys automatically

## Scaling Up (Paid)
If you need:
- Persistent storage
- Multiple dynos
- Better performance

Click **"Billing"** in Railway and upgrade your plan.

## Next Steps

### Add Authentication
To prevent unauthorized access, add API key authentication:
```python
from functools import wraps
from flask import request

API_KEY = os.environ.get('API_KEY', 'your-secret-key')

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if key != API_KEY:
            return {'error': 'Unauthorized'}, 401
        return f(*args, **kwargs)
    return decorated

@app.route('/synthesize', methods=['POST'])
@require_api_key
def synthesize():
    ...
```

### Custom Domain
- Go to Settings → Domain
- Add a custom domain you own
- Follow Railway's instructions for DNS setup

### Environment Variables
To set environment variables in Railway:
1. Go to **Settings**
2. Scroll to **Environment Variables**
3. Click **"Raw Editor"** and add:
   ```
   API_KEY=your-secret-key
   AUDIO_DIR=/data/audio_files
   ```

## Support
- Railway Docs: https://docs.railway.app
- Flask Docs: https://flask.palletsprojects.com
- pyttsx3 Docs: https://pyttsx3.readthedocs.io

Happy deploying! 🚀
