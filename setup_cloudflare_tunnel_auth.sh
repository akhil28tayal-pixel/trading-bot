#!/bin/bash
# Setup Cloudflare Tunnel for Mobile Authentication
# More reliable than ngrok for this use case

echo "Setting up Cloudflare Tunnel for Mobile Authentication"
echo "====================================================="
echo ""

ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com << 'ENDSSH'

echo "1. Installing cloudflared..."
cd ~

# Check if already installed
if command -v cloudflared &> /dev/null; then
    echo "cloudflared already installed"
    cloudflared --version
else
    # Download and install
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    sudo dpkg -i cloudflared-linux-amd64.deb
    echo "cloudflared installed"
    cloudflared --version
fi

echo ""
echo "2. Creating tunnel configuration..."
mkdir -p ~/.cloudflared

# Create config
cat > ~/.cloudflared/config.yml << 'EOF'
tunnel: trading-bot-auth
credentials-file: /home/trader/.cloudflared/credentials.json

ingress:
  - hostname: "*.trycloudflare.com"
    service: http://localhost:5001
  - service: http_status:404
EOF

echo "3. Testing cloudflared tunnel..."
echo "Starting tunnel for 10 seconds..."

# Start tunnel in background
nohup cloudflared tunnel --url http://localhost:5001 > /tmp/cloudflare.log 2>&1 &
CF_PID=$!

# Wait for tunnel to start
sleep 5

# Get the tunnel URL
TUNNEL_URL=$(cat /tmp/cloudflare.log | grep -o 'https://[^[:space:]]*' | head -1)

if [ -n "$TUNNEL_URL" ]; then
    echo "SUCCESS: Cloudflare Tunnel created"
    echo "URL: $TUNNEL_URL"
    
    # Save URL for later use
    echo "$TUNNEL_URL" > /tmp/tunnel_url.txt
    
    # Test if it's working
    if curl -s "$TUNNEL_URL" > /dev/null 2>&1; then
        echo "Tunnel is responding"
    else
        echo "Tunnel not responding (Flask server not running yet)"
    fi
else
    echo "FAILED: Could not get tunnel URL"
    echo "Check logs: cat /tmp/cloudflare.log"
fi

# Cleanup
kill $CF_PID 2>/dev/null || true
pkill -f cloudflared 2>/dev/null || true

echo ""
echo "4. Creating a simple mobile auth script..."
cat > /home/trader/trading_bot/mobile_auth_simple.py << 'PYEOF'
#!/usr/bin/env python3
"""
Simple Mobile Authentication using Cloudflare Tunnel
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

@app.route("/")
def login_callback():
    """Handle Kite login callback"""
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
        
        config.ACCESS_TOKEN = access_token
        
        print("Access token generated and saved")
        
        # Send success notification
        send(f"Authentication successful! Token saved. Bot ready to trade.")
        
        return """
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Success!</title>
            <style>
                body { font-family: Arial; text-align: center; padding: 20px; }
                h1 { color: green; }
            </style>
        </head>
        <body>
            <h1>Authentication Successful!</h1>
            <p>Your token has been saved.</p>
            <p>Trading bot is ready!</p>
        </body>
        </html>
        """
        
    except Exception as e:
        send(f"Authentication failed: {e}")
        return f"Authentication failed: {e}"

def start_cloudflare_tunnel():
    """Start Cloudflare tunnel and return URL"""
    print("Starting Cloudflare tunnel...")
    
    # Kill any existing cloudflared
    subprocess.run(['pkill', '-f', 'cloudflared'], check=False)
    time.sleep(1)
    
    # Start new tunnel
    process = subprocess.Popen(
        ['cloudflared', 'tunnel', '--url', 'http://localhost:5001'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for tunnel to start
    time.sleep(5)
    
    # Try to get URL from logs
    try:
        result = subprocess.run(
            ['grep', '-o', 'https://[^[:space:]]*trycloudflare.com', '/tmp/cloudflare.log'],
            capture_output=True,
            text=True
        )
        if result.stdout:
            url = result.stdout.strip().split('\n')[0]
            print(f"Tunnel URL: {url}")
            return url
    except:
        pass
    
    # Alternative method
    try:
        response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
        data = response.json()
        if data.get('tunnels'):
            url = data['tunnels'][0]['public_url']
            print(f"Tunnel URL: {url}")
            return url
    except:
        pass
    
    return None

def send_auth_link():
    """Send authentication link via Telegram"""
    # Start Flask server in background
    import threading
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5001, use_reloader=False), daemon=True).start()
    
    time.sleep(2)
    
    # Start tunnel
    tunnel_url = start_cloudflare_tunnel()
    
    if tunnel_url:
        # Generate Kite login URL
        login_url = kite.login_url()
        
        message = f"""Mobile Authentication Ready!

Tunnel URL: {tunnel_url}

Update Kite redirect URL to: {tunnel_url}/

Then click: {login_url}

Login to Kite and you'll be redirected back automatically."""
        
        send(message)
        return True
    else:
        send("Failed to create tunnel. Please try again.")
        return False

if __name__ == "__main__":
    send_auth_link()
PYEOF

chmod +x /home/trader/trading_bot/mobile_auth_simple.py

echo ""
echo "======================================"
echo "Cloudflare Tunnel Setup Complete!"
echo "======================================"
echo ""
echo "You can now test mobile authentication!"
echo ""

ENDSSH

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Now test by sending /auth to your Telegram bot"
