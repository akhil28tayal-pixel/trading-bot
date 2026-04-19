# 🧪 Telegram Authentication Test Guide

**Script**: `test_telegram_auth.py`  
**Purpose**: Comprehensive testing of Telegram connectivity and Kite authentication  
**Date**: April 19, 2026

---

## 🎯 What This Test Does

The test script performs **9 comprehensive tests**:

1. ✅ **Telegram Configuration** - Checks token and chat ID
2. ✅ **Telegram API Connectivity** - Tests connection to Telegram
3. ✅ **Send Test Message** - Sends a test message to your Telegram
4. ✅ **Kite API Configuration** - Verifies API key and secret
5. ✅ **Token File Status** - Checks if token.json exists and is valid
6. ✅ **Kite Login Link** - Generates authentication link
7. ✅ **Auth Handler Module** - Tests telegram_auth_handler.py
8. ✅ **Bot Commands** - Verifies /auth and /checktoken commands exist
9. ✅ **Comprehensive Message** - Sends detailed status to Telegram

---

## 🚀 How to Run

### **On Local Machine:**

```bash
cd /Users/akhiltayal/Desktop/trading_bot

# Run the test
python3 test_telegram_auth.py
```

### **On EC2:**

```bash
# SSH into EC2
ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com

# Navigate to project
cd /home/trader/trading_bot

# Pull latest code (includes test script)
git pull

# Activate virtual environment
source .venv/bin/activate

# Run the test
python test_telegram_auth.py
```

---

## 📊 Expected Output

### **Console Output:**

```
============================================================
  TRADING BOT - TELEGRAM AUTHENTICATION TEST SUITE
============================================================

Started: 2026-04-19 14:32:00

============================================================
  TEST 1: Telegram Configuration
============================================================
✅ PASS - Telegram Token
     Token: Set
✅ PASS - Telegram Chat ID
     Chat ID: 123456789
✅ PASS - .env File
     Path: /home/trader/trading_bot/.env

Result: 3/3 tests passed

============================================================
  TEST 2: Telegram API Connectivity
============================================================
✅ PASS - Telegram API
     Bot: @your_bot_username
     Bot Name: Trading Bot
     Bot ID: 987654321

============================================================
  TEST 3: Send Test Message
============================================================
✅ PASS - Send Message
     Check your Telegram for the test message

============================================================
  TEST 4: Kite API Configuration
============================================================
✅ PASS - Kite API Key
     Key: Set
✅ PASS - Kite API Secret
     Secret: Set

Result: 2/2 tests passed

============================================================
  TEST 5: Token File Status
============================================================
✅ PASS - Access Token
✅ PASS - Token Expiry
     Expires: 2026-04-20 06:00:00
     Time Left: 15.5 hours

============================================================
  TEST 6: Kite Login Link Generation
============================================================
✅ PASS - Login Link
     Generated successfully

     URL: https://kite.zerodha.com/connect/login?api_key=...

============================================================
  TEST 7: Telegram Auth Handler
============================================================
✅ PASS - Import Module
     telegram_auth_handler imported
✅ PASS - Token Check Function
     Valid: True, Needs Auth: False
     Expiry: 2026-04-20 06:00:00
✅ PASS - Login Link Function
     Link generated

============================================================
  TEST 8: Telegram Bot Commands
============================================================
✅ PASS - /auth Command
✅ PASS - /checktoken Command

============================================================
  Sending Comprehensive Test Message
============================================================
✅ PASS - Comprehensive Test Message
     Check Telegram for detailed test results

============================================================
  TEST SUMMARY
============================================================
✅ PASS - Telegram Config
✅ PASS - Telegram Connectivity
✅ PASS - Send Message
✅ PASS - Kite Config
✅ PASS - Token File
✅ PASS - Kite Login Link
✅ PASS - Auth Handler
✅ PASS - Bot Commands
✅ PASS - Comprehensive Message

============================================================
  TOTAL: 9/9 tests passed (100.0%)
============================================================

🎉 All tests passed! System is ready for authentication.

📱 Check your Telegram for test messages and login link!

Completed: 2026-04-19 14:32:15
```

---

## 📱 Telegram Messages You'll Receive

### **Message 1: Simple Test**
```
🧪 Telegram Test Message

This is an automated test from your trading bot.

Test Details:
• Time: 2026-04-19 14:32:05
• Mode: PAPER
• Python: 3.12.3

Status: ✅ Telegram connectivity working!

If you received this message, Telegram integration is functioning correctly.
```

### **Message 2: Comprehensive Status**
```
🧪 Trading Bot - Authentication Test

📊 System Status:
• Time: 2026-04-19 14:32:10
• Mode: PAPER
• Python: 3.12.3

🔐 Kite Authentication:
• Token Status: ✅ Valid
• Token Expiry: 06:00:00 (15.5h left)
• API Key: ✅ Set
• API Secret: ✅ Set

📱 Telegram Integration:
• Bot Token: ✅ Working (you received this message!)
• Chat ID: 123456789

🔗 Kite Login Link:
https://kite.zerodha.com/connect/login?api_key=...

✅ Available Commands:
• /auth - Get authentication link
• /checktoken - Check token status
• /status - Bot status
• /help - All commands

📝 Next Steps:
1. If token is expired, use /auth command
2. Click the login link above
3. Authorize the application
4. Token will be saved automatically

Test completed successfully! All systems operational.
```

