# 🔐 Telegram-Based Kite Authentication Guide

**Feature**: Automated Kite token generation through Telegram messages  
**Status**: ✅ Implemented and Ready  
**Date**: April 19, 2026

---

## 🎯 Overview

This system automates Kite authentication by:
1. ✅ Checking token expiry every morning at 8:00 AM
2. ✅ Sending Kite login link via Telegram if token is expired
3. ✅ Handling authentication callback automatically
4. ✅ Notifying when authentication is complete
5. ✅ Manual authentication via `/auth` command anytime

---

## 📋 How It Works

### **Automatic Morning Check (8:00 AM Daily)**

Every morning at 8:00 AM, the system:
1. Checks if Zerodha access token is valid
2. If expired → Sends Telegram message with login link
3. You click the link → Login to Kite → Done!
4. Token saved automatically for the day
5. Bot ready to trade at 9:15 AM

### **Manual Authentication (Anytime)**

Use `/auth` command in Telegram:
1. Send `/auth` to the bot
2. Receive Kite login link instantly
3. Click link → Login → Authorize
4. Receive confirmation message
5. Ready to trade!

---

## 🚀 Setup Instructions

### **Step 1: Deploy Updated Code to EC2**

```bash
# SSH into EC2
ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com

# Navigate to project
cd /home/trader/trading_bot

# Pull latest changes
git pull

# Restart services
sudo supervisorctl restart all
```

### **Step 2: Verify Setup**

```bash
# Check if telegram_auth_handler.py exists
ls -lh telegram_auth_handler.py

# Check if Telegram bot has new commands
sudo supervisorctl tail telegram_bot stdout | grep -i "auth"
```

### **Step 3: Test Authentication**

Send `/auth` to your Telegram bot - you should receive a Kite login link!

---

## 📱 Telegram Commands

### **Authentication Commands**

#### `/auth` - Get Kite Login Link
```
🔐 Kite Authentication

Click the link below to authenticate:

https://kite.zerodha.com/connect/login?api_key=...

Steps:
1️⃣ Click the link
2️⃣ Login to Zerodha Kite
3️⃣ Authorize the application
4️⃣ You'll be redirected automatically

Note: Link valid for 10 minutes.
```

#### `/checktoken` - Check Token Status
```
✅ Token Status: VALID

Your Zerodha access token is active.

Token Details:
• Status: Active
• Expires: 2026-04-20 06:00:00
• Time Left: 15.5 hours

Bot is ready to trade!
```

---

## 🌅 Morning Authentication Flow

### **Scenario 1: Token Expired**

**8:00 AM - Automatic Check:**
```
🌅 Good Morning!

It's time to authenticate for today's trading session.

Your Zerodha access token has expired.

Please authenticate now to enable trading at 9:15 AM.

Use /auth command to get the login link.
```

**You send `/auth`:**
```
🔐 Kite Authentication

Click the link below to authenticate:
[Login Link]
```

**After clicking and logging in:**
```
✅ Authentication Successful!

Your Zerodha access token has been generated and saved.

Token Details:
• Created: 2026-04-20 08:05:00
• Expires: 2026-04-21 06:00:00
• Valid for: ~22.0 hours

Trading bot is now ready!
```

### **Scenario 2: Token Valid**

**8:00 AM - Automatic Check:**
```
🌅 Good Morning!

Your authentication is valid for today.

Token Status:
• Valid until: 06:00:00
• Trading starts: 9:15 AM
• Mode: PAPER

Bot is ready to trade!
```

---

## 🔧 Technical Details

### **Files Created**

1. **`telegram_auth_handler.py`** - Main authentication handler
   - Token validity checker
   - Login link generator
   - Flask authentication server
   - Morning scheduler (8:00 AM check)
   - Telegram notification sender

2. **`deployment/telegram_bot.py`** - Updated with auth commands
   - `/auth` - Request authentication
   - `/checktoken` - Check token status

### **How Authentication Works**

