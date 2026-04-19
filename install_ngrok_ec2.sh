#!/bin/bash
# Complete ngrok setup for EC2 - Mobile Authentication

echo "📱 Installing ngrok for Mobile Kite Authentication"
echo "===================================================="
echo ""

ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com << 'ENDSSH'

echo "Step 1: Installing ngrok..."
cd ~

# Check if already installed
if command -v ngrok &> /dev/null; then
    echo "✅ ngrok already installed"
    ngrok version
else
    # Download and install
    wget -q https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
    tar xzf ngrok-v3-stable-linux-amd64.tgz
    sudo mv ngrok /usr/local/bin/
    rm ngrok-v3-stable-linux-amd64.tgz
    echo "✅ ngrok installed"
    ngrok version
fi

echo ""
echo "Step 2: Checking for port conflicts..."

# Check if port 5001 is in use
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 5001 is in use. Killing process..."
    sudo kill -9 $(lsof -t -i:5001) 2>/dev/null || true
    sleep 2
    echo "✅ Port 5001 freed"
else
    echo "✅ Port 5001 is available"
fi

echo ""
echo "Step 3: Pulling latest code..."
cd /home/trader/trading_bot
git pull

echo ""
echo "Step 4: Installing Python dependencies..."
source .venv/bin/activate
pip install -q flask requests

echo ""
echo "Step 5: Restarting services..."
sudo supervisorctl restart all
sleep 3

echo ""
echo "Step 6: Checking service status..."
sudo supervisorctl status

echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "📱 You can now authenticate from your phone!"
echo ""
echo "Just send /auth to your Telegram bot:"
echo "  @akhil_new_bot"
echo ""
echo "The bot will:"
echo "  1. Start ngrok tunnel"
echo "  2. Create HTTPS URL"
echo "  3. Send you clickable login link"
echo "  4. Handle authentication"
echo "  5. Save token automatically"
echo ""
echo "No SSH needed after this setup!"
echo ""

ENDSSH

echo ""
echo "======================================"
echo "✅ EC2 Setup Complete!"
echo "======================================"
echo ""
echo "Test it now:"
echo "  1. Open Telegram on your phone"
echo "  2. Find @akhil_new_bot"
echo "  3. Send: /auth"
echo "  4. Follow the instructions"
echo ""
