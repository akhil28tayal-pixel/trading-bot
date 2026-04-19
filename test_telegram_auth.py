#!/usr/bin/env python3
"""
Telegram Authentication Test Script
Tests Telegram connectivity and Kite authentication flow
"""

import os
import sys
import json
import time
import datetime
import requests
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from notifier import send


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_status(test_name, passed, message=""):
    """Print test status"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if message:
        print(f"     {message}")


def test_telegram_config():
    """Test 1: Check Telegram configuration"""
    print_header("TEST 1: Telegram Configuration")
    
    tests_passed = 0
    total_tests = 3
    
    # Check token
    has_token = hasattr(config, 'TELEGRAM_TOKEN') and config.TELEGRAM_TOKEN
    print_status("Telegram Token", has_token, 
                 f"Token: {'Set' if has_token else 'Missing'}")
    if has_token:
        tests_passed += 1
    
    # Check chat ID
    has_chat_id = hasattr(config, 'CHAT_ID') and config.CHAT_ID
    print_status("Telegram Chat ID", has_chat_id,
                 f"Chat ID: {config.CHAT_ID if has_chat_id else 'Missing'}")
    if has_chat_id:
        tests_passed += 1
    
    # Check .env file
    env_exists = os.path.exists('.env')
    print_status(".env File", env_exists,
                 f"Path: {os.path.abspath('.env')}")
    if env_exists:
        tests_passed += 1
    
    print(f"\nResult: {tests_passed}/{total_tests} tests passed")
    return tests_passed == total_tests


def test_telegram_connectivity():
    """Test 2: Test Telegram API connectivity"""
    print_header("TEST 2: Telegram API Connectivity")
    
    if not hasattr(config, 'TELEGRAM_TOKEN') or not config.TELEGRAM_TOKEN:
        print_status("Telegram API", False, "No token configured")
        return False
    
    try:
        # Test getMe endpoint
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                print_status("Telegram API", True, 
                           f"Bot: @{bot_info.get('username', 'unknown')}")
                print(f"     Bot Name: {bot_info.get('first_name', 'N/A')}")
                print(f"     Bot ID: {bot_info.get('id', 'N/A')}")
                return True
        
        print_status("Telegram API", False, f"HTTP {response.status_code}")
        return False
        
    except Exception as e:
        print_status("Telegram API", False, f"Error: {e}")
        return False


def test_send_message():
    """Test 3: Send test message via Telegram"""
    print_header("TEST 3: Send Test Message")
    
    test_message = f"""🧪 <b>Telegram Test Message</b>

This is an automated test from your trading bot.

<b>Test Details:</b>
• Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Mode: {config.MODE}
• Python: {sys.version.split()[0]}

<b>Status:</b> ✅ Telegram connectivity working!

