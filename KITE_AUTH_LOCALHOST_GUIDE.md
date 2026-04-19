# 🔐 Kite Authentication with Localhost (HTTPS Solution)

**Problem**: Kite requires HTTPS for redirect URLs, but EC2 doesn't have SSL  
**Solution**: Use localhost redirect with SSH port forwarding  
**Date**: April 19, 2026

---

## 🎯 Overview

Since Kite API requires HTTPS redirect URLs and your EC2 instance doesn't have an SSL certificate, we use **localhost** as the redirect URL (which Kite allows without HTTPS) combined with **SSH port forwarding** to connect your local machine to EC2.

---

## ✅ **Step-by-Step Authentication Process**

### **Step 1: Update Kite App Redirect URL**

1. Go to https://developers.kite.trade/apps
2. Click on your app
3. Set **Redirect URL** to:
   ```
   http://127.0.0.1:5001/
   ```
   OR
   ```
   http://localhost:5001/
   ```

**Important**: Kite allows `http://localhost` and `http://127.0.0.1` without HTTPS!

---

### **Step 2: Open SSH with Port Forwarding**

**On your local machine, open a terminal and run:**

```bash
ssh -i ~/Downloads/trading-bot.pem -L 5001:localhost:5001 trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com
```

**What this does:**
- `-L 5001:localhost:5001` forwards local port 5001 to EC2's port 5001
- Any request to `localhost:5001` on your machine goes to EC2
- Keep this terminal open during authentication!

---

### **Step 3: Start Authentication Server on EC2**

**In the SSH session you just opened, run:**

```bash
cd /home/trader/trading_bot
source .venv/bin/activate
python3 auth.py
```

**You'll see:**
```
🔐 Starting auto login...
👉 Open this URL if browser doesn't open:
https://kite.zerodha.com/connect/login?api_key=...
⏳ Waiting for login...
```

---

### **Step 4: Login to Kite**

1. Browser should open automatically with Kite login page
2. If not, copy the URL from terminal and open in browser
3. Enter your Kite credentials
4. Enter 2FA code
5. Click "Authorize"

---

### **Step 5: Automatic Redirect**

After authorization:
1. Kite redirects to `http://127.0.0.1:5001/`
2. Your browser connects to localhost:5001
3. SSH port forwarding sends it to EC2:5001
4. Flask server on EC2 receives the callback
5. Token is generated and saved
6. You see success page!

---

### **Step 6: Confirmation**

**On EC2 terminal:**
```
✅ Access token generated and saved
Login successful, token set
```

**On Telegram:**
```
✅ Authentication Successful!

Your Zerodha access token has been generated and saved.

Token Details:
• Created: 2026-04-19 15:10:00
• Expires: 2026-04-20 06:00:00
• Valid for: ~14.8 hours

Trading bot is now ready!
```

**In Browser:**
```
✅ Authentication Successful!
Your access token has been saved.
You can close this window and check Telegram for confirmation.
Trading bot is ready to trade!
```

---

## 🚀 **Quick Command Summary**

### **One-Time Setup:**
```bash
# Update Kite redirect URL to:
http://127.0.0.1:5001/
```

### **Every Time You Need to Authenticate:**

**Terminal 1 (Local Machine):**
```bash
ssh -i ~/Downloads/trading-bot.pem -L 5001:localhost:5001 trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com
```

**Terminal 1 (Now in SSH Session):**
```bash
cd /home/trader/trading_bot
source .venv/bin/activate
python3 auth.py
```

**Browser:**
- Opens automatically or use the URL shown
- Login → 2FA → Authorize → Done!

---

## 📱 **Using Telegram Bot**

### **Send `/auth` to Your Bot**

The bot will send you complete instructions:

```
🔐 Kite Authentication

⚠️ SETUP REQUIRED (Kite needs HTTPS)

Since Kite requires HTTPS and EC2 doesn't have SSL, use SSH port forwarding:

Step 1: Open Terminal on Your Computer
ssh -i ~/Downloads/trading-bot.pem -L 5001:localhost:5001 trader@ec2...

Step 2: In SSH Session, Run:
cd /home/trader/trading_bot
source .venv/bin/activate
python3 auth.py

Step 3: Login to Kite
Browser will open automatically, or use:
[Login Link]

Step 4: Complete Login
• Enter password and 2FA
• Authorize the app
• Redirects to localhost:5001 (forwarded to EC2)
• Token saved automatically

Important:
• Kite redirect URL must be: http://127.0.0.1:5001/
• Keep SSH session open during auth
• Link valid for 10 minutes

You'll receive confirmation after success!
```

---

## 🔍 **How It Works**

