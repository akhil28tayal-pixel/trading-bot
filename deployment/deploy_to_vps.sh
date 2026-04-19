#!/bin/bash
"""
Complete VPS Deployment Script
Deploys your trading bot to production VPS in one command
"""

set -e  # Exit on any error

echo "🚀 TRADING BOT VPS DEPLOYMENT"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

print_info "Starting VPS deployment..."

# Step 1: System Update
print_info "Step 1: Updating system packages..."
apt update && apt upgrade -y
print_status "System updated"

# Step 2: Install Dependencies
print_info "Step 2: Installing dependencies..."
apt install -y python3 python3-pip python3-venv git supervisor nginx htop curl wget unzip
print_status "Dependencies installed"

# Step 3: Create Trading User
print_info "Step 3: Creating trading user..."
if ! id "trader" &>/dev/null; then
    adduser --disabled-password --gecos "" trader
    usermod -aG sudo trader
    print_status "User 'trader' created"
else
    print_warning "User 'trader' already exists"
fi

# Step 4: Set Timezone
print_info "Step 4: Setting timezone to Asia/Kolkata..."
timedatectl set-timezone Asia/Kolkata
print_status "Timezone set to IST"

# Step 5: Setup Trading Bot Directory
print_info "Step 5: Setting up trading bot directory..."
sudo -u trader bash << 'EOF'
cd /home/trader

# Create project directory if it doesn't exist
if [ ! -d "trading_bot" ]; then
    mkdir -p trading_bot
    echo "✅ Created trading_bot directory"
else
    echo "⚠️  trading_bot directory already exists"
fi

cd trading_bot

# Create Python virtual environment
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Created Python virtual environment"
else
    echo "⚠️  Virtual environment already exists"
fi

# Activate virtual environment and install packages
source .venv/bin/activate
pip install --upgrade pip
pip install kiteconnect pandas numpy matplotlib seaborn websocket-client requests python-telegram-bot psutil

echo "✅ Python packages installed"

# Create log directories
mkdir -p logs/{daily,errors,trades,system}
echo "✅ Log directories created"

# Create basic directory structure
mkdir -p {strategies,risk,backtest,utils,deployment}
echo "✅ Directory structure created"
EOF

print_status "Trading bot environment setup complete"

# Step 6: Configure Supervisor
print_info "Step 6: Configuring supervisor..."

# Create supervisor config
cat > /etc/supervisor/conf.d/trading_bot.conf << 'EOF'
[program:trading_bot]
command=/home/trader/trading_bot/.venv/bin/python /home/trader/trading_bot/main.py
directory=/home/trader/trading_bot
user=trader
autostart=false
autorestart=true
startretries=3
redirect_stderr=true
stdout_logfile=/home/trader/trading_bot/logs/supervisor.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
environment=PYTHONPATH="/home/trader/trading_bot"
priority=100

[program:trading_bot_monitor]
command=/home/trader/trading_bot/.venv/bin/python /home/trader/trading_bot/deployment/monitor.py
directory=/home/trader/trading_bot
user=trader
autostart=true
autorestart=true
startretries=3
redirect_stderr=true
stdout_logfile=/home/trader/trading_bot/logs/monitor.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=3
environment=PYTHONPATH="/home/trader/trading_bot"
priority=200

[group:trading_system]
programs=trading_bot,trading_bot_monitor
priority=999
EOF

# Reload supervisor
supervisorctl reread
supervisorctl update
print_status "Supervisor configured"

# Step 7: Setup Cron Jobs
print_info "Step 7: Setting up cron jobs..."
sudo -u trader bash << 'EOF'
# Create cron jobs
(crontab -l 2>/dev/null; echo "# Trading Bot Automation") | crontab -
(crontab -l 2>/dev/null; echo "10 9 * * 1-5 /usr/bin/supervisorctl start trading_bot") | crontab -
(crontab -l 2>/dev/null; echo "0 16 * * 1-5 /usr/bin/supervisorctl stop trading_bot") | crontab -
(crontab -l 2>/dev/null; echo "0 18 * * 1-5 /home/trader/trading_bot/deployment/daily_cleanup.sh") | crontab -
echo "✅ Cron jobs configured"
EOF

print_status "Cron jobs setup complete"

# Step 8: Configure Firewall
print_info "Step 8: Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow 80
ufw allow 443
print_status "Firewall configured"

# Step 9: Create Deployment Info File
print_info "Step 9: Creating deployment info..."
cat > /home/trader/trading_bot/DEPLOYMENT_INFO.txt << EOF
🚀 TRADING BOT DEPLOYMENT COMPLETE
==================================

Deployment Date: $(date)
Server IP: $(curl -s ifconfig.me)
Server Location: $(curl -s ipinfo.io/city), $(curl -s ipinfo.io/country)
Python Version: $(python3 --version)
Timezone: $(timedatectl show --property=Timezone --value)

📁 IMPORTANT PATHS:
- Project Directory: /home/trader/trading_bot
- Log Directory: /home/trader/trading_bot/logs
- Config File: /home/trader/trading_bot/config.py
- Supervisor Config: /etc/supervisor/conf.d/trading_bot.conf

🔧 MANAGEMENT COMMANDS:
- Start Bot: sudo supervisorctl start trading_bot
- Stop Bot: sudo supervisorctl stop trading_bot
- Check Status: sudo supervisorctl status
- View Logs: tail -f /home/trader/trading_bot/logs/supervisor.log

📋 NEXT STEPS:
1. Upload your trading bot code to /home/trader/trading_bot/
2. Configure config.py with your API credentials
3. Run authentication: python3 deployment/manual_auth.py <request_token>
4. Start the bot: sudo supervisorctl start trading_bot

🚨 IMPORTANT NOTES:
- Bot will auto-start at 9:10 AM on weekdays
- Bot will auto-stop at 4:00 PM on weekdays
- Daily cleanup runs at 6:00 PM
- Monitor logs regularly for any issues

✅ DEPLOYMENT SUCCESSFUL!
EOF

chown trader:trader /home/trader/trading_bot/DEPLOYMENT_INFO.txt
print_status "Deployment info created"

# Final Status
echo ""
echo "🎉 VPS DEPLOYMENT COMPLETE!"
echo "=========================="
print_status "System updated and configured"
print_status "Trading user created"
print_status "Python environment ready"
print_status "Supervisor configured"
print_status "Cron jobs scheduled"
print_status "Firewall configured"
echo ""
print_info "Next steps:"
echo "1. Upload your trading bot code to /home/trader/trading_bot/"
echo "2. Configure your API credentials"
echo "3. Test the deployment"
echo "4. Start trading!"
echo ""
print_info "Check /home/trader/trading_bot/DEPLOYMENT_INFO.txt for detailed instructions"
echo ""
print_status "🚀 Ready for trading bot deployment!"
