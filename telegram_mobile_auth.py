#!/usr/bin/env python3
"""
Mobile-Friendly Telegram Authentication Handler
Authenticate from anywhere using ngrok HTTPS tunnel
No SSH required - works entirely from Telegram mobile app!
"""

import os
import sys
import json
import datetime
import threading
import time
import subprocess
import requests
from flask import Flask, request

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from auth import kite, TOKEN_FILE, _calculate_token_expiry
from notifier import send

app = Flask(__name__)
access_token_global = None
auth_in_progress = False
ngrok_url = None
ngrok_process = None


def start_ngrok():
    """Start ngrok tunnel and return public HTTPS URL"""
    global ngrok_process, ngrok_url
    
    print("🚀 Starting ngrok tunnel...")
    
    # Start ngrok
    try:
        ngrok_process = subprocess.Popen(
            ['ngrok', 'http', '5001', '--log=stdout'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for ngrok to start
        time.sleep(3)
        
        # Get public URL from ngrok API
        response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
        data = response.json()
        
        if data.get('tunnels'):
            ngrok_url = data['tunnels'][0]['public_url']
            
            # Ensure it's HTTPS
            if ngrok_url.startswith('http://'):
                ngrok_url = ngrok_url.replace('http://', 'https://')
            
            print(f"✅ ngrok tunnel created: {ngrok_url}")
            return ngrok_url
        else:
            print("❌ No tunnels found")
            return None
            
    except Exception as e:
        print(f"❌ Error starting ngrok: {e}")
        return None


def stop_ngrok():
    """Stop ngrok tunnel"""
    global ngrok_process
    
    if ngrok_process:
        print("🛑 Stopping ngrok...")
        ngrok_process.terminate()
        ngrok_process = None
        print("✅ ngrok stopped")


def check_token_validity():
    """Check if token is valid and not expired"""
    if not os.path.exists(TOKEN_FILE):
        return False, None, True
    
    try:
        with open(TOKEN_FILE, 'r') as f:
            data = json.load(f)
        
        expiry_str = data.get('expiry')
        if expiry_str:
            expiry = datetime.datetime.fromisoformat(expiry_str)
            now = datetime.datetime.now()
            
            if now >= expiry:
                return False, expiry, True
            elif (expiry - now).total_seconds() < 3600:
                return True, expiry, True
            else:
                return True, expiry, False
        else:
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


def send_mobile_auth_request():
    """Send mobile-friendly authentication request via Telegram"""
    global auth_in_progress, ngrok_url
    
    if auth_in_progress:
        send("⚠️ Authentication already in progress. Please wait...")
        return False
    
    auth_in_progress = True
    
    try:
        # Start ngrok tunnel
        ngrok_url = start_ngrok()
        
        if not ngrok_url:
            send("❌ Failed to create HTTPS tunnel. Please try again.")
            auth_in_progress = False
            return False
        
        # Start Flask server in background
        server_thread = threading.Thread(target=start_flask_server, daemon=True)
        server_thread.start()
        time.sleep(2)
        
        # Generate login link
        login_url = generate_kite_login_link()
        
        # Send message with clickable link
        message = f"""🔐 <b>Kite Authentication - Mobile Ready!</b>

✅ <b>HTTPS URL Created!</b>

Your authentication is ready. Just click the link below:

<b>👉 <a href="{login_url}">Click Here to Login to Kite</a></b>

<b>📱 Steps:</b>
1️⃣ Click the link above (works on mobile!)
2️⃣ Login with your Kite credentials
3️⃣ Enter 2FA code
4️⃣ Click "Authorize"
5️⃣ Done! Token saved automatically

<b>🔗 Technical Details:</b>
• HTTPS URL: {ngrok_url}
• Redirect URL: {ngrok_url}/
• Valid for: 2 hours

<b>⚠️ Important:</b>
• Update Kite redirect URL to: <code>{ngrok_url}/</code>
• Link expires in 10 minutes
• You'll receive confirmation after success

<i>Authenticate from anywhere - no computer needed!</i>"""
        
        success = send(message)
        
        if success:
            print("✅ Mobile auth request sent via Telegram")
            return True
        else:
            print("❌ Failed to send Telegram message")
            stop_ngrok()
            auth_in_progress = False
            return False
            
    except Exception as e:
        print(f"Error sending auth request: {e}")
        stop_ngrok()
        auth_in_progress = False
        return False


@app.route("/")
def login_callback():
    """Handle Kite login callback"""
    global access_token_global, auth_in_progress
    
    request_token = request.args.get("request_token")
    
    if not request_token:
        return """
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>No Request Token</title>
        </head>
        <body style="font-family: Arial; text-align: center; padding: 20px;">
            <h1 style="color: orange;">⚠️ No Request Token</h1>
            <p>Please try authentication again.</p>
        </body>
        </html>
        """
    
    try:
        # Generate session
        from kiteconnect import KiteConnect
        kite_instance = KiteConnect(api_key=config.API_KEY)
        
        session = kite_instance.generate_session(
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
        
        # Send success notification
        success_message = f"""✅ <b>Authentication Successful!</b>

Your Zerodha access token has been saved.

<b>Token Details:</b>
• Created: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Expires: {expiry.strftime('%Y-%m-%d %H:%M:%S')}
• Valid for: ~{(expiry - datetime.datetime.now()).total_seconds() / 3600:.1f} hours

<b>🎉 Trading bot is now ready!</b>

The bot will automatically trade during market hours (9:15 AM - 3:30 PM).

You can check status anytime with /status command.

<i>You can close this page now.</i>"""
        
        send(success_message)
        
        # Stop ngrok after successful auth
        threading.Timer(5.0, stop_ngrok).start()
        
        auth_in_progress = False
        
        return """
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Success!</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .container {
                    background: white;
                    color: #333;
                    padding: 40px;
                    border-radius: 20px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    max-width: 500px;
                }
                h1 { color: #28a745; margin-bottom: 20px; }
                .emoji { font-size: 64px; margin: 20px 0; }
                p { font-size: 16px; line-height: 1.6; }
                .button {
                    display: inline-block;
                    margin-top: 20px;
                    padding: 12px 30px;
                    background: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 25px;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="emoji">✅</div>
                <h1>Authentication Successful!</h1>
                <p>Your Zerodha access token has been saved.</p>
                <p><strong>Trading bot is ready!</strong></p>
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    Check Telegram for confirmation.<br>
                    You can close this page now.
                </p>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        error_msg = f"Authentication failed: {e}"
        print(f"❌ {error_msg}")
        
        send(f"❌ <b>Authentication Failed</b>\n\n{error_msg}\n\nPlease try again with /auth command.")
        
        stop_ngrok()
        auth_in_progress = False
        
        return f"""
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Authentication Failed</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 20px;
                    background: #fff0f0;
                }}
                h1 {{ color: #dc3545; }}
                .error {{ color: #d00; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>❌ Authentication Failed</h1>
            <p class="error">{error_msg}</p>
            <p>Please check Telegram and try again.</p>
        </body>
        </html>
        """


def start_flask_server():
    """Start Flask authentication server"""
    print("🔐 Starting Flask server on port 5001...")
    app.run(host="0.0.0.0", port=5001, use_reloader=False)


if __name__ == "__main__":
    print("📱 Mobile-Friendly Telegram Auth Handler Started")
    print("=" * 60)
    
    # Check if ngrok is installed
    try:
        subprocess.run(['ngrok', 'version'], capture_output=True, check=True)
        print("✅ ngrok is installed")
    except:
        print("❌ ngrok not found!")
        print("   Install with: wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz")
        sys.exit(1)
    
    # Check token status
    is_valid, expiry, needs_auth = check_token_validity()
    
    if needs_auth:
        print("⚠️ Token needs authentication")
        print("   Send /auth to your Telegram bot to start")
    else:
        print(f"✅ Token is valid")
        if expiry:
            print(f"   Expires: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("=" * 60)
    print("Waiting for /auth command from Telegram...")
    
    # Keep running
    while True:
        time.sleep(60)
