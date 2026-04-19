# 📱 Mobile Kite Authentication Guide

**Authenticate from anywhere using just your phone!**  
**No SSH, no computer needed - just Telegram!**  
**Date**: April 19, 2026

---

## 🎯 Overview

This solution allows you to authenticate with Kite entirely from your mobile phone via Telegram. No SSH, no computer required!

### **How It Works:**
1. Send `/auth` to Telegram bot (from your phone)
2. Bot creates temporary HTTPS URL using ngrok
3. Bot sends you clickable Kite login link
4. Click link → Login → Done!
5. Token saved automatically

---

## 🚀 **One-Time Setup (On EC2)**

### **Step 1: Install ngrok**

SSH into EC2 once to install ngrok:

```bash
ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com

# Install ngrok
cd ~
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/
rm ngrok-v3-stable-linux-amd64.tgz

# Verify installation
ngrok version

# Exit
exit
```

### **Step 2: Deploy Updated Code**

```bash
# On your local machine
cd /Users/akhiltayal/Desktop/trading_bot
./update_ec2_telegram.sh
```

### **Step 3: Update Kite Redirect URL**

**Important**: You'll need to update the Kite redirect URL each time you authenticate (ngrok URL changes).

The bot will tell you the URL to use!

---

## 📱 **Daily Authentication (From Mobile)**

### **Step 1: Send /auth to Telegram Bot**

Open Telegram on your phone and send:
```
/auth
```

### **Step 2: Wait for Setup**

You'll receive:
```
🔐 Starting Mobile Authentication...

⏳ Please wait while I set up the HTTPS tunnel...

This will take about 5-10 seconds.

You'll receive a clickable link shortly!
```

### **Step 3: Receive Login Link**

After 5-10 seconds, you'll get:
```
🔐 Kite Authentication - Mobile Ready!

✅ HTTPS URL Created!

Your authentication is ready. Just click the link below:

👉 Click Here to Login to Kite

📱 Steps:
1️⃣ Click the link above (works on mobile!)
2️⃣ Login with your Kite credentials
3️⃣ Enter 2FA code
4️⃣ Click "Authorize"
5️⃣ Done! Token saved automatically

🔗 Technical Details:
• HTTPS URL: https://abc123.ngrok.io
• Redirect URL: https://abc123.ngrok.io/
• Valid for: 2 hours

⚠️ Important:
• Update Kite redirect URL to: https://abc123.ngrok.io/
• Link expires in 10 minutes
• You'll receive confirmation after success

Authenticate from anywhere - no computer needed!
```

### **Step 4: Update Kite Redirect URL**

**On your phone:**
1. Go to https://developers.kite.trade/apps
2. Click on your app
3. Update **Redirect URL** to the URL from the message (e.g., `https://abc123.ngrok.io/`)
4. Save

### **Step 5: Click Login Link**

Click the "Click Here to Login to Kite" link in the Telegram message.

### **Step 6: Complete Authentication**

1. Enter your Kite user ID and password
2. Enter 2FA code
3. Click "Authorize"
4. You'll see a success page
5. Done!

### **Step 7: Receive Confirmation**

You'll get a confirmation message:
```
✅ Authentication Successful!

Your Zerodha access token has been saved.

Token Details:
• Created: 2026-04-19 15:30:00
• Expires: 2026-04-20 06:00:00
• Valid for: ~14.5 hours

🎉 Trading bot is now ready!

The bot will automatically trade during market hours (9:15 AM - 3:30 PM).

You can check status anytime with /status command.

You can close this page now.
```

---

## 🔄 **Complete Mobile Workflow**

```
1. Open Telegram on phone
2. Send: /auth
3. Wait 5-10 seconds
4. Receive clickable link
5. Update Kite redirect URL (from message)
6. Click login link
7. Login to Kite (password + 2FA)
8. Authorize
9. See success page
10. Receive confirmation on Telegram
11. Done! ✅
```

**Total time: ~2 minutes**

---

## 📋 **What Happens Behind the Scenes**