```
┌─────────────────────────────────────────────────────────┐
│                  AUTHENTICATION FLOW                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. User sends /auth command                            │
│         ↓                                                │
│  2. Bot starts Flask server on port 5001                │
│         ↓                                                │
│  3. Bot generates Kite login URL                        │
│         ↓                                                │
│  4. Bot sends URL via Telegram                          │
│         ↓                                                │
│  5. User clicks URL → Opens Kite login                  │
│         ↓                                                │
│  6. User logs in → Kite redirects to EC2:5001           │
│         ↓                                                │
│  7. Flask receives request_token                        │
│         ↓                                                │
│  8. Flask generates access_token                        │
│         ↓                                                │
│  9. Flask saves token.json                              │
│         ↓                                                │
│  10. Flask sends success message via Telegram           │
│         ↓                                                │
│  11. Bot ready to trade!                                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### **Token Expiry Logic**

- Zerodha tokens expire at **6:00 AM IST** daily
- System checks at **8:00 AM IST** (2 hours before market open)
- Gives you time to authenticate before 9:15 AM market open
- Token valid for ~24 hours from generation

### **Port Configuration**

- **Flask Server**: Port 5001 (EC2)
- **Accessible from**: Internet (public IP)
- **Security**: Callback URL must match registered redirect URI

---

## 🛠️ Configuration

### **Required Environment Variables (.env)**

```bash
# Kite API
KITE_API_KEY=your_api_key
KITE_API_SECRET=your_api_secret

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Trading
TRADING_MODE=PAPER
TRADING_CAPITAL=100000
```

### **EC2 Security Group**

Ensure port 5001 is open for incoming connections:
```
Type: Custom TCP
Port: 5001
Source: 0.0.0.0/0 (or your IP)
```

### **Kite API Settings**

Redirect URL must be set to:
```
http://ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com:5001/
```

---

## 📊 Usage Examples

### **Daily Routine**

**Morning (8:00 AM):**
1. Receive morning message from bot
2. If token expired → Receive `/auth` prompt
3. Send `/auth` command
4. Click login link
5. Login to Kite
6. Receive confirmation
7. Bot ready for 9:15 AM trading

**During Day:**
- Bot trades automatically (9:15 AM - 3:30 PM)
- No manual intervention needed
- Monitor via `/status` command

**Evening:**
- Bot stops trading at 3:30 PM
- Token remains valid until 6:00 AM next day

### **Weekend Behavior**

- No authentication needed on weekends
- Bot in sleep mode
- Monday morning → Automatic auth check at 8:00 AM

---

## 🔍 Troubleshooting

### **Issue: Not Receiving Morning Messages**

**Check:**
```bash
# Verify telegram_auth_handler is running
ps aux | grep telegram_auth_handler

# Check Telegram bot token
echo $TELEGRAM_BOT_TOKEN

# Test Telegram connectivity
python3 -c "from notifier import send; send('Test message')"
```

### **Issue: /auth Command Not Working**

**Check:**
```bash
# Verify telegram_bot.py has auth commands
grep -A 10 "elif text == '/auth'" deployment/telegram_bot.py

# Restart Telegram bot
sudo supervisorctl restart telegram_bot

# Check logs
tail -f logs/telegram_bot.log
```

### **Issue: Authentication Link Not Working**

**Check:**
1. EC2 security group allows port 5001
2. Flask server is running: `netstat -tulpn | grep 5001`
3. Kite redirect URL matches EC2 public IP
4. Link not expired (valid for 10 minutes)

### **Issue: Token Not Saving**

**Check:**
```bash
# Verify token.json permissions
ls -lh token.json

# Check if token.json is being created
watch -n 1 'ls -lh token.json'

# Check Flask logs
sudo supervisorctl tail telegram_bot stderr
```

---

## ✅ Verification Checklist

### **Before Going Live**

- [ ] Updated code deployed to EC2
- [ ] Telegram bot restarted
- [ ] `/auth` command works
- [ ] `/checktoken` command works
- [ ] Morning message test (change time to current time + 1 min)
- [ ] Authentication flow tested end-to-end
- [ ] Token saved successfully
- [ ] Confirmation message received
- [ ] Bot can access saved token

### **Daily Checklist**

- [ ] Check morning message (8:00 AM)
- [ ] Authenticate if needed (before 9:15 AM)
- [ ] Verify token with `/checktoken`
- [ ] Confirm bot status with `/status`
- [ ] Monitor trading (9:15 AM - 3:30 PM)

---

## 🎯 Benefits

### **Convenience**
- ✅ No need to SSH into EC2
- ✅ No need to run auth scripts manually
- ✅ Authenticate from anywhere via Telegram
- ✅ Automatic morning reminders

### **Reliability**
- ✅ Never miss authentication
- ✅ Automatic token expiry checks
- ✅ Proactive notifications
- ✅ Confirmation messages

### **Security**
- ✅ Secure OAuth flow
- ✅ Token stored safely on EC2
- ✅ No credentials in Telegram
- ✅ Standard Zerodha authentication

---

## 📝 Summary

### **What This Solves**
- ❌ **Before**: Manual SSH + auth script every morning
- ✅ **After**: Click Telegram link, login, done!

### **Key Features**
1. Automatic morning check (8:00 AM)
2. Telegram-based authentication
3. Manual `/auth` command anytime
4. Token status checking
5. Success/failure notifications

### **User Experience**
```
8:00 AM → Receive message
8:05 AM → Click link, login
8:06 AM → Receive confirmation
9:15 AM → Bot starts trading automatically
```

**Simple, automated, and reliable!** 🎉

---

**Status**: ✅ Ready to Use  
**Next Step**: Deploy to EC2 and test `/auth` command  
**Support**: Check logs in `logs/telegram_bot.log`
