# 🚨 WSL Connection Issues - SOLVED

## Problem
When running the scraper with `--running True`, you get:
```
selenium.common.exceptions.WebDriverException: Message: unknown error: cannot connect to chrome at localhost:9222
```

## Root Cause
WSL cannot connect to Windows `localhost:9222` directly. You need to use the **Windows host IP address** instead.

---

## ✅ **SOLUTION: Use Windows Host IP**

### **Step 1: Find Your Windows Host IP**

Run this in WSL:
```bash
ip route show | grep -i default | awk '{ print $3}'
```

**Your Windows host IP is: `172.24.128.1`**

---

### **Step 2: Start Chrome on Windows**

Open **PowerShell on Windows** and run:

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome-debug"
```

**Important:** Make sure Chrome starts the **--remote-debugging-port on 0.0.0.0**, not just localhost!

If you want to be explicit, you can add:
```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-debugging-address=0.0.0.0 --user-data-dir="C:\temp\chrome-debug"
```

---

### **Step 3: Verify Connection from WSL**

Test the connection using your Windows IP:

```bash
curl http://172.24.128.1:9222/json/version
```

**If you see JSON output** = ✅ Connection works!  
**If you see nothing or timeout** = ❌ Connection blocked (see firewall section below)

---

### **Step 4: Login to LinkedIn**

In the Chrome window:
1. Go to `https://www.linkedin.com/`
2. Login with your throwaway account

---

### **Step 5: Run Scraper with Host IP**

Now run the scraper with `--host` flag:

```bash
python3 scraper.py --running True --port 9222 --host 172.24.128.1 \
  --url https://www.linkedin.com/in/louise-scarlette-maunoir/ \
  --save True
```

**That's it!** 🎉

---

## 🔥 **Windows Firewall Issues**

If `curl http://172.24.128.1:9222/json/version` times out, Windows Firewall is blocking the connection.

### **Quick Fix: Allow Port 9222**

**Option A: PowerShell (Recommended)**

Run this in **Windows PowerShell as Administrator**:

```powershell
New-NetFirewallRule -DisplayName "Chrome Debug Port" -Direction Inbound -LocalPort 9222 -Protocol TCP -Action Allow
```

**Option B: GUI Method**

1. Open Windows Defender Firewall
2. Click "Advanced settings"
3. Click "Inbound Rules" → "New Rule"
4. Select "Port" → Next
5. Enter port `9222` → Next
6. Select "Allow the connection" → Next
7. Check all profiles → Next
8. Name it "Chrome Debug Port" → Finish

---

## 🧪 **Testing the Connection**

### Test 1: Check if Chrome is listening

In **Windows PowerShell**:
```powershell
netstat -an | Select-String "9222"
```

You should see:
```
TCP    0.0.0.0:9222          0.0.0.0:0              LISTENING
```

### Test 2: Check from WSL

In **WSL**:
```bash
curl http://172.24.128.1:9222/json/version
```

Expected output:
```json
{
   "Browser": "Chrome/120.0.6099.109",
   "Protocol-Version": "1.3",
   "User-Agent": "Mozilla/5.0...",
   "V8-Version": "12.0.267.8",
   "WebKit-Version": "537.36",
   "webSocketDebuggerUrl": "ws://172.24.128.1:9222/devtools/browser/..."
}
```

### Test 3: Run the scraper

```bash
python3 scraper.py --running True --port 9222 --host 172.24.128.1 \
  --url https://www.linkedin.com/in/louise-scarlette-maunoir/ \
  --save True
```

---

## 📝 **Quick Reference Commands**

### Get Windows IP from WSL:
```bash
ip route show | grep -i default | awk '{ print $3}'
```

### Start Chrome on Windows:
```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-debugging-address=0.0.0.0 --user-data-dir="C:\temp\chrome-debug"
```

### Test connection:
```bash
curl http://172.24.128.1:9222/json/version
```

### Run scraper:
```bash
python3 scraper.py --running True --port 9222 --host 172.24.128.1 --url YOUR_URL --save True
```

---

## 🎯 **Environment Variable Support**

You can also set the host in your `.env` file:

```bash
# .env
CHROME_DEBUG_HOST=172.24.128.1
CHROME_DEBUG_PORT=9222
```

Then the scraper will use it automatically:
```bash
python3 scraper.py --running True --url YOUR_URL --save True
```

---

## 🐛 **Still Not Working?**

### Error: "Connection refused"
- Make sure Chrome is actually running with `--remote-debugging-port=9222`
- Check Windows Task Manager for `chrome.exe` process
- Verify the port with: `netstat -an | Select-String "9222"` (Windows)

### Error: "Connection timeout"
- Windows Firewall is blocking port 9222
- Add firewall rule (see above)
- Or temporarily disable firewall for testing

### Error: "Chrome not reachable"
- Check if you're using the correct Windows IP: `ip route show | grep default`
- The IP might change after reboot
- Add `--host YOUR_IP` to the command

### Chrome closes immediately
- Use `--user-data-dir` flag (already in the command)
- Don't close the Chrome window manually

---

## ✅ **Success Checklist**

- [ ] Chrome started on Windows with `--remote-debugging-port=9222`
- [ ] `netstat` shows port 9222 listening on Windows
- [ ] Firewall rule added for port 9222
- [ ] `curl http://172.24.128.1:9222/json/version` returns JSON from WSL
- [ ] Logged into LinkedIn in the Chrome window
- [ ] Running scraper with `--host 172.24.128.1`
- [ ] Profile data saved to `data/` directory

---

## 🎉 **You're all set!**

The scraper should now work perfectly! 🚀
