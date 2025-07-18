# 🚀 REPLIT QUICKSTART - IA Fiscal Capivari

## ⚡ Quick Fix for Current Error

You're getting a Pydantic import error. Here's the **instant fix**:

### 1. Run the Fix Script
```bash
python fix_replit.py
```

### 2. If that doesn't work, run these commands:
```bash
# Install dependencies
pip install -r requirements-replit.txt

# Create directories
mkdir -p data/raw data/processed data/alerts logs reports

# Set Python path
export PYTHONPATH=/home/runner/workspace/src
```

### 3. Then run the main application:
```bash
python main_replit.py
```

## 🔧 Manual Fix (if needed)

If you're still getting the Pydantic error, edit `src/config.py`:

**Change line 4 from:**
```python
from pydantic import BaseSettings
```

**To:**
```python
from pydantic_settings import BaseSettings
```

## 🔐 Required Secrets

Make sure you have these in **Tools → Secrets**:

```
APIFY_API_TOKEN=your_token_here
CLAUDE_API_KEY=your_key_here
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ADMIN_EMAIL=admin@capivari.sp.gov.br
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here
WEBHOOK_SECRET=your_webhook_secret_here
```

## 🎯 After Fix

Your system will be available at:
- **API**: `https://workspace.your-username.repl.co`
- **Dashboard**: `https://workspace.your-username.repl.co:3000`

## 🆘 Still Having Issues?

### Common Solutions:

**1. Module Import Error:**
```bash
export PYTHONPATH=/home/runner/workspace/src
```

**2. Permission Error:**
```bash
chmod +x main_replit.py
```

**3. Dependencies Error:**
```bash
pip install --upgrade pip
pip install -r requirements-replit.txt
```

**4. Database Error:**
```bash
mkdir -p data
touch data/ia_fiscal.db
```

## 🚀 One-Line Deploy

For fastest deployment:
```bash
python fix_replit.py && python main_replit.py
```

**You should see:**
```
🚀 Starting IA Fiscal Capivari on Replit
✅ Detected Replit environment
✅ All services started successfully
🌐 API server running on port 8000
📊 Dashboard running on port 8501
```

## 📞 Need Help?

If you're still stuck, run:
```bash
python -c "import sys; print('Python path:', sys.path)"
```

And share the output - I can help debug further!

---

**🎉 Let's get this fiscal transparency system live! 🏛️**