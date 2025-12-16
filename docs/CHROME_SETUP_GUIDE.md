# 🌐 Chrome & ChromeDriver Setup Guide

## Problem
You're getting this error:
```
selenium.common.exceptions.WebDriverException: Message: unknown error: cannot find Chrome binary
```

This means **Chrome/Chromium and ChromeDriver are not installed** on your system.

---

## 🚀 Quick Fix for Linux (WSL/Ubuntu/Debian)

### Step 1: Install Google Chrome

```bash
# Download Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

# Install Chrome
sudo dpkg -i google-chrome-stable_current_amd64.deb

# Fix any dependency issues
sudo apt-get install -f

# Verify installation
google-chrome --version
```

**OR** install Chromium (lighter alternative):

```bash
sudo apt-get update
sudo apt-get install -y chromium-browser

# Verify installation
chromium-browser --version
```

---

### Step 2: Install ChromeDriver

**Option A: Automatic Installation (Recommended)**

```bash
# Install webdriver-manager
pip install webdriver-manager

# This will auto-download the correct chromedriver version
```

Then update `scraper.py` to use webdriver-manager (I can do this for you).

**Option B: Manual Installation**

```bash
# Check your Chrome version
google-chrome --version
# Example output: Google Chrome 120.0.6099.109

# Download matching ChromeDriver from:
# https://googlechromelabs.github.io/chrome-for-testing/

# For Chrome 120+, use:
wget https://storage.googleapis.com/chrome-for-testing-public/120.0.6099.109/linux64/chromedriver-linux64.zip

# Unzip
unzip chromedriver-linux64.zip

# Move to system path
sudo mv chromedriver-linux64/chromedriver /usr/local/bin/

# Make executable
sudo chmod +x /usr/local/bin/chromedriver

# Verify
chromedriver --version
```

---

## 🔧 Update scraper.py to Use Webdriver Manager

I can modify `scraper.py` to automatically download and manage ChromeDriver. This is **much easier** than manual installation!

Would you like me to:
1. ✅ Update `scraper.py` to use `webdriver-manager` (auto-downloads chromedriver)
2. ✅ Update `requirements.txt` to include `webdriver-manager`

---

## 🎯 Easiest Solution: Use Remote Debugging Mode

**No Chrome installation needed if you already have Chrome on Windows (WSL users)!**

### Step 1: Start Chrome on Windows in debug mode

Open PowerShell and run:
```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome-debug"
```

### Step 2: Login to LinkedIn in that Chrome window

Just browse to linkedin.com and login normally.

### Step 3: Run the scraper in WSL

```bash
python3 scraper.py --running True --port 9222 --url https://www.linkedin.com/in/PROFILE_NAME/ --save True
```

**This way you don't need to install Chrome in WSL at all!** The scraper will connect to your Windows Chrome.

---

## 🐛 Troubleshooting

### "chromedriver version doesn't match Chrome version"

**Solution**: Use webdriver-manager (auto-matches versions):

```bash
pip install webdriver-manager
```

Then I'll update the code to use it.

### "Chrome binary not found"

**Solution**: Specify Chrome location manually in `scraper.py`:

```python
options.binary_location = "/usr/bin/google-chrome"  # or /usr/bin/chromium-browser
```

### "Permission denied on chromedriver"

**Solution**:
```bash
sudo chmod +x /usr/local/bin/chromedriver
```

---

## ✅ Recommended Approach

**For WSL Users (You!):**

Use the **Remote Debugging Mode** approach - it's the easiest and doesn't require installing Chrome in WSL:

1. Start Chrome on Windows with `--remote-debugging-port=9222`
2. Login to LinkedIn in that Chrome window
3. Run scraper with `--running True --port 9222`

**For Native Linux Users:**

Use **webdriver-manager** approach:

1. Install Chrome: `wget + dpkg` (shown above)
2. Install webdriver-manager: `pip install webdriver-manager`
3. Update scraper.py to use webdriver-manager
4. Run normally: `python3 scraper.py --url YOUR_URL --save True`

---

## 🚀 Next Steps

Let me know which approach you prefer:

1. **Remote debugging** (connect to Windows Chrome) - **EASIEST for WSL**
2. **Webdriver-manager** (auto-manages chromedriver) - **BEST for automation**
3. **Manual installation** (install Chrome + ChromeDriver manually)

I can help you set up any of these! 🎯
