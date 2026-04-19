#!/bin/bash
# Setup Cloudflare Tunnel for HTTPS Authentication
# This provides a free HTTPS URL for Kite authentication

echo "🌐 Setting up Cloudflare Tunnel for Kite Authentication"
echo "========================================================"
echo ""
echo "This will create a free HTTPS URL for your EC2 instance"
echo "so you can authenticate from anywhere (including mobile!)"
echo ""

# Install cloudflared on EC2
ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com << 'ENDSSH'

echo "📦 Installing Cloudflare Tunnel (cloudflared)..."

# Download cloudflared
cd ~
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# Install
sudo dpkg -i cloudflared-linux-amd64.deb

# Verify installation
cloudflared --version

echo ""
echo "✅ Cloudflared installed!"
echo ""

# Create tunnel configuration
echo "📝 Creating tunnel configuration..."

mkdir -p ~/.cloudflared

cat > ~/.cloudflared/config.yml << 'EOF'
tunnel: trading-bot-auth
credentials-file: /home/trader/.cloudflared/credentials.json

ingress:
  - hostname: "*.trycloudflare.com"
    service: http://localhost:5001
  - service: http_status:404
EOF

echo "✅ Configuration created!"
echo ""

echo "🚀 Starting Cloudflare Tunnel..."
echo ""
echo "This will create a temporary HTTPS URL."
echo "The URL will be displayed below - use it for Kite redirect URL"
echo ""
echo "Press Ctrl+C when done with authentication, then restart with:"
echo "  cloudflared tunnel --url http://localhost:5001"
echo ""

# Start tunnel (this will show the HTTPS URL)
cloudflared tunnel --url http://localhost:5001

ENDSSH

echo ""
echo "======================================"
echo "✅ Cloudflare Tunnel Setup Complete!"
echo "======================================"