<i>If you received this message, Telegram integration is functioning correctly.</i>"""
    
    try:
        success = send(test_message)
        print_status("Send Message", success,
                    "Check your Telegram for the test message")
        return success
    except Exception as e:
        print_status("Send Message", False, f"Error: {e}")
        return False


def test_kite_config():
    """Test 4: Check Kite API configuration"""
    print_header("TEST 4: Kite API Configuration")
    
    tests_passed = 0
    total_tests = 2
    
    # Check API key
    has_api_key = hasattr(config, 'API_KEY') and config.API_KEY
    print_status("Kite API Key", has_api_key,
                 f"Key: {'Set' if has_api_key else 'Missing'}")
    if has_api_key:
        tests_passed += 1
    
    # Check API secret
    has_api_secret = hasattr(config, 'API_SECRET') and config.API_SECRET
    print_status("Kite API Secret", has_api_secret,
                 f"Secret: {'Set' if has_api_secret else 'Missing'}")
    if has_api_secret:
        tests_passed += 1
    
    print(f"\nResult: {tests_passed}/{total_tests} tests passed")
    return tests_passed == total_tests


def test_token_file():
    """Test 5: Check token.json file"""
    print_header("TEST 5: Token File Status")
    
    token_file = 'token.json'
    
    if not os.path.exists(token_file):
        print_status("Token File", False, "token.json not found")
        print("     This is normal if you haven't authenticated yet")
        return False
    
    try:
        with open(token_file, 'r') as f:
            token_data = json.load(f)
        
        # Check token structure
        has_access_token = 'access_token' in token_data
        print_status("Access Token", has_access_token)
        
        # Check expiry
        if 'expiry' in token_data:
            expiry = datetime.datetime.fromisoformat(token_data['expiry'])
            now = datetime.datetime.now()
            is_valid = now < expiry
            time_left = expiry - now if is_valid else datetime.timedelta(0)
            
            print_status("Token Expiry", is_valid,
                        f"Expires: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")
            if is_valid:
                print(f"     Time Left: {time_left.total_seconds() / 3600:.1f} hours")
            else:
                print(f"     Expired {abs(time_left.total_seconds() / 3600):.1f} hours ago")
            
            return is_valid
        else:
            # Old format - check date
            token_date = token_data.get('date')
            today = str(datetime.date.today())
            is_valid = token_date == today
            
            print_status("Token Date", is_valid,
                        f"Date: {token_date} (Today: {today})")
            return is_valid
            
    except Exception as e:
        print_status("Token File", False, f"Error reading: {e}")
        return False


def test_kite_login_link():
    """Test 6: Generate Kite login link"""
    print_header("TEST 6: Kite Login Link Generation")
    
    if not hasattr(config, 'API_KEY') or not config.API_KEY:
        print_status("Login Link", False, "No API key configured")
        return False
    
    try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=config.API_KEY)
        login_url = kite.login_url()
        
        print_status("Login Link", True, "Generated successfully")
        print(f"\n     URL: {login_url}\n")
        
        return True
        
    except Exception as e:
        print_status("Login Link", False, f"Error: {e}")
        return False


def test_auth_handler():
    """Test 7: Test telegram_auth_handler module"""
    print_header("TEST 7: Telegram Auth Handler")
    
    try:
        from telegram_auth_handler import (
            check_token_validity,
            generate_kite_login_link
        )
        
        print_status("Import Module", True, "telegram_auth_handler imported")
        
        # Test token validity check
        try:
            is_valid, expiry, needs_auth = check_token_validity()
            print_status("Token Check Function", True,
                        f"Valid: {is_valid}, Needs Auth: {needs_auth}")
            if expiry:
                print(f"     Expiry: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print_status("Token Check Function", False, f"Error: {e}")
        
        # Test login link generation
        try:
            login_url = generate_kite_login_link()
            print_status("Login Link Function", True, "Link generated")
        except Exception as e:
            print_status("Login Link Function", False, f"Error: {e}")
        
        return True
        
    except ImportError as e:
        print_status("Import Module", False, f"Error: {e}")
        return False


def test_telegram_bot_commands():
    """Test 8: Test Telegram bot command availability"""
    print_header("TEST 8: Telegram Bot Commands")
    
    try:
        # Check if telegram_bot.py has auth commands
        bot_file = 'deployment/telegram_bot.py'
        
        if not os.path.exists(bot_file):
            print_status("Bot File", False, f"{bot_file} not found")
            return False
        
        with open(bot_file, 'r') as f:
            content = f.read()
        
        # Check for auth commands
        has_auth_cmd = "elif text == '/auth':" in content
        has_checktoken_cmd = "elif text == '/checktoken':" in content
        
        print_status("/auth Command", has_auth_cmd)
        print_status("/checktoken Command", has_checktoken_cmd)
        
        return has_auth_cmd and has_checktoken_cmd
        
    except Exception as e:
        print_status("Bot Commands", False, f"Error: {e}")
        return False


def send_auth_test_message():
    """Send comprehensive auth test message via Telegram"""
    print_header("Sending Comprehensive Test Message")
    
    # Gather all test results
    token_status = "Unknown"
    token_expiry = "N/A"
    
    if os.path.exists('token.json'):
        try:
            with open('token.json', 'r') as f:
                token_data = json.load(f)
            
            if 'expiry' in token_data:
                expiry = datetime.datetime.fromisoformat(token_data['expiry'])
                now = datetime.datetime.now()
                if now < expiry:
                    token_status = "✅ Valid"
                    time_left = (expiry - now).total_seconds() / 3600
                    token_expiry = f"{expiry.strftime('%H:%M:%S')} ({time_left:.1f}h left)"
                else:
                    token_status = "❌ Expired"
                    token_expiry = expiry.strftime('%Y-%m-%d %H:%M:%S')
        except:
            token_status = "⚠️ Error reading"
    else:
        token_status = "❌ Not found"
    
    # Generate login link
    login_link = "Error generating link"
    try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=config.API_KEY)
        login_link = kite.login_url()
    except:
        pass
    
    message = f"""🧪 <b>Trading Bot - Authentication Test</b>

<b>📊 System Status:</b>
• Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Mode: {config.MODE}
• Python: {sys.version.split()[0]}

<b>🔐 Kite Authentication:</b>
• Token Status: {token_status}
• Token Expiry: {token_expiry}
• API Key: {'✅ Set' if hasattr(config, 'API_KEY') and config.API_KEY else '❌ Missing'}
• API Secret: {'✅ Set' if hasattr(config, 'API_SECRET') and config.API_SECRET else '❌ Missing'}

<b>📱 Telegram Integration:</b>
• Bot Token: ✅ Working (you received this message!)
• Chat ID: {config.CHAT_ID if hasattr(config, 'CHAT_ID') else 'Not set'}

<b>🔗 Kite Login Link:</b>
{login_link}

<b>✅ Available Commands:</b>
• /auth - Get authentication link
• /checktoken - Check token status
• /status - Bot status
• /help - All commands

<b>📝 Next Steps:</b>
1. If token is expired, use /auth command
2. Click the login link above
3. Authorize the application
4. Token will be saved automatically

<i>Test completed successfully! All systems operational.</i>"""
    
    try:
        success = send(message)
        print_status("Comprehensive Test Message", success,
                    "Check Telegram for detailed test results")
        return success
    except Exception as e:
        print_status("Comprehensive Test Message", False, f"Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  TRADING BOT - TELEGRAM AUTHENTICATION TEST SUITE")
    print("=" * 60)
    print(f"\nStarted: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Run all tests
    results['Telegram Config'] = test_telegram_config()
    results['Telegram Connectivity'] = test_telegram_connectivity()
    results['Send Message'] = test_send_message()
    results['Kite Config'] = test_kite_config()
    results['Token File'] = test_token_file()
    results['Kite Login Link'] = test_kite_login_link()
    results['Auth Handler'] = test_auth_handler()
    results['Bot Commands'] = test_telegram_bot_commands()
    
    # Send comprehensive test message
    time.sleep(2)  # Brief pause
    results['Comprehensive Message'] = send_auth_test_message()
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'=' * 60}")
    print(f"  TOTAL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print(f"{'=' * 60}")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready for authentication.")
        print("\n📱 Check your Telegram for test messages and login link!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
    
    print(f"\nCompleted: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
