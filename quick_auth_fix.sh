#!/bin/bash
# Quick fix for mobile authentication - Direct Flask approach
# Bypasses ngrok and uses direct IP with port opening

echo "Quick Authentication Fix"
echo "========================"
echo ""

ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com << 'ENDSSH'

echo "1. Opening port 5001 in firewall..."
sudo ufw allow 5001/tcp 2>/dev/null || echo "UFW not configured, skipping firewall rule"

echo ""
echo "2. Creating direct mobile auth (no ngrok)..."
cat > /home/trader/trading_bot/mobile_auth_direct.py << 'PYEOF'
#!/usr/bin/env python3
"""
Direct Mobile Authentication - No ngrok required
Uses EC2 public IP directly with port 5001
"""

import os
import sys
import json
import datetime
import subprocess
import requests
from flask import Flask, request

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from auth import kite, TOKEN_FILE, _calculate_token_expiry
from notifier import send

app = Flask(__name__)

def get_public_ip():
    """Get EC2 public IP"""
    try:
        response = requests.get('http://checkip.amazonaws.com', timeout=5)
        return response.text.strip()
    except:
        return "ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com"

@app.route("/")
def login_callback():
    """Handle Kite login callback"""
    request_token = request.args.get("request_token")
    
    if not request_token:
        return """
        <html>
        <head><title>No Request Token</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1 style="color: orange;">No Request Token</h1>
            <p>Please try authentication again.</p>
        </body>
        </html>
        """
    
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
        
        config.ACCESS_TOKEN = access_token
        
        print("Access token generated and saved")
        
        # Send success notification
        success_message = f"""Authentication Successful!

Your Zerodha access token has been saved.

Token Details:
Created: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Expires: {expiry.strftime('%Y-%m-%d %H:%M:%S')}
Valid for: ~{(expiry - datetime.datetime.now()).total_seconds() / 3600:.1f} hours

Trading bot is now ready!"""
        
        send(success_message)
        
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
            </style>
        </head>
        <body>
            <div class="container">
                <div class="emoji"></div>
                <h1>Authentication Successful!</h1>
                <p>Your Zerodha access token has been saved.</p>
                <p><strong>Trading bot is ready!</strong></p>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        error_msg = f"Authentication failed: {e}"
        print(f"Error: {error_msg}")
        
        send(f"Authentication Failed: {error_msg}")
        
        return f"""
        <html>
        <head><title>Authentication Failed</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1 style="color: red;">Authentication Failed</h1>
            <p>{error_msg}</p>
        </body>
        </html>
        """

def start_direct_auth():
    """Start direct authentication"""
    # Kill any process on port 5001
    subprocess.run(['sudo', 'kill', '-9', '$(lsof -t -i:5001)'], shell=True, check=False)
    time.sleep(1)
    
    # Get public IP
    public_ip = get_public_ip()
    redirect_url = f"http://{public_ip}:5001/"
    
    # Start Flask server
    import threading
    
    def run_server():
        app.run(host='0.0.0.0', port=5001, use_reloader=False)
    
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(2)
    
    # Generate Kite login URL
    login_url = kite.login_url()
    
    # Send instructions to Telegram
    message = f"""Mobile Authentication Ready!

IMPORTANT: Update Kite Redirect URL FIRST!

1. Go to: https://developers.kite.trade/apps
2. Update redirect URL to: {redirect_url}
3. Save changes

Then click this link to login:
{login_url}

Steps:
1. Click the link above
2. Login to Kite
3. Enter 2FA
4. Authorize
5. Done!

Note: Port 5001 must be open in AWS Security Group."""
    
    send(message)
    print(f"Direct auth started. Redirect URL: {redirect_url}")

if __name__ == "__main__":
    start_direct_auth()
PYEOF

chmod +x /home/trader/trading_bot/mobile_auth_direct.py

echo ""
echo "3. Testing direct auth..."
cd /home/trader/trading_bot
source .venv/bin/activate
python3 mobile_auth_direct.py

echo ""
echo "======================================"
echo "Direct Auth Setup Complete!"
echo "======================================"
echo ""
echo "Check your Telegram for instructions!"

ENDSSH

echo ""
echo "======================================"
echo "Fix Complete!"
echo "======================================"
echo ""
echo "This approach uses direct IP instead of ngrok"
echo "Check your Telegram for the authentication link!"
