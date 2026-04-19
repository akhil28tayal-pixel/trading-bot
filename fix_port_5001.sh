#!/bin/bash
# Fix port 5001 conflicts on EC2

echo "🔧 Fixing Port 5001 Conflicts"
echo "=============================="
echo ""

ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com << 'ENDSSH'

echo "Checking what's using port 5001..."
echo ""

# Check if port is in use
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 5001 is in use by:"
    lsof -i :5001
    echo ""
    
    # Kill the processes
    echo "Killing processes on port 5001..."
    sudo kill -9 $(lsof -t -i:5001) 2>/dev/null || true
    sleep 2
    
    # Verify
    if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Port still in use, trying harder..."
        sudo fuser -k 5001/tcp 2>/dev/null || true
        sleep 2
    fi
    
    echo "✅ Port 5001 freed"
else
    echo "✅ Port 5001 is already free"
fi

echo ""
echo "Checking for ngrok processes..."
if pgrep -f ngrok > /dev/null; then
    echo "⚠️  Found ngrok processes, killing them..."
    pkill -f ngrok
    sleep 2
    echo "✅ ngrok processes killed"
else
    echo "✅ No ngrok processes running"
fi

echo ""
echo "======================================"
echo "✅ Port 5001 is now available!"
echo "======================================"
echo ""
echo "You can now send /auth to your Telegram bot"

ENDSSH

echo ""
echo "✅ Done! Try /auth again on Telegram"
