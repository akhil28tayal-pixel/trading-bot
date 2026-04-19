#!/bin/bash
"""
Deploy Trading Bot to AWS EC2
Complete deployment script for EC2 instance
"""

# EC2 Configuration
EC2_HOST="ubuntu@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com"
PROJECT_NAME="trading_bot"
REMOTE_PATH="/home/ubuntu/$PROJECT_NAME"

echo "🚀 Deploying Trading Bot to AWS EC2..."
echo "📍 Target: $EC2_HOST"
echo "📁 Remote Path: $REMOTE_PATH"

# 1. Test SSH connection
echo "1. Testing SSH connection..."
ssh -o ConnectTimeout=10 $EC2_HOST "echo 'SSH connection successful'" || {
    echo "❌ SSH connection failed. Please check:"
    echo "   - EC2 instance is running"
    echo "   - Security group allows SSH (port 22)"
    echo "   - SSH key is configured correctly"
    exit 1
}

# 2. Prepare local project
echo "2. Preparing local project..."
# Remove any local-specific files
rm -f .env
rm -f *.log
rm -f .kite_token*

# 3. Create deployment package
echo "3. Creating deployment package..."
tar -czf trading_bot_deploy.tar.gz \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.log' \
    --exclude='.env' \
    --exclude='node_modules' \
    --exclude='.DS_Store' \
    .

# 4. Upload to EC2
echo "4. Uploading project to EC2..."
scp trading_bot_deploy.tar.gz $EC2_HOST:/tmp/

# 5. Deploy on EC2
echo "5. Deploying on EC2..."
ssh $EC2_HOST << 'EOF'
set -e

echo "📦 Setting up project on EC2..."

# Update system
sudo apt-get update -y

# Install required packages
sudo apt-get install -y python3 python3-pip python3-venv supervisor nginx

# Create project directory
sudo mkdir -p /home/ubuntu/trading_bot
sudo chown ubuntu:ubuntu /home/ubuntu/trading_bot

# Extract project
cd /home/ubuntu
tar -xzf /tmp/trading_bot_deploy.tar.gz -C trading_bot/

# Set up Python virtual environment
cd trading_bot
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install kiteconnect flask requests psutil websocket-client python-telegram-bot

# Create logs directory
mkdir -p logs

# Create environment file template
cat > .env << 'ENV_EOF'
# Kite Connect API Configuration
KITE_API_KEY=""
KITE_API_SECRET=""
KITE_ACCESS_TOKEN=""

# Trading Configuration
TRADING_MODE="PAPER"
TRADING_CAPITAL=100000
RISK_PER_TRADE=0.01
DAILY_LOSS_LIMIT=0.03
PAPER_TRADING=true

# Telegram Configuration
TELEGRAM_BOT_TOKEN=""
TELEGRAM_CHAT_ID=""

# Execution Settings
ENABLE_SLIPPAGE=true
SLIPPAGE_PERCENT=0.003
ENABLE_DELAY=true
EXECUTION_DELAY_MS=200
ENABLE_VOLATILITY_ADJUSTMENT=true
ENABLE_TIME_BASED_SLIPPAGE=true
ENABLE_PARTIAL_FILLS=false
ENV_EOF

echo "✅ Project deployed successfully!"
echo "📝 Next steps:"
echo "   1. Edit /home/ubuntu/trading_bot/.env with your API keys"
echo "   2. Run: sudo /home/ubuntu/trading_bot/setup_supervisor.sh"
echo "   3. Start the bot: sudo supervisorctl start trading_system"

EOF

# 6. Create supervisor setup script
echo "6. Creating supervisor setup script..."
ssh $EC2_HOST << 'EOF'
cat > /home/ubuntu/trading_bot/setup_supervisor.sh << 'SUPERVISOR_EOF'
#!/bin/bash
"""
Setup Supervisor Configuration for Trading Bot
"""

echo "🔧 Setting up Supervisor configuration..."

# Create supervisor configuration
sudo tee /etc/supervisor/conf.d/trading_bot.conf > /dev/null << 'CONF_EOF'
[program:trading_bot]
command=/home/ubuntu/trading_bot/.venv/bin/python /home/ubuntu/trading_bot/main.py
directory=/home/ubuntu/trading_bot
user=ubuntu
autostart=true
autorestart=true
startretries=3
redirect_stderr=true
stdout_logfile=/home/ubuntu/trading_bot/logs/supervisor.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
environment=PATH="/home/ubuntu/trading_bot/.venv/bin"
priority=100

