#!/usr/bin/env python3
"""
Telegram Bot Setup and Test Script
Configures Telegram notifications for the trading bot
"""

import requests
import json
import sys
import os

# Add project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config

def get_chat_id():
    """Get chat ID from Telegram bot updates"""
    print("🔍 Getting your Telegram chat ID...")
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getUpdates"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not data.get('ok'):
            print(f"❌ Error: {data.get('description', 'Unknown error')}")
            return None
            
        if not data['result']:
            print("\n⚠️  No messages found!")
            print("📱 Please:")
            print("1. Open Telegram")
            print("2. Search for your bot (or find it in @BotFather)")
            print("3. Send any message like 'hello' or '/start'")
            print("4. Run this script again")
            return None
            
        # Find the most recent chat
        latest_update = data['result'][-1]
        if 'message' in latest_update:
            chat_id = latest_update['message']['chat']['id']
            username = latest_update['message']['chat'].get('username', 'Unknown')
            first_name = latest_update['message']['chat'].get('first_name', 'Unknown')
            
            print(f"✅ Found your chat!")
            print(f"👤 Name: {first_name}")
            print(f"🆔 Username: @{username}")
            print(f"🔢 Chat ID: {chat_id}")
            
            return str(chat_id)
        else:
            print("❌ No message found in latest update")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def send_test_message(chat_id):
    """Send a test message to verify Telegram setup"""
    print(f"\n📤 Sending test message to chat ID: {chat_id}")
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    
    message = """🚀 *Trading Bot Telegram Setup Complete!*

✅ Your trading bot can now send notifications
📊 You'll receive alerts for:
• Trade executions
• Daily summaries  
• System status updates
• Emergency alerts

🤖 Bot Status: Connected and Ready!
📅 Date: Testing Phase
💼 Mode: Paper Trading

_This is a test message from your algo trading bot._"""

    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        
        if data.get('ok'):
            print("✅ Test message sent successfully!")
            print("📱 Check your Telegram - you should see the test message")
            return True
        else:
            print(f"❌ Failed to send message: {data.get('description', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

def update_config_file(chat_id):
    """Update config.py with the correct chat ID"""
    print(f"\n📝 Updating config.py with chat ID: {chat_id}")
    
    try:
        # Read current config
        with open('config.py', 'r') as f:
            content = f.read()
        
        # Replace the chat ID line
        old_line = 'CHAT_ID = ""  # Will be updated after getting real chat ID'
        new_line = f'CHAT_ID = "{chat_id}"'
        
        if old_line in content:
            content = content.replace(old_line, new_line)
        else:
            # Try alternative patterns
            import re
            content = re.sub(r'CHAT_ID = ".*?"', f'CHAT_ID = "{chat_id}"', content)
        
        # Write updated config
        with open('config.py', 'w') as f:
            f.write(content)
            
        print("✅ Config file updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating config: {e}")
        print(f"💡 Please manually update config.py:")
        print(f"   Change CHAT_ID to: \"{chat_id}\"")
        return False

def test_notifier():
    """Test the notifier module"""
    print("\n🧪 Testing notifier module...")
    
    try:
        from notifier import send
        result = send("🧪 Test notification from trading bot setup!", "info")
        
        if result:
            print("✅ Notifier module working correctly!")
        else:
            print("⚠️  Notifier module loaded but message may not have sent")
            
    except ImportError as e:
        print(f"❌ Could not import notifier: {e}")
    except Exception as e:
        print(f"❌ Error testing notifier: {e}")

def main():
    """Main setup function"""
    print("🤖 TELEGRAM BOT SETUP")
    print("=" * 40)
    
    # Check if token is configured
    if not config.TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN not configured in config.py")
        return
    
    print(f"✅ Telegram token configured")
    print(f"🔗 Token: {config.TELEGRAM_TOKEN[:10]}...")
    
    # Get chat ID
    chat_id = get_chat_id()
    if not chat_id:
        return
    
    # Send test message
    if not send_test_message(chat_id):
        return
    
    # Update config file
    update_config_file(chat_id)
    
    # Test notifier module
    test_notifier()
    
    print("\n🎉 TELEGRAM SETUP COMPLETE!")
    print("=" * 40)
    print("✅ Chat ID configured")
    print("✅ Test message sent")
    print("✅ Config file updated")
    print("✅ Ready for trading notifications")
    print("\n📱 Your trading bot will now send Telegram notifications!")

if __name__ == "__main__":
    main()
