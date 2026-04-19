#!/usr/bin/env python3
"""
Telegram-based Kite Authentication Handler
Sends login link via Telegram when token expires
"""

import os
import sys
import json
import datetime
import threading
import time
from flask import Flask, request

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from auth import kite, TOKEN_FILE, _calculate_token_expiry, load_token
from notifier import send

app = Flask(__name__)
access_token_global = None
auth_in_progress = False


def check_token_validity():
    """
    Check if token is valid and not expired
    Returns: (is_valid, expiry_time, needs_auth)
    """
    if not os.path.exists(TOKEN_FILE):
        return False, None, True
    
    try:
        with open(TOKEN_FILE, 'r') as f:
            data = json.load(f)
        
        expiry_str = data.get('expiry')
        if expiry_str:
            expiry = datetime.datetime.fromisoformat(expiry_str)
            now = datetime.datetime.now()
            
            # Check if expired or expiring in next hour
            if now >= expiry:
                return False, expiry, True
            elif (expiry - now).total_seconds() < 3600:  # Less than 1 hour
                return True, expiry, True  # Valid but expiring soon
            else:
                return True, expiry, False
        else:
            # Old format, check date
            if data.get('date') != str(datetime.date.today()):
                return False, None, True
            return True, None, False
            
    except Exception as e:
        print(f"Error checking token: {e}")
        return False, None, True


def generate_kite_login_link():
    """Generate Kite login URL"""
    from kiteconnect import KiteConnect
    kite_instance = KiteConnect(api_key=config.API_KEY)
    login_url = kite_instance.login_url()
    return login_url


def send_auth_request_via_telegram():
    """Send authentication request via Telegram"""
    global auth_in_progress
    
    if auth_in_progress:
        print("Authentication already in progress")
        return False
    
    auth_in_progress = True
    
    try:
        # Generate login link
        login_url = generate_kite_login_link()
        
        # Create message
        message = f"""🔐 <b>Kite Authentication Required</b>

Your Zerodha access token has expired or is expiring soon.

<b>Please authenticate to continue trading:</b>

1️⃣ Click the link below to login to Kite
2️⃣ Authorize the application
3️⃣ You'll be redirected automatically
4️⃣ Token will be saved for today

<b>Login Link:</b>
{login_url}

<b>Note:</b> This link is valid for 10 minutes.
Authentication server is running on EC2.

<i>After successful login, you'll receive a confirmation message.</i>"""
        
        # Send via Telegram
        success = send(message)
        
        if success:
            print("✅ Authentication request sent via Telegram")
            return True
        else:
            print("❌ Failed to send Telegram message")
            return False
            
    except Exception as e:
        print(f"Error sending auth request: {e}")
        auth_in_progress = False
        return False


@app.route("/")
def login_callback():
    """Handle Kite login callback"""
    global access_token_global, auth_in_progress
    
    request_token = request.args.get("request_token")
    
    if not request_token:
        return "No request token received"
    
    try:
        # Generate session
        session = kite.generate_session(
            request_token,
            api_secret=config.API_SECRET
        )
        
        access_token = session["access_token"]
        expiry = _calculate_token_expiry()
        
        # Save token
        with open(TOKEN_FILE, "w") as f:
            json.dump({
                "access_token": access_token,
                "date": str(datetime.date.today()),
                "created_at": datetime.datetime.now().isoformat(),
                "expiry": expiry.isoformat(),
            }, f)
        
        access_token_global = access_token
        config.ACCESS_TOKEN = access_token
        
        print("✅ Access token generated and saved")
        
        # Send success notification via Telegram
        success_message = f"""✅ <b>Authentication Successful!</b>

Your Zerodha access token has been generated and saved.

<b>Token Details:</b>
• Created: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Expires: {expiry.strftime('%Y-%m-%d %H:%M:%S')}
• Valid for: ~{(expiry - datetime.datetime.now()).total_seconds() / 3600:.1f} hours

<b>Trading bot is now ready!</b>

The bot will automatically start trading during market hours (9:15 AM - 3:30 PM).

<i>You can check status with /status command.</i>"""
        
        send(success_message)
        
        auth_in_progress = False
        
        return """
        <html>
        <head><title>Authentication Successful</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1 style="color: green;">✅ Authentication Successful!</h1>
            <p>Your access token has been saved.</p>
            <p>You can close this window and check Telegram for confirmation.</p>
            <p><strong>Trading bot is ready to trade!</strong></p>
        </body>
        </html>
        """
        
    except Exception as e:
        error_msg = f"Authentication failed: {e}"
        print(f"❌ {error_msg}")
        
        # Send error notification
        send(f"❌ <b>Authentication Failed</b>\n\n{error_msg}\n\nPlease try again with /auth command.")
        
        auth_in_progress = False
        
        return f"""
        <html>
        <head><title>Authentication Failed</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1 style="color: red;">❌ Authentication Failed</h1>
            <p>{error_msg}</p>
            <p>Please check Telegram and try again.</p>
        </body>
        </html>
        """


