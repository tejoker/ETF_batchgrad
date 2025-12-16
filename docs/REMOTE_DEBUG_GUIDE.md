# 🚀 Quick Start: Remote Debugging Mode

## Why This Works
When using remote debugging mode, the scraper **connects to an already-running Chrome instance**. This means:
- ✅ No Chrome installation needed in WSL
- ✅ No chromedriver needed
- ✅ You login manually (no credential errors)
- ✅ Works perfectly for WSL users

---

## 🎯 3-Step Process

### **Step 1: Start Chrome in Debug Mode (Windows PowerShell)**

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome-debug"
```

**What this does:**
- Opens Chrome with debugging enabled on port 9222
- Uses a separate profile (won't interfere with your regular Chrome)
- Stays open in the background

---

### **Step 2: Login to LinkedIn**

In the Chrome window that opened:
1. Go to `https://www.linkedin.com/`
2. Login with your throwaway account
3. **Keep this window open!**

---

### **Step 3: Run the Scraper (WSL)**

```bash
python3 scraper.py --running True --port 9222 --url https://www.linkedin.com/in/PROFILE_NAME/ --save True
```

**That's it!** The scraper will:
1. Connect to your Windows Chrome (no credentials needed!)
2. Use your logged-in session
3. Scrape the profile
4. Save to `data/PROFILE_NAME.json`

---

## 📝 Examples

### Scrape a single profile:
```bash
python3 scraper.py --running True --port 9222 \
  --url https://www.linkedin.com/in/louise-scarlette-maunoir/ \
  --save True
```

### Scrape multiple profiles from a file:
```bash
# Create url.txt with one URL per line
echo "https://www.linkedin.com/in/profile1/" > url.txt
echo "https://www.linkedin.com/in/profile2/" >> url.txt

# Run scraper
python3 scraper.py --running True --port 9222 \
  --path url.txt \
  --save True
```

---

## 🐛 Troubleshooting

### "Cannot connect to Chrome"

**Problem**: Scraper can't connect to Chrome on port 9222

**Solutions**:
1. Make sure Chrome is running with `--remote-debugging-port=9222`
2. Check if port 9222 is accessible:
   ```bash
   curl http://localhost:9222/json/version
   ```
3. Try a different port:
   ```powershell
   # Windows
   & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9223 --user-data-dir="C:\temp\chrome-debug"
   ```
   ```bash
   # WSL
   python3 scraper.py --running True --port 9223 --url YOUR_URL --save True
   ```

### "ChromeDriver not found"

**This error should NOT appear in remote debugging mode!** If you see it:
- Make sure you're using `--running True`
- Check that the code fix was applied correctly

### "Unable to find element"

**Problem**: Scraper can't find LinkedIn elements

**Solutions**:
1. Make sure you're **logged in** to LinkedIn in the Chrome window
2. Navigate to a profile manually first to verify access
3. Enable debug mode to see what's happening:
   ```bash
   python3 scraper.py --running True --port 9222 --url YOUR_URL --save True --debug True
   ```

---

## 💡 Pro Tips

### Keep Chrome Window Open
The Chrome window with `--remote-debugging-port` must **stay open** while scraping. Don't close it!

### Multiple Scrapes
Once Chrome is running in debug mode, you can run the scraper multiple times without restarting Chrome:

```bash
# First profile
python3 scraper.py --running True --port 9222 --url https://www.linkedin.com/in/profile1/ --save True

# Second profile (Chrome still running!)
python3 scraper.py --running True --port 9222 --url https://www.linkedin.com/in/profile2/ --save True
```

### Different Port
If port 9222 is already in use, use a different port:

```powershell
# Windows - use port 9223
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9223 --user-data-dir="C:\temp\chrome-debug"
```

```bash
# WSL - specify the port
python3 scraper.py --running True --port 9223 --url YOUR_URL --save True
```

### Check Connection
Before scraping, verify Chrome is accessible:

```bash
curl http://localhost:9222/json/version
```

You should see JSON output with Chrome version info.

---

## 🎓 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  Windows                                                     │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Chrome (--remote-debugging-port=9222)             │    │
│  │  - Logged into LinkedIn                            │    │
│  │  - Listening on port 9222                          │    │
│  └────────────────────────────────────────────────────┘    │
│                          ↕                                   │
│                    Port 9222                                 │
│                          ↕                                   │
└──────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│  WSL/Linux                                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Python Scraper                                    │    │
│  │  - Connects to localhost:9222                      │    │
│  │  - Controls Chrome via DevTools Protocol           │    │
│  │  - Scrapes LinkedIn profiles                       │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

---

## ✅ Advantages

- ✅ **No Chrome installation in WSL** - uses Windows Chrome
- ✅ **No chromedriver needed** - connects directly via DevTools Protocol
- ✅ **Manual login** - no credential storage issues
- ✅ **Easy debugging** - you can see what's happening in Chrome
- ✅ **Reusable session** - login once, scrape many profiles
- ✅ **Perfect for WSL** - leverages Windows GUI

---

## 📚 Related Files

- `scraper.py` - Main scraper script
- `.env` - Credentials (not needed for remote debugging!)
- `data/` - Output directory for scraped JSON files
- `app.log` - Debug logs

---

**Ready to scrape!** 🚀

Just remember:
1. Start Chrome with debug mode (Windows)
2. Login to LinkedIn
3. Run scraper with `--running True` (WSL)
