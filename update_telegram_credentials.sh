#!/bin/bash
# Update Telegram Bot Credentials - Local and Production

NEW_TOKEN="8283740538:AAElnriNYc5Z6mTbUpTpOUnxBz4mdiqj35c"
NEW_CHAT_ID="8315722255"

echo "🔄 Updating Telegram Bot Credentials"
echo "======================================"
echo ""

# ============================================
# UPDATE LOCAL .env FILE
# ============================================
echo "📝 Step 1: Updating Local .env file..."

if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found, creating from .env.example..."
    cp .env.example .env
fi

# Remove old Telegram credentials
sed -i.bak '/^TELEGRAM_BOT_TOKEN=/d' .env
sed -i.bak '/^TELEGRAM_CHAT_ID=/d' .env

# Add new credentials
echo "TELEGRAM_BOT_TOKEN=$NEW_TOKEN" >> .env
echo "TELEGRAM_CHAT_ID=$NEW_CHAT_ID" >> .env

echo "✅ Local .env updated"
echo "   Token: $NEW_TOKEN"
echo "   Chat ID: $NEW_CHAT_ID"
echo ""

# ============================================
# UPDATE PRODUCTION (EC2)
# ============================================
echo "📡 Step 2: Updating Production (EC2)..."
echo ""

read -p "Do you want to update EC2 now? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Connecting to EC2..."
    
    ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com << 'ENDSSH'
cd /home/trader/trading_bot

echo "Updating EC2 .env file..."

# Backup current .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Remove old Telegram credentials
sed -i '/^TELEGRAM_BOT_TOKEN=/d' .env
sed -i '/^TELEGRAM_CHAT_ID=/d' .env

# Add new credentials
echo "TELEGRAM_BOT_TOKEN=8283740538:AAElnriNYc5Z6mTbUpTpOUnxBz4mdiqj35c" >> .env
echo "TELEGRAM_CHAT_ID=8315722255" >> .env

echo "✅ EC2 .env updated"

# Restart services
echo ""
echo "Restarting services..."
sudo supervisorctl restart all

echo ""
echo "Waiting for services to start..."
sleep 3

echo ""
echo "Service status:"
sudo supervisorctl status

echo ""
echo "✅ EC2 update complete!"
ENDSSH
    
    echo ""
    echo "✅ Production updated successfully!"
else
    echo "⏭️  Skipping EC2 update"
    echo ""
    echo "To update EC2 manually, run:"
    echo "  ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com"
    echo "  cd /home/trader/trading_bot"
    echo "  nano .env"
    echo "  # Update TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID"
    echo "  sudo supervisorctl restart all"
fi

echo ""
echo "======================================"
echo "✅ Update Complete!"
echo "======================================"
echo ""
echo "📋 New Credentials:"
echo "   Token: $NEW_TOKEN"
echo "   Chat ID: $NEW_CHAT_ID"
echo ""
echo "🧪 Test the bot:"
echo "   1. Send /help to your new bot"
echo "   2. Run: python3 test_telegram_auth.py"
echo ""