def start_auth_server():
    """Start Flask authentication server"""
    print("🔐 Starting authentication server on port 5001...")
    app.run(host="0.0.0.0", port=5001, use_reloader=False)


def check_and_request_auth_if_needed():
    """
    Check token validity and request authentication if needed
    Returns: True if token is valid, False if auth needed
    """
    is_valid, expiry, needs_auth = check_token_validity()
    
    if needs_auth:
        print("⚠️ Token expired or expiring soon - requesting authentication")
        
        # Start auth server in background
        server_thread = threading.Thread(target=start_auth_server, daemon=True)
        server_thread.start()
        
        # Wait a moment for server to start
        time.sleep(2)
        
        # Send auth request via Telegram
        send_auth_request_via_telegram()
        
        return False
    else:
        if expiry:
            print(f"✅ Token valid until {expiry.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("✅ Token valid for today")
        return True


def schedule_morning_auth_check():
    """
    Schedule daily authentication check at 8:00 AM
    This runs continuously and checks every morning
    """
    print("📅 Starting daily authentication scheduler...")
    
    while True:
        now = datetime.datetime.now()
        
        # Check if it's 8:00 AM
        if now.hour == 8 and now.minute == 0:
            print(f"🌅 Morning check at {now.strftime('%Y-%m-%d %H:%M:%S')}")
            
            is_valid, expiry, needs_auth = check_token_validity()
            
            if needs_auth:
                message = f"""🌅 <b>Good Morning!</b>

It's time to authenticate for today's trading session.

Your Zerodha access token has expired.

<b>Please authenticate now to enable trading at 9:15 AM.</b>

Use /auth command to get the login link."""
                
                send(message)
                
                # Also send the auth link directly
                check_and_request_auth_if_needed()
            else:
                message = f"""🌅 <b>Good Morning!</b>

Your authentication is valid for today.

<b>Token Status:</b>
• Valid until: {expiry.strftime('%H:%M:%S') if expiry else 'End of day'}
• Trading starts: 9:15 AM
• Mode: {config.MODE}

<b>Bot is ready to trade!</b>

Use /status to check bot status."""
                
                send(message)
            
            # Sleep for 60 seconds to avoid multiple triggers
            time.sleep(60)
        
        # Check every minute
        time.sleep(60)


if __name__ == "__main__":
    print("🚀 Telegram Auth Handler Started")
    print("=" * 50)
    
    # Check current token status
    is_valid, expiry, needs_auth = check_token_validity()
    
    if needs_auth:
        print("⚠️ Token needs authentication")
        check_and_request_auth_if_needed()
    else:
        print(f"✅ Token is valid")
        if expiry:
            print(f"   Expires: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Start daily scheduler
    schedule_morning_auth_check()
