#!/bin/bash
# Fix ngrok issues on EC2

echo "Fixing ngrok Issues"
echo "==================="
echo ""

ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.sh << 'ENDSSH'

echo "1. Checking ngrok log..."
if [ -f /tmp/ngrok_test.log ]; then
    echo "ngrok test log:"
    cat /tmp/ngrok_test.log
else
    echo "No ngrok test log found"
fi

echo ""
echo "2. Testing ngrok with verbose output..."
cd ~

# Kill any existing ngrok
pkill -f ngrok 2>/dev/null || true
sleep 2

# Try ngrok with verbose output
echo "Starting ngrok with verbose logging..."
timeout 10 ngrok http 5001 --log=stdout --log-level=debug &
NGROK_PID=$!
sleep 5

# Check if ngrok API is responding
if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
    echo "SUCCESS: ngrok API is responding"
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null)
    echo "URL: $NGROK_URL"
else
    echo "FAILED: ngrok API not responding"
    echo "Checking if ngrok process is running..."
    if ps aux | grep ngrok | grep -v grep; then
        echo "ngrok process is running but API not accessible"
    else
        echo "ngrok process not found"
    fi
fi

# Cleanup
kill $NGROK_PID 2>/dev/null || true
pkill -f ngrok 2>/dev/null || true

echo ""
echo "3. Alternative: Using Cloudflare Tunnel..."
echo "If ngrok continues to fail, we can use Cloudflare Tunnel instead."

ENDSSH

echo ""
echo "======================================"
echo "Fix complete!"
echo "======================================"
