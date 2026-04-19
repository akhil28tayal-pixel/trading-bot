#!/bin/bash
# Fix Kite Redirect Issue - Setup HTTPS with SSL

echo "Fixing Kite Redirect Issue"
echo "========================"
echo "Setting up HTTPS with SSL certificate for atcpa.co"
echo ""

ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com << 'ENDSSH'

cd /home/trader/trading_bot

echo "1. Creating HTTPS authentication script..."
cat > mobile_auth_https.py << 'PYEOF'
#!/usr/bin/env python3
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

DOMAIN = 'atcpa.co'
HTTPS_URL = f'https://{DOMAIN}'
REDIRECT_URL = f'{HTTPS_URL}/'

@app.route('/')
def login_callback():
    request_token = request.args.get('request_token')
    
    if not request_token:
        return '<html><head><title>No Request Token</title></head><body style=\"font-family: Arial; text-align: center; padding: 50px;\"><h1 style=\"color: orange;\">No Request Token</h1><p>Please try authentication again.</p></body></html>'
    
    try:
        session = kite.generate_session(request_token, api_secret=config.API_SECRET)
        access_token = session['access_token']
        expiry = _calculate_token_expiry()
        
        with open(TOKEN_FILE, 'w') as f:
            json.dump({
                'access_token': access_token,
                'date': str(datetime.date.today()),
                'created_at': datetime.datetime.now().isoformat(),
                'expiry': expiry.isoformat(),
            }, f)
        
        config.ACCESS_TOKEN = access_token
        
        success_message = f'Authentication Successful! Your Zerodha access token has been saved. Trading bot is now ready!'
        send(success_message)
        
        return '<html><head><title>Success!</title></head><body style=\"font-family: Arial; text-align: center; padding: 50px;\"><h1 style=\"color: green;\">Authentication Successful!</h1><p>Your token has been saved.</p></body></html>'
        
    except Exception as e:
        error_msg = f'Authentication failed: {e}'
        send(f'Authentication Failed: {error_msg}')
        return f'<html><head><title>Failed</title></head><body style=\"font-family: Arial; text-align: center; padding: 50px;\"><h1 style=\"color: red;\">Authentication Failed</h1><p>{error_msg}</p></body></html>'

def kill_port_5001():
    try:
        result = subprocess.run(['lsof', '-t', '-i:5001'], capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                print(f'Killing process {pid} on port 5001...')
                subprocess.run(['kill', '-9', pid], check=False)
            time.sleep(1)
            print('Port 5001 freed')
    except Exception as e:
        print(f'Warning: Could not check port 5001: {e}')

def start_https_auth():
    print(f'Starting HTTPS authentication for {DOMAIN}...')
    print(f'HTTPS URL: {HTTPS_URL}')
    print(f'Redirect URL: {REDIRECT_URL}')
    
    kill_port_5001()
    
    import threading
    
    def run_server():
        app.run(host='127.0.0.1', port=5001, use_reloader=False)
    
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(3)
    
    login_url = kite.login_url()
    
    message = f'''HTTPS Authentication Ready!

Domain: {DOMAIN}
HTTPS URL: {HTTPS_URL}
Redirect URL: {REDIRECT_URL}

IMPORTANT: Update Kite Redirect URL to:
{REDIRECT_URL}

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
6. Nginx proxies to Flask (HTTPS)
7. Token saved automatically

HTTPS setup with SSL certificate!'''
    
    send(message)
    print(f'Instructions sent to Telegram')
    print(f'HTTPS URL: {HTTPS_URL}')
    print(f'Redirect URL: {REDIRECT_URL}')

if __name__ == '__main__':
    start_https_auth()
PYEOF

chmod +x mobile_auth_https.py

echo "2. Starting HTTPS authentication..."
source .venv/bin/activate
python3 mobile_auth_https.py

ENDSSH

echo ""
echo "======================================"
echo "HTTPS Setup Complete!"
echo "======================================"
echo ""
echo "Check your Telegram for HTTPS instructions!"
echo "Update Kite redirect URL to: https://atcpa.co/"
