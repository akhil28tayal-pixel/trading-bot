#!/bin/bash
# Setup Mobile-Friendly Kite Authentication
# Uses ngrok to create HTTPS URL - authenticate from anywhere!

echo "📱 Setting up Mobile-Friendly Kite Authentication"
echo "=================================================="
echo ""
echo "This will:"
echo "1. Install ngrok on EC2 (free HTTPS tunnel)"
echo "2. Create a persistent HTTPS URL"
echo "3. Allow authentication from Telegram on mobile"
echo ""

ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com << 'ENDSSH'

echo "📦 Step 1: Installing ngrok..."
cd ~

# Download ngrok
if [ ! -f "ngrok" ]; then
    wget -q https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
    tar xzf ngrok-v3-stable-linux-amd64.tgz
    sudo mv ngrok /usr/local/bin/
    rm ngrok-v3-stable-linux-amd64.tgz
    echo "✅ ngrok installed"
else
    echo "✅ ngrok already installed"
fi

echo ""
echo "📝 Step 2: Creating ngrok configuration..."

# Create ngrok config
mkdir -p ~/.ngrok2
cat > ~/.ngrok2/ngrok.yml << 'EOF'
version: "2"
authtoken: ""
tunnels:
  kite-auth:
    proto: http
    addr: 5001
    inspect: false
EOF

echo "✅ Configuration created"
echo ""

echo "🚀 Step 3: Starting ngrok tunnel..."
echo ""
echo "This will create an HTTPS URL like: https://abc123.ngrok.io"
echo ""

# Start ngrok in background
nohup ngrok http 5001 > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

echo "⏳ Waiting for ngrok to start..."
sleep 3

# Get the public URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null)

if [ -n "$NGROK_URL" ]; then
    echo ""
    echo "======================================"
    echo "✅ HTTPS URL Created!"
    echo "======================================"
    echo ""
    echo "Your HTTPS URL: $NGROK_URL"
    echo ""
    echo "📋 Next Steps:"
    echo ""
    echo "1. Update Kite Redirect URL to:"
    echo "   ${NGROK_URL}/"
    echo ""
    echo "2. Save this URL - you'll need it for authentication"
    echo ""
    echo "3. ngrok is now running in background (PID: $NGROK_PID)"
    echo ""
    echo "To stop ngrok: kill $NGROK_PID"
    echo ""
    
    # Save URL to file
    echo "$NGROK_URL" > /tmp/ngrok_url.txt
    echo "✅ URL saved to /tmp/ngrok_url.txt"
else
    echo "❌ Failed to get ngrok URL"
    echo "Check logs: cat /tmp/ngrok.log"
fi

ENDSSH

echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
