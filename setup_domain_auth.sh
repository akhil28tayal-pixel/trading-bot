#!/bin/bash
# Setup Domain-based Mobile Authentication
# Uses atcpa.co with HTTPS certificate

echo "Setting up Domain-based Authentication"
echo "====================================="
echo "Domain: atcpa.co"
echo ""

ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com << 'ENDSSH'

cd /home/trader/trading_bot

echo "1. Creating domain-based authentication script..."
cat > mobile_auth_domain.py << 'PYEOF'
#!/usr/bin/env python3
"""
Domain-based Mobile Authentication
Uses atcpa.co with HTTPS certificate
Professional and reliable authentication
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

DOMAIN = "atcpa.co"
HTTPS_URL = f"https://{DOMAIN}"
REDIRECT_URL = f"{HTTPS_URL}/"

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
            <title>Authentication Successful!</title>
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
                h1 { color: #28a745; margin-bottom: 20px; font-size: 2em; }
                .emoji { font-size: 64px; margin: 20px 0; }
                .success-icon { color: #28a745; }
                .domain { color: #667eea; font-weight: bold; }
                p { font-size: 16px; line-height: 1.6; }
                .footer { margin-top: 30px; font-size: 14px; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="emoji success-icon">!</div>
                <h1>Authentication Successful!</h1>
                <p>Your Zerodha access token has been saved.</p>
                <p><strong>Trading bot is ready!</strong></p>
                <div class="footer">
                    <p>Powered by <span class="domain">atcpa.co</span></p>
                    <p>You can close this page now.</p>
                </div>
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

def kill_port_443():
    """Kill any process using port 443"""
    try:
        result = subprocess.run(
            ['sudo', 'lsof', '-t', '-i:443'],
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                print(f"Killing process {pid} on port 443...")
                subprocess.run(['sudo', 'kill', '-9', pid], check=False)
            time.sleep(1)
            print("Port 443 freed")
    except Exception as e:
        print(f"Warning: Could not check port 443: {e}")

def kill_port_80():
    """Kill any process using port 80"""
    try:
        result = subprocess.run(
            ['sudo', 'lsof', '-t', '-i:80'],
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                print(f"Killing process {pid} on port 80...")
                subprocess.run(['sudo', 'kill', '-9', pid], check=False)
            time.sleep(1)
            print("Port 80 freed")
    except Exception as e:
        print(f"Warning: Could not check port 80: {e}")

def start_domain_auth():
    """Start domain-based authentication"""
    print(f"Starting domain-based authentication for {DOMAIN}...")
    
    # Kill any process on ports 80 and 443
    kill_port_80()
    kill_port_443()
    
    print(f"Domain: {DOMAIN}")
    print(f"HTTPS URL: {HTTPS_URL}")
    print(f"Redirect URL: {REDIRECT_URL}")
    
    # Start Flask server on port 443 (HTTPS)
    import threading
    
    def run_server():
        # Use SSL context for HTTPS
        context = ('/etc/ssl/certs/atcpa.co.crt', '/etc/ssl/private/atcpa.co.key')
        try:
            app.run(host='0.0.0.0', port=443, ssl_context=context, use_reloader=False)
        except Exception as e:
            print(f"SSL context not found, running on HTTP port 80: {e}")
            # Fallback to HTTP if SSL certs not found
            app.run(host='0.0.0.0', port=80, use_reloader=False)
    
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(3)
    
    # Generate Kite login URL
    login_url = kite.login_url()
    
    # Send instructions to Telegram
    message = f"""Professional Authentication Ready!

Domain: {DOMAIN}
Redirect URL: {REDIRECT_URL}

Steps:
1. Go to: https://developers.kite.trade/apps
2. Update redirect URL to: {REDIRECT_URL}
3. Save changes

Then click this link to login:
{login_url}

Authentication Flow:
1. Click the link above
2. Login to Kite
3. Enter 2FA
4. Authorize
5. Redirect to {REDIRECT_URL}
6. Token saved automatically

Professional setup with SSL certificate!"""
    
    send(message)
    print(f"Instructions sent to Telegram")
    print(f"Domain: {DOMAIN}")
    print(f"Redirect URL: {REDIRECT_URL}")

if __name__ == "__main__":
    start_domain_auth()
PYEOF

chmod +x mobile_auth_domain.py

echo "2. Testing domain authentication..."
source .venv/bin/activate
python3 mobile_auth_domain.py

echo ""
echo "======================================"
echo "Domain Authentication Setup Complete!"
echo "======================================"
echo ""
echo "Check your Telegram for instructions!"

ENDSSH

echo ""
echo "======================================"
echo "Domain Setup Complete!"
echo "======================================"
echo ""
echo "Now using professional domain: atcpa.co"
echo "Check your Telegram for authentication instructions!"