```
┌─────────────────────────────────────────────────────────┐
│              AUTHENTICATION FLOW                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. SSH Port Forwarding Active                          │
│     Local:5001 ←→ EC2:5001                              │
│         ↓                                                │
│  2. Flask Server Running on EC2:5001                    │
│         ↓                                                │
│  3. Browser Opens Kite Login                            │
│         ↓                                                │
│  4. User Logs In (Password + 2FA)                       │
│         ↓                                                │
│  5. Kite Redirects to http://127.0.0.1:5001/            │
│         ↓                                                │
│  6. Browser Connects to localhost:5001                  │
│         ↓                                                │
│  7. SSH Forwards to EC2:5001                            │
│         ↓                                                │
│  8. Flask Receives Callback                             │
│         ↓                                                │
│  9. Token Generated & Saved                             │
│         ↓                                                │
│  10. Success! ✅                                         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## ⚠️ **Important Notes**

### **1. Kite Redirect URL**
- **Must be**: `http://127.0.0.1:5001/` or `http://localhost:5001/`
- **Cannot be**: EC2 public IP or domain (requires HTTPS)
- **Update at**: https://developers.kite.trade/apps

### **2. SSH Port Forwarding**
- Must be active during authentication
- Use `-L 5001:localhost:5001` flag
- Keep terminal open until auth completes

### **3. Flask Server**
- Must be running on EC2 before clicking login link
- Runs on port 5001
- Started by `python3 auth.py`

### **4. Token Expiry**
- Tokens expire at ~6 AM IST daily
- Need to re-authenticate each day before market opens
- Use `/checktoken` to check status

---

## 🛠️ **Troubleshooting**

### **Issue: "Connection Refused" After Login**

**Cause**: SSH port forwarding not active or Flask server not running

**Fix**:
```bash
# Check if SSH port forwarding is active
# On local machine:
netstat -an | grep 5001

# Should show: tcp4  0  0  127.0.0.1.5001  *.*  LISTEN

# If not, restart SSH with port forwarding:
ssh -i ~/Downloads/trading-bot.pem -L 5001:localhost:5001 trader@ec2...
```

### **Issue: "Invalid Redirect URL"**

**Cause**: Kite app redirect URL doesn't match

**Fix**:
1. Go to https://developers.kite.trade/apps
2. Ensure redirect URL is exactly: `http://127.0.0.1:5001/`
3. Save changes
4. Try authentication again

### **Issue: "No Request Token Received"**

**Cause**: Flask server not running when Kite redirected

**Fix**:
```bash
# In SSH session, check if Flask is running:
ps aux | grep "python.*auth.py"

# If not running, start it:
cd /home/trader/trading_bot
source .venv/bin/activate
python3 auth.py
```

### **Issue: Browser Doesn't Open**

**Cause**: Running on headless EC2 server

**Solution**:
1. Copy the URL from terminal
2. Paste in your local browser
3. Complete authentication
4. Redirect will still work via port forwarding

---

## 📋 **Checklist**

Before authenticating, ensure:

- [ ] Kite redirect URL set to `http://127.0.0.1:5001/`
- [ ] SSH port forwarding active (`-L 5001:localhost:5001`)
- [ ] Connected to EC2 via SSH
- [ ] In `/home/trader/trading_bot` directory
- [ ] Virtual environment activated
- [ ] Flask server running (`python3 auth.py`)
- [ ] Browser ready to open Kite login
- [ ] Kite credentials available
- [ ] 2FA device ready

---

## 🎯 **Daily Workflow**

### **Every Morning Before 9:15 AM:**

1. **Check Token Status**
   ```bash
   # Send to Telegram bot:
   /checktoken
   ```

2. **If Expired, Authenticate**
   ```bash
   # Terminal 1 (Local):
   ssh -i ~/Downloads/trading-bot.pem -L 5001:localhost:5001 trader@ec2...
   
   # Terminal 1 (SSH Session):
   cd /home/trader/trading_bot
   source .venv/bin/activate
   python3 auth.py
   
   # Browser: Login → 2FA → Authorize
   ```

3. **Verify Success**
   ```bash
   # Send to Telegram bot:
   /checktoken
   
   # Should show: ✅ Token Status: VALID
   ```

4. **Close SSH Session**
   ```bash
   # After successful auth, you can close the SSH session
   exit
   ```

---

## 🚀 **Alternative: Use ngrok (Temporary HTTPS)**

If you prefer not to use SSH port forwarding:

### **Install ngrok on EC2:**
```bash
cd ~
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/
```

### **Start ngrok:**
```bash
ngrok http 5001
```

### **Update Kite Redirect URL:**
Use the HTTPS URL from ngrok (e.g., `https://abc123.ngrok.io/`)

### **Authenticate:**
```bash
cd /home/trader/trading_bot
source .venv/bin/activate
python3 auth.py
```

**Note**: ngrok URL changes each time, so you'd need to update Kite redirect URL daily.

---

## ✅ **Summary**

### **Why This Works:**
- ✅ Kite allows `http://localhost` without HTTPS
- ✅ SSH port forwarding connects local to EC2
- ✅ No SSL certificate needed
- ✅ Secure authentication flow

### **Key Points:**
- Redirect URL: `http://127.0.0.1:5001/`
- SSH command: `ssh -i ~/key.pem -L 5001:localhost:5001 user@ec2`
- Auth command: `python3 auth.py`
- Keep SSH open during auth

### **Daily Routine:**
1. Check token with `/checktoken`
2. If expired → SSH with port forwarding
3. Run `python3 auth.py`
4. Login to Kite
5. Done!

---

**Ready to authenticate!** 🚀
