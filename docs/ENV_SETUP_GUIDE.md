# 🔐 Environment Variables Setup Guide

## Why Use Environment Variables?

Environment variables are **much safer** than storing credentials in config files because:
- ✅ They're not committed to Git (protected by `.gitignore`)
- ✅ They're separate from your code
- ✅ They're easier to manage across different environments
- ✅ They follow security best practices

---

## 🚀 Quick Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

This will install `python-dotenv` which is needed for loading environment variables.

### Step 2: Create Your .env File
```bash
# Copy the example file
cp .env.example .env

# Edit with your credentials
nano .env   # or use any text editor
```

### Step 3: Add Your Throwaway Account Credentials
Edit `.env` and replace with your **throwaway LinkedIn account**:

```bash
LINKEDIN_USERNAME=your_throwaway_email@example.com
LINKEDIN_PASSWORD=your_throwaway_password

# Optional settings
CHROME_DEBUG_PORT=9222
RATE_LIMIT_SECONDS=3
DEBUG_MODE=false
```

⚠️ **IMPORTANT**: Use a throwaway account, NOT your personal LinkedIn account!

### Step 4: Verify .env is Ignored by Git
```bash
git status
# You should NOT see .env in the list
```

✅ The `.env` file is already added to `.gitignore` so it won't be committed.

---

## 📖 Usage

### Option 1: Using Environment Variables (Recommended)

```bash
# The scraper will automatically use credentials from .env
python3 scraper.py --url https://www.linkedin.com/in/PROFILE_NAME/ --save True
```

### Option 2: Using config.ini (Fallback)

If no `.env` file exists, the scraper will fall back to `config.ini`:

```bash
# Create config.ini from example
cp example.config.ini config.ini

# Edit with your credentials
nano config.ini

# Run scraper
python3 scraper.py --url https://www.linkedin.com/in/PROFILE_NAME/ --save True
```

### Option 3: Using Remote Debugging (No Credentials Needed!)

```bash
# 1. Start Chrome in debug mode
google-chrome --remote-debugging-port=9222 --user-data-dir="~/.config/google-chrome"

# 2. Login to LinkedIn in that Chrome window

# 3. Run scraper (no credentials needed!)
python3 scraper.py --running True --port 9222 --url YOUR_URL --save True
```

---

## 🔧 Environment Variables Reference

### Required Variables (for non-debugging mode)

| Variable | Description | Example |
|----------|-------------|---------|
| `LINKEDIN_USERNAME` | LinkedIn email/username | `throwaway@example.com` |
| `LINKEDIN_PASSWORD` | LinkedIn password | `SecurePassword123!` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CHROME_DEBUG_PORT` | Chrome debugging port | `9222` |
| `RATE_LIMIT_SECONDS` | Delay between requests | `3` |
| `DEBUG_MODE` | Enable debug logging | `false` |

---

## 🛡️ Security Best Practices

### DO ✅
- ✅ Use a **throwaway LinkedIn account**
- ✅ Keep `.env` file local (never commit it)
- ✅ Use strong, unique passwords
- ✅ Review `.gitignore` to ensure `.env` is listed
- ✅ Share `.env.example` (template without real credentials)
- ✅ Use remote debugging mode when possible (no credentials needed)

### DON'T ❌
- ❌ Use your personal LinkedIn account
- ❌ Commit `.env` to Git
- ❌ Share your `.env` file with others
- ❌ Use weak passwords
- ❌ Store credentials in code
- ❌ Push `config.ini` to Git

---

## 🔍 Verification

### Check if Environment Variables are Loaded

Create a test script `test_env.py`:

```python
from dotenv import load_dotenv
import os

load_dotenv()

username = os.getenv("LINKEDIN_USERNAME")
password = os.getenv("LINKEDIN_PASSWORD")

if username and password:
    print("✅ Environment variables loaded successfully!")
    print(f"Username: {username[:3]}***{username[-3:]}")  # Partially masked
    print(f"Password: {'*' * len(password)}")
else:
    print("❌ Environment variables not found!")
    print("Make sure you have a .env file with LINKEDIN_USERNAME and LINKEDIN_PASSWORD")