[program:telegram_bot]
command=/home/ubuntu/trading_bot/.venv/bin/python /home/ubuntu/trading_bot/deployment/telegram_bot.py
directory=/home/ubuntu/trading_bot
user=ubuntu
autostart=true
autorestart=true
startretries=3
redirect_stderr=true
stdout_logfile=/home/ubuntu/trading_bot/logs/telegram_bot.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=PATH="/home/ubuntu/trading_bot/.venv/bin"
priority=200

[group:trading_system]
programs=trading_bot,telegram_bot
priority=999
CONF_EOF

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update

echo "✅ Supervisor configuration complete!"
echo "📊 Available commands:"
echo "   sudo supervisorctl status"
echo "   sudo supervisorctl start trading_system"
echo "   sudo supervisorctl stop trading_system"
echo "   sudo supervisorctl restart trading_system"

SUPERVISOR_EOF

chmod +x /home/ubuntu/trading_bot/setup_supervisor.sh

EOF

# 7. Create authentication setup script
echo "7. Creating authentication setup script..."
ssh $EC2_HOST << 'EOF'
cat > /home/ubuntu/trading_bot/setup_auth.sh << 'AUTH_EOF'
#!/bin/bash
"""
Setup Authentication for Trading Bot
"""

echo "🔐 Setting up authentication..."

cd /home/ubuntu/trading_bot
source .venv/bin/activate

# Check if API keys are configured
if [ -z "$KITE_API_KEY" ] || [ -z "$KITE_API_SECRET" ]; then
    echo "⚠️  Please configure your API keys in .env file first"
    echo "   Edit: /home/ubuntu/trading_bot/.env"
    exit 1
fi

# Start authentication server
echo "🌐 Starting authentication server..."
echo "📍 Access: http://$(curl -s ifconfig.me):5001"
echo "👉 Complete the login process and the token will be saved"

python3 auth.py

AUTH_EOF

chmod +x /home/ubuntu/trading_bot/setup_auth.sh

EOF

# 8. Create monitoring script
echo "8. Creating monitoring script..."
ssh $EC2_HOST << 'EOF'
cat > /home/ubuntu/trading_bot/monitor.sh << 'MONITOR_EOF'
#!/bin/bash
"""
Monitor Trading Bot Status
"""

echo "📊 Trading Bot Status Monitor"
echo "=============================="

# Check supervisor status
echo "🔧 Supervisor Status:"
sudo supervisorctl status

echo ""

# Check processes
echo "🔍 Running Processes:"
ps aux | grep python | grep trading_bot | grep -v grep

echo ""

# Check logs
echo "📝 Recent Logs (last 10 lines):"
echo "--- Supervisor Log ---"
tail -10 /home/ubuntu/trading_bot/logs/supervisor.log 2>/dev/null || echo "No supervisor log found"

echo ""
echo "--- Telegram Bot Log ---"
tail -10 /home/ubuntu/trading_bot/logs/telegram_bot.log 2>/dev/null || echo "No telegram log found"

echo ""

# Check system resources
echo "💻 System Resources:"
echo "Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
echo "Disk: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 " used)"}')"
echo "Load: $(uptime | awk -F'load average:' '{print $2}')"

MONITOR_EOF

chmod +x /home/ubuntu/trading_bot/monitor.sh

EOF

# 9. Cleanup
echo "9. Cleaning up..."
rm -f trading_bot_deploy.tar.gz

echo ""
echo "🎉 Deployment Complete!"
echo "=============================="
echo ""
echo "📍 EC2 Instance: $EC2_HOST"
echo "📁 Project Path: $REMOTE_PATH"
echo ""
echo "🔧 Next Steps:"
echo "1. SSH to EC2: ssh $EC2_HOST"
echo "2. Configure API keys: nano /home/ubuntu/trading_bot/.env"
echo "3. Setup supervisor: sudo /home/ubuntu/trading_bot/setup_supervisor.sh"
echo "4. Setup authentication: /home/ubuntu/trading_bot/setup_auth.sh"
echo "5. Start the bot: sudo supervisorctl start trading_system"
echo "6. Monitor status: /home/ubuntu/trading_bot/monitor.sh"
echo ""
echo "📊 Management Commands:"
echo "   sudo supervisorctl status"
echo "   sudo supervisorctl restart trading_system"
echo "   tail -f /home/ubuntu/trading_bot/logs/supervisor.log"
echo ""
echo "🚀 Your trading bot is ready for deployment!"