```
┌─────────────────────────────────────────────────────────┐
│           MOBILE AUTHENTICATION FLOW                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. You send /auth from Telegram (mobile)               │
│         ↓                                                │
│  2. Bot starts ngrok on EC2                             │
│         ↓                                                │
│  3. ngrok creates HTTPS URL (e.g., abc123.ngrok.io)     │
│         ↓                                                │
│  4. Bot starts Flask server on EC2:5001                 │
│         ↓                                                │
│  5. Bot sends you Kite login link via Telegram          │
│         ↓                                                │
│  6. You click link on mobile                            │
│         ↓                                                │
│  7. Kite login page opens                               │
│         ↓                                                │
│  8. You login (password + 2FA)                          │
│         ↓                                                │
│  9. Kite redirects to https://abc123.ngrok.io/          │
│         ↓                                                │
│  10. ngrok forwards to EC2:5001                         │
│         ↓                                                │
│  11. Flask receives callback                            │
│         ↓                                                │
│  12. Token generated & saved                            │
│         ↓                                                │
│  13. Success message sent to Telegram                   │
│         ↓                                                │
│  14. ngrok tunnel closed                                │
│         ↓                                                │
│  15. Done! ✅                                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## ⚠️ **Important Notes**

### **1. ngrok URL Changes Each Time**
- ngrok free tier gives you a new URL each time
- You must update Kite redirect URL before each authentication
- The bot tells you the exact URL to use

### **2. Update Kite Redirect URL**
- **Before clicking login link**, update the redirect URL
- Go to: https://developers.kite.trade/apps
- Update to the URL from Telegram message
- Save changes

### **3. Link Expiry**
- Kite login link expires in 10 minutes
- ngrok tunnel stays active for 2 hours
- If expired, just send `/auth` again

### **4. One Authentication Per Day**
- Tokens expire at ~6 AM IST daily
- Authenticate once before market opens (9:15 AM)
- Valid for entire trading day

---

## 🛠️ **Troubleshooting**

### **Issue: "ngrok not found"**

**Solution:**
```bash
# SSH into EC2
ssh -i ~/Downloads/trading-bot.pem trader@ec2...

# Install ngrok
cd ~
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/

# Verify
ngrok version
```

### **Issue: "Invalid Redirect URL"**

**Cause**: Kite redirect URL doesn't match ngrok URL

**Solution**:
1. Check the URL in Telegram message
2. Go to https://developers.kite.trade/apps
3. Update redirect URL to match exactly
4. Include the trailing slash: `https://abc123.ngrok.io/`

### **Issue: "Connection Refused"**

**Cause**: Flask server not running or ngrok tunnel failed

**Solution**:
```bash
# Check if bot is running
sudo supervisorctl status

# Restart if needed
sudo supervisorctl restart all

# Try /auth again
```

### **Issue: "Authentication Failed"**

**Possible causes**:
- Wrong Kite credentials
- 2FA code expired
- API key/secret incorrect

**Solution**:
- Verify Kite credentials
- Use fresh 2FA code
- Check .env file has correct API key/secret

---

## 📊 **Comparison: Old vs New Method**

### **Old Method (SSH Required)**
```
❌ Need computer
❌ Need to SSH into EC2
❌ Need to run commands
❌ Need port forwarding
❌ Complex setup
⏱️ Time: 5-10 minutes
```

### **New Method (Mobile Only)**
```
✅ Just your phone
✅ Just Telegram
✅ One command: /auth
✅ Click link and login
✅ Super simple
⏱️ Time: 2 minutes
```

---

## 🎯 **Daily Routine**

### **Morning (Before 9:15 AM)**

**On your phone:**

1. Open Telegram
2. Send `/checktoken` to bot
3. If expired:
   - Send `/auth`
   - Wait for link
   - Update Kite redirect URL
   - Click link
   - Login
   - Done!
4. If valid:
   - Nothing to do!
   - Bot ready to trade

**That's it!** ✅

---

## 💡 **Pro Tips**

### **1. Save Kite App Page**
Bookmark https://developers.kite.trade/apps on your phone for quick access.

### **2. Use Password Manager**
Store Kite credentials in your phone's password manager for quick login.

### **3. Enable Biometric 2FA**
If Kite supports it, use fingerprint/face ID for faster 2FA.

### **4. Morning Routine**
Set a reminder at 8:30 AM to check token status and authenticate if needed.

### **5. Keep Telegram Notifications On**
So you get the login link immediately.

---

## ✅ **Summary**

### **Setup (One Time)**
1. Install ngrok on EC2
2. Deploy updated code
3. Done!

### **Daily Use (From Phone)**
1. Send `/auth` to Telegram
2. Update Kite redirect URL
3. Click login link
4. Login to Kite
5. Done!

### **Benefits**
- ✅ Authenticate from anywhere
- ✅ No computer needed
- ✅ No SSH needed
- ✅ Works on mobile
- ✅ Super fast (2 minutes)
- ✅ Fully automated

---

**Ready to authenticate from your phone!** 📱🚀

Just send `/auth` to your Telegram bot and follow the instructions!
