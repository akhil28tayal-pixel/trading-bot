#!/bin/bash
# Run the fixed mobile authentication on EC2

echo "Running Fixed Mobile Authentication"
echo "================================="
echo ""

ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com << 'ENDSSH'

cd /home/trader/trading_bot

# Create the fixed auth script
cat > mobile_auth_fixed.py << 'PYEOF'
#!/usr/bin/env python3
"""
Fixed Mobile Authentication - Direct IP approach
No ngrok required, uses EC2 public IP directly
"""

import os
import sys
import json
import datetime
import subprocess
import time
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
                <div class="emoji">!</div>
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

def kill_port_5001():
    """Kill any process using port 5001"""
    try:
        result = subprocess.run(
            ['lsof', '-t', '-i:5001'],
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                print(f"Killing process {pid} on port 5001...")
                subprocess.run(['kill', '-9', pid], check=False)
            time.sleep(1)
            print("Port 5001 freed")
    except Exception as e:
        print(f"Warning: Could not check port 5001: {e}")

def start_direct_auth():
    """Start direct authentication"""
    print("Starting direct mobile authentication...")
    
    # Kill any process on port 5001
    kill_port_5001()
    
    # Get public IP
    public_ip = get_public_ip()
    redirect_url = f"http://{public_ip}:5001/"
    
    print(f"Public IP: {public_ip}")
    print(f"Redirect URL: {redirect_url}")
    
    # Start Flask server in background
    import threading
    
    def run_server():
        app.run(host='0.0.0.0', port=5001, use_reloader=False)
    
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(3)
    
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

Note: Port 5001 must be open in AWS Security Group.

Redirect URL: {redirect_url}"""
    
    send(message)
    print(f"Instructions sent to Telegram")
    print(f"Redirect URL: {redirect_url}")

if __name__ == "__main__":
    start_direct_auth()
PYEOF

chmod +x mobile_auth_fixed.py

echo "Running fixed mobile authentication..."
source .venv/bin/activate
python3 mobile_auth_fixed.py

ENDSSH

echo ""
echo "======================================"
echo "Fixed auth running!"
echo "======================================"
echo ""
echo "Check your Telegram for authentication instructions!"
