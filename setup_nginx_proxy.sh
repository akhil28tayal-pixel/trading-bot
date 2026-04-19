#!/bin/bash
# Setup Nginx Proxy for atcpa.co -> Flask on port 5001

echo "Setting up Nginx Proxy for Domain Authentication"
echo "=============================================="
echo "Domain: atcpa.co"
echo "Proxy: http://127.0.0.1:5001"
echo ""

ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com << 'ENDSSH'

echo "1. Installing nginx..."
sudo apt update
sudo apt install -y nginx

echo ""
echo "2. Creating nginx configuration for atcpa.co..."
sudo tee /etc/nginx/sites-available/atcpa.co << 'NGINXCONF'
server {
    listen 80;
    server_name atcpa.co;

    location / {
        proxy_pass http://127.0.0.1:5001;  # your Flask app
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Handle WebSocket connections if needed
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
NGINXCONF

echo ""
echo "3. Enabling the site..."
sudo ln -sf /etc/nginx/sites-available/atcpa.co /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # Remove default site

echo ""
echo "4. Testing nginx configuration..."
sudo nginx -t

echo ""
echo "5. Restarting nginx..."
sudo systemctl restart nginx
sudo systemctl enable nginx

echo ""
echo "6. Checking nginx status..."
sudo systemctl status nginx --no-pager

echo ""
echo "7. Creating domain-based authentication script (port 5001)..."
cd /home/trader/trading_bot

cat > mobile_auth_domain_nginx.py << 'PYEOF'
#!/usr/bin/env python3
"""
Domain-based Mobile Authentication with Nginx Proxy
Uses atcpa.co domain with nginx proxy to port 5001
Professional authentication with custom domain
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
URL = f"https://{DOMAIN}"
REDIRECT_URL = f"{URL}/"

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
                .nginx-badge {
                    background: #009639;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 5px;
                    font-size: 12px;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="nginx-badge">POWERED BY NGINX</div>
                <div class="emoji success-icon">!</div>
                <h1>Authentication Successful!</h1>
                <p>Your Zerodha access token has been saved.</p>
                <p><strong>Trading bot is ready!</strong></p>
                <div class="footer">
                    <p>Powered by <span class="domain">atcpa.co</span></p>
                    <p>Professional nginx proxy setup</p>
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

def start_domain_auth():
    """Start domain-based authentication with nginx"""
    print(f"Starting domain-based authentication for {DOMAIN}...")
    print(f"Nginx proxy: {URL} -> http://127.0.0.1:5001")
    
    # Kill any process on port 5001
    kill_port_5001()
    
    print(f"Domain: {DOMAIN}")
    print(f"URL: {URL}")
    print(f"Redirect URL: {REDIRECT_URL}")
    
    # Start Flask server on port 5001 (nginx will proxy to it)
    import threading
    
    def run_server():
        app.run(host='127.0.0.1', port=5001, use_reloader=False)
    
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(3)
    
    # Generate Kite login URL
    login_url = kite.login_url()
    
    # Send instructions to Telegram
    message = f"""Professional Authentication Ready!

Domain: {DOMAIN}
Setup: Nginx Proxy
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
6. Nginx proxies to Flask server
7. Token saved automatically

Professional setup with nginx proxy!"""
    
    send(message)
    print(f"Instructions sent to Telegram")
    print(f"Domain: {DOMAIN}")
    print(f"Redirect URL: {REDIRECT_URL}")

if __name__ == "__main__":
    start_domain_auth()
PYEOF

chmod +x mobile_auth_domain_nginx.py

echo ""
echo "8. Testing nginx proxy authentication..."
source .venv/bin/activate
python3 mobile_auth_domain_nginx.py

echo ""
echo "======================================"
echo "Nginx Proxy Setup Complete!"
echo "======================================"
echo ""
echo "Domain: atcpa.co"
echo "Proxy: nginx -> http://127.0.0.1:5001"
echo "Check your Telegram for authentication instructions!"

ENDSSH

echo ""
echo "======================================"
echo "Nginx Proxy Setup Complete!"
echo "======================================"
echo ""
echo "Your domain now proxies to Flask on port 5001"
echo "Check your Telegram for authentication instructions!"
