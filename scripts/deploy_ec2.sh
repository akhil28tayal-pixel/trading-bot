#!/bin/bash
"""
AWS EC2 Deployment Script
Deploy trading bot to AWS EC2 instance with SSH key authentication
"""

# Configuration
EC2_HOST="ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com"
EC2_USER="trader"
EC2_PATH="/home/trader/trading_bot"
SSH_KEY="$HOME/Downloads/trading-bot.pem"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    print_error "SSH key not found: $SSH_KEY"
    echo "Please ensure your SSH key file exists at this location"
    exit 1
fi

# Set correct permissions on SSH key
chmod 400 "$SSH_KEY"

echo "🚀 AWS EC2 DEPLOYMENT"
echo "===================="
print_info "Deploying to: $EC2_USER@$EC2_HOST:$EC2_PATH"
print_info "Using SSH key: $SSH_KEY"
echo ""

# Step 1: Test SSH connection
print_info "Step 1: Testing SSH connection..."
ssh -i "$SSH_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no $EC2_USER@$EC2_HOST "echo 'SSH connection successful'" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    print_error "Cannot connect to EC2. Please check:"
    echo "  - EC2 instance is running"
    echo "  - SSH key is correct: $SSH_KEY"
    echo "  - Security group allows SSH (port 22)"
    echo "  - Try manual test: ssh -i $SSH_KEY $EC2_USER@$EC2_HOST"
    exit 1
fi
print_status "SSH connection successful"

# Step 2: Create backup on EC2
print_info "Step 2: Creating backup on EC2..."
ssh -i "$SSH_KEY" $EC2_USER@$EC2_HOST "
    cd $EC2_PATH
    if [ -d '.backup' ]; then rm -rf .backup; fi
    mkdir -p .backup
    cp -r . .backup/ 2>/dev/null || true
    echo 'Backup created'
"
print_status "Backup created on EC2"

# Step 3: Upload code
print_info "Step 3: Uploading code changes..."

# Create exclude file for rsync
cat > .rsync_exclude << 'EOF'
.git/
.venv/
__pycache__/
*.pyc
*.pyo
.DS_Store
.env
*.log
.rsync_exclude
EOF

# Upload using rsync with SSH key
rsync -avz --exclude-from=.rsync_exclude -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
    ./ $EC2_USER@$EC2_HOST:$EC2_PATH/

if [ $? -eq 0 ]; then
    print_status "Code uploaded successfully"
else
    print_error "Code upload failed"
    exit 1
fi

# Clean up exclude file
rm -f .rsync_exclude

# Step 4: Install dependencies on EC2
print_info "Step 4: Checking Python dependencies..."
ssh -i "$SSH_KEY" $EC2_USER@$EC2_HOST "
    cd $EC2_PATH
    if [ ! -d '.venv' ]; then
        echo 'Creating virtual environment...'
        python3 -m venv .venv
    fi
    source .venv/bin/activate
    pip install --upgrade pip
    pip install kiteconnect flask requests psutil websocket-client python-telegram-bot
    echo 'Dependencies installed'
"
print_status "Python dependencies updated"

# Step 5: Create logs directory
print_info "Step 5: Setting up logs directory..."
ssh -i "$SSH_KEY" $EC2_USER@$EC2_HOST "
    cd $EC2_PATH
    mkdir -p logs
    echo 'Logs directory created'
"
print_status "Logs directory created"

# Step 6: Create environment file
print_info "Step 6: Setting up environment configuration..."
ssh -i "$SSH_KEY" $EC2_USER@$EC2_HOST "
    cd $EC2_PATH
    if [ ! -f '.env' ]; then
        cat > .env << 'ENV_EOF'
# Kite Connect API Configuration
KITE_API_KEY=\"a3vxb4s820e8zrbj\"
KITE_API_SECRET=\"ijtzic5rgln81whkq5ecmrnospku4ed3\"
KITE_ACCESS_TOKEN=\"\"

# Trading Configuration
TRADING_MODE=\"PAPER\"
TRADING_CAPITAL=100000
RISK_PER_TRADE=0.01
DAILY_LOSS_LIMIT=0.03
PAPER_TRADING=true

# Telegram Configuration
TELEGRAM_BOT_TOKEN=\"8785296450:AAHKrXHS6c--phdu2FrjEMFJQHcQ4cgNJVk\"
TELEGRAM_CHAT_ID=\"\"

# Execution Settings
ENABLE_SLIPPAGE=true
SLIPPAGE_PERCENT=0.003
ENABLE_DELAY=true
EXECUTION_DELAY_MS=200
ENABLE_VOLATILITY_ADJUSTMENT=true
ENABLE_TIME_BASED_SLIPPAGE=true
ENABLE_PARTIAL_FILLS=false
ENV_EOF
        echo 'Environment file created'
    else
        echo 'Environment file already exists'
    fi
"
print_status "Environment configuration set up"

# Step 7: Restart services
print_info "Step 7: Restarting trading bot services..."
ssh -i "$SSH_KEY" $EC2_USER@$EC2_HOST "
    cd $EC2_PATH
    # Kill any existing Python processes
    pkill -f 'python.*main.py' || true
    pkill -f 'python.*telegram_bot.py' || true
    sleep 2
    echo 'Services stopped'
"
print_status "Services stopped"

# Step 8: Start trading bot
print_info "Step 8: Starting trading bot..."
ssh -i "$SSH_KEY" $EC2_USER@$EC2_HOST "
    cd $EC2_PATH
    source .venv/bin/activate
    nohup python3 main.py > logs/main.log 2>&1 &
    echo 'Trading bot started'
"
print_status "Trading bot started"

# Step 9: Start telegram bot
print_info "Step 9: Starting telegram bot..."
ssh -i "$SSH_KEY" $EC2_USER@$EC2_HOST "
    cd $EC2_PATH
    source .venv/bin/activate
    nohup python3 deployment/telegram_bot.py > logs/telegram_bot.log 2>&1 &
    echo 'Telegram bot started'
"
print_status "Telegram bot started"

# Step 10: Verify deployment
print_info "Step 10: Verifying deployment..."
sleep 3
ssh -i "$SSH_KEY" $EC2_USER@$EC2_HOST "
    cd $EC2_PATH
    echo '=== Running Processes ==='
    ps aux | grep python | grep -E '(main|telegram_bot)' | grep -v grep || echo 'No processes found'
    echo ''
    echo '=== Recent Logs ==='
    tail -5 logs/main.log 2>/dev/null || echo 'No main log yet'
    echo ''
    tail -5 logs/telegram_bot.log 2>/dev/null || echo 'No telegram log yet'
"

echo ""
print_status "Deployment Complete!"
echo "=========================="
echo "📍 EC2 Instance: $EC2_HOST"
echo "📁 Project Path: $EC2_PATH"
echo ""
echo "📊 Management Commands:"
echo "  SSH to EC2: ssh -i $SSH_KEY $EC2_USER@$EC2_HOST"
echo "  View logs: ssh -i $SSH_KEY $EC2_USER@$EC2_HOST 'tail -f $EC2_PATH/logs/main.log'"
echo "  Check status: ssh -i $SSH_KEY $EC2_USER@$EC2_HOST 'ps aux | grep python'"
echo ""
echo "🔧 Next Steps:"
echo "1. Configure authentication: ssh -i $SSH_KEY $EC2_USER@$EC2_HOST 'cd $EC2_PATH && python3 auth.py'"
echo "2. Test telegram bot commands"
echo "3. Monitor bot performance"
echo ""
print_status "Your trading bot is now deployed on AWS EC2!"
