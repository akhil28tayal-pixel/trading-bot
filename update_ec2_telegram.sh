#!/bin/bash
# Quick script to update Telegram credentials on EC2

echo "🚀 Updating Telegram Credentials on EC2"
echo "========================================"
echo ""
echo "New Token: 8283740538:AAElnriNYc5Z6mTbUpTpOUnxBz4mdiqj35c"
echo "New Chat ID: 8315722255"
echo ""

ssh -i ~/Downloads/trading-bot.pem trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com << 'ENDSSH'
cd /home/trader/trading_bot

echo "📝 Backing up current .env..."
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

echo "🔄 Updating credentials..."
# Remove old credentials
sed -i '/^TELEGRAM_BOT_TOKEN=/d' .env
sed -i '/^TELEGRAM_CHAT_ID=/d' .env

# Add new credentials
echo "TELEGRAM_BOT_TOKEN=8283740538:AAElnriNYc5Z6mTbUpTpOUnxBz4mdiqj35c" >> .env
echo "TELEGRAM_CHAT_ID=8315722255" >> .env

echo "✅ Credentials updated"
echo ""

echo "🔄 Restarting services..."
sudo supervisorctl restart all

echo ""
echo "⏳ Waiting for services to start..."
sleep 3

echo ""
echo "📊 Service Status:"
sudo supervisorctl status

echo ""
echo "🧪 Testing configuration..."
python3 -c "import config; print('Token:', config.TELEGRAM_TOKEN[:20] + '...'); print('Chat ID:', config.CHAT_ID)"

echo ""
echo "✅ EC2 Update Complete!"
echo ""
echo "📱 Test by sending /help to your Telegram bot"
ENDSSH

echo ""
echo "======================================"
echo "✅ Done!"
echo "======================================"