---

## 🔍 What Each Test Checks

### **Test 1: Telegram Configuration**
- Verifies `TELEGRAM_TOKEN` is set
- Verifies `TELEGRAM_CHAT_ID` is set
- Checks `.env` file exists

### **Test 2: Telegram API Connectivity**
- Connects to Telegram API
- Retrieves bot information
- Confirms bot is active

### **Test 3: Send Test Message**
- Sends actual message via Telegram
- Tests `notifier.py` module
- Confirms end-to-end messaging works

### **Test 4: Kite API Configuration**
- Checks `KITE_API_KEY` is set
- Checks `KITE_API_SECRET` is set

### **Test 5: Token File Status**
- Checks if `token.json` exists
- Validates token structure
- Checks expiry time
- Calculates time remaining

### **Test 6: Kite Login Link**
- Generates Kite authentication URL
- Tests KiteConnect library
- Displays login link

### **Test 7: Auth Handler Module**
- Imports `telegram_auth_handler.py`
- Tests `check_token_validity()` function
- Tests `generate_kite_login_link()` function

### **Test 8: Bot Commands**
- Verifies `/auth` command exists in bot code
- Verifies `/checktoken` command exists in bot code

### **Test 9: Comprehensive Message**
- Sends detailed status report to Telegram
- Includes all system information
- Provides actionable next steps

---

## ✅ Success Criteria

**All tests should pass (9/9) if:**
- ✅ Telegram bot token is configured
- ✅ Telegram chat ID is set
- ✅ Kite API credentials are configured
- ✅ All required modules are installed
- ✅ Network connectivity is working

---

## ❌ Troubleshooting

### **Test 1 Fails: Telegram Config**
```bash
# Check .env file
cat .env | grep TELEGRAM

# Verify config.py loads correctly
python3 -c "import config; print(config.TELEGRAM_TOKEN)"
```

### **Test 2 Fails: Telegram Connectivity**
```bash
# Check internet connection
ping -c 3 api.telegram.org

# Test token manually
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
```

### **Test 3 Fails: Send Message**
```bash
# Check notifier.py
python3 -c "from notifier import send; send('Test')"

# Verify chat ID
python3 -c "import config; print(config.CHAT_ID)"
```

### **Test 4 Fails: Kite Config**
```bash
# Check Kite credentials
cat .env | grep KITE

# Verify they're loaded
python3 -c "import config; print(config.API_KEY)"
```

### **Test 5 Fails: Token File**
```bash
# Check if token.json exists
ls -lh token.json

# View token content
cat token.json

# This is normal if you haven't authenticated yet
```

### **Test 6 Fails: Kite Login Link**
```bash
# Check KiteConnect installation
pip list | grep kiteconnect

# Test manually
python3 -c "from kiteconnect import KiteConnect; print('OK')"
```

### **Test 7 Fails: Auth Handler**
```bash
# Check if file exists
ls -lh telegram_auth_handler.py

# Test import
python3 -c "import telegram_auth_handler; print('OK')"
```

### **Test 8 Fails: Bot Commands**
```bash
# Check telegram_bot.py
grep -n "/auth" deployment/telegram_bot.py
grep -n "/checktoken" deployment/telegram_bot.py
```

---

## 🔄 Running Tests Regularly

### **Before Market Open (Daily)**
```bash
# Quick test
python3 test_telegram_auth.py

# Should show token status and validity
```

### **After Code Changes**
```bash
# Full test after updates
python3 test_telegram_auth.py

# Verify all systems still working
```

### **After Deployment**
```bash
# On EC2 after deployment
cd /home/trader/trading_bot
source .venv/bin/activate
python test_telegram_auth.py
```

---

## 📝 Test Results Interpretation

### **100% Pass (9/9)**
```
🎉 Perfect! All systems operational
✅ Telegram working
✅ Kite configured
✅ Authentication ready
```

### **88% Pass (8/9) - Token File Failed**
```
⚠️ Normal if not authenticated yet
✅ System ready for first authentication
📝 Use /auth command to authenticate
```

### **< 80% Pass**
```
❌ Configuration issues detected
📋 Review failed tests
🔧 Fix issues before proceeding
```

---

## 🎯 Next Steps After Testing

### **If All Tests Pass:**
1. ✅ System is ready
2. ✅ Telegram commands available
3. ✅ Can authenticate via /auth
4. ✅ Ready for production

### **If Token Expired:**
1. Send `/auth` to Telegram bot
2. Click login link
3. Authorize application
4. Receive confirmation
5. Re-run test to verify

### **If Tests Fail:**
1. Review error messages
2. Check troubleshooting section
3. Fix configuration issues
4. Re-run test
5. Repeat until 100% pass

---

## 📊 Sample Test Run

```bash
# Run test
$ python3 test_telegram_auth.py

# Expected duration: 10-15 seconds
# Expected messages: 2 Telegram messages
# Expected result: 9/9 tests passed

# Exit code
$ echo $?
0  # Success
```

---

## ✅ Summary

**Purpose**: Verify Telegram and Kite authentication is working  
**Tests**: 9 comprehensive checks  
**Duration**: ~15 seconds  
**Output**: Console + 2 Telegram messages  
**Success**: 9/9 tests passed  

**Ready to use!** 🚀
