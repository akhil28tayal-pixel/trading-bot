#!/bin/bash
# Diagnose authentication issues on EC2

echo "🔍 Diagnosing Authentication Issues"
echo "===================================="
echo ""

ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com << 'ENDSSH'

echo "1. Checking ngrok installation..."
if command -v ngrok &> /dev/null; then
    echo "✅ ngrok is installed"
    ngrok version
else
    echo "❌ ngrok NOT installed"
    echo "   Installing now..."
    cd ~
    wget -q https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
    tar xzf ngrok-v3-stable-linux-amd64.tgz
    sudo mv ngrok /usr/local/bin/
    rm ngrok-v3-stable-linux-amd64.tgz
    echo "✅ ngrok installed"
    ngrok version
fi

echo ""
echo "2. Checking Python dependencies..."
cd /home/trader/trading_bot
source .venv/bin/activate

python3 << 'PYEOF'
import sys
missing = []

try:
    import flask
    print("✅ flask installed")
except ImportError:
    print("❌ flask NOT installed")
    missing.append("flask")

try:
    import requests
    print("✅ requests installed")
except ImportError:
    print("❌ requests NOT installed")
    missing.append("requests")

if missing:
    print(f"\nInstalling missing packages: {', '.join(missing)}")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "-q"] + missing)
    print("✅ Packages installed")
PYEOF

echo ""
echo "3. Checking if telegram_mobile_auth.py exists..."
if [ -f "telegram_mobile_auth.py" ]; then
    echo "✅ telegram_mobile_auth.py exists"
else
    echo "❌ telegram_mobile_auth.py NOT found"
    echo "   Pulling from GitHub..."
    git pull
fi

echo ""
echo "4. Testing mobile auth import..."
python3 << 'PYEOF'
import sys
import os
sys.path.insert(0, '/home/trader/trading_bot')

try:
    from telegram_mobile_auth import send_mobile_auth_request
    print("✅ telegram_mobile_auth imports successfully")
except Exception as e:
    print(f"❌ Import failed: {e}")
    print("\nTrying to identify the issue...")
    import traceback
    traceback.print_exc()
PYEOF

echo ""
echo "5. Checking Telegram bot status..."
sudo supervisorctl status telegram_bot

echo ""
echo "6. Checking recent telegram_bot logs..."
echo "Last 20 lines:"
tail -20 logs/telegram_bot.log 2>/dev/null || echo "No logs found"

echo ""
echo "7. Checking port 5001..."
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 5001 is in use:"
    lsof -i :5001
else
    echo "✅ Port 5001 is free"
fi

echo ""
echo "8. Testing ngrok manually..."
echo "Starting ngrok for 5 seconds..."
timeout 5 ngrok http 5001 > /tmp/ngrok_test.log 2>&1 &
NGROK_PID=$!
sleep 3

if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
    echo "✅ ngrok can start successfully"
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null)
    echo "   Test URL: $NGROK_URL"
else
    echo "❌ ngrok failed to start"
    echo "   Check /tmp/ngrok_test.log for details"
fi

kill $NGROK_PID 2>/dev/null || true
pkill -f ngrok 2>/dev/null || true

echo ""
echo "======================================"
echo "Diagnosis Complete!"
echo "======================================"

ENDSSH

echo ""
echo "✅ Diagnosis complete! Check output above for issues."