```

Run it:
```bash
python3 test_env.py
```

---

## 🐛 Troubleshooting

### "No credentials found" Error

**Problem**: Scraper can't find credentials

**Solutions**:
1. Check if `.env` file exists: `ls -la .env`
2. Verify `.env` has correct format (no spaces around `=`)
3. Check if `python-dotenv` is installed: `pip list | grep dotenv`
4. Make sure `.env` is in the same directory as `scraper.py`

### ".env file not being read"

**Problem**: Changes to `.env` not taking effect

**Solutions**:
1. Restart your terminal/shell
2. Check for typos in variable names
3. No spaces: `LINKEDIN_USERNAME=email` not `LINKEDIN_USERNAME = email`
4. No quotes needed: `LINKEDIN_USERNAME=email@test.com` not `LINKEDIN_USERNAME="email@test.com"`

### "Environment variable is None"

**Problem**: `os.getenv()` returns `None`

**Solutions**:
1. Verify variable name matches exactly (case-sensitive)
2. Check `.env` file is in the correct location
3. Ensure `load_dotenv()` is called before accessing variables
4. Try absolute path: `load_dotenv('/full/path/to/.env')`

---

## 📝 Example .env File

```bash
# LinkedIn Throwaway Account Credentials
LINKEDIN_USERNAME=scraper.throwaway@gmail.com
LINKEDIN_PASSWORD=MySecurePass123!

# Chrome Settings
CHROME_DEBUG_PORT=9222

# Rate Limiting (seconds between requests)
RATE_LIMIT_SECONDS=5

# Enable debug logging
DEBUG_MODE=true
```

---

## 🔄 Migration from config.ini

If you're currently using `config.ini`:

### Step 1: Copy Credentials
```bash
# View your current config
cat config.ini

# Create .env with same credentials
nano .env
```

### Step 2: Test
```bash
# Test with environment variables
python3 scraper.py --url YOUR_URL --save True

# Check logs to confirm it's using env vars
tail -f app.log
# Should see: "Using credentials from environment variables"
```

### Step 3: Remove config.ini (Optional)
```bash
# Once confirmed working, you can remove config.ini
rm config.ini
```

---

## 🌍 Using in Different Environments

### Development (Local)
```bash
# .env in project root
LINKEDIN_USERNAME=dev.account@example.com
LINKEDIN_PASSWORD=DevPassword123
```

### Production (Server)
```bash
# Set environment variables directly
export LINKEDIN_USERNAME="prod.account@example.com"
export LINKEDIN_PASSWORD="ProdPassword456"

# Or use system environment variables
echo "export LINKEDIN_USERNAME='prod.account@example.com'" >> ~/.bashrc
echo "export LINKEDIN_PASSWORD='ProdPassword456'" >> ~/.bashrc
source ~/.bashrc
```

### Docker
```dockerfile
# In docker-compose.yml
environment:
  - LINKEDIN_USERNAME=${LINKEDIN_USERNAME}
  - LINKEDIN_PASSWORD=${LINKEDIN_PASSWORD}
```

Or use an env file:
```yaml
env_file:
  - .env
```

---

## ✅ Final Checklist

Before you start scraping:

- [ ] `python-dotenv` installed (`pip install python-dotenv`)
- [ ] `.env` file created from `.env.example`
- [ ] Throwaway LinkedIn credentials added to `.env`
- [ ] `.env` is in `.gitignore` (already done)
- [ ] Verified credentials work: `python3 test_env.py`
- [ ] Tested scraper: `python3 scraper.py --url YOUR_URL`
- [ ] `.env` not showing in `git status`

---

## 🆘 Still Having Issues?

1. **Check the logs**: `tail -f app.log`
2. **Enable debug mode**: Set `DEBUG_MODE=true` in `.env`
3. **Use remote debugging mode**: Avoids credential issues entirely
4. **Verify Python version**: `python3 --version` (should be 3.7+)
5. **Reinstall dependencies**: `pip install -r requirements.txt --force-reinstall`

---

**Last Updated**: October 20, 2025  
**Security**: ✅ Credentials now protected with environment variables!
