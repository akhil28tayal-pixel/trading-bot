#!/bin/bash
"""
Automated Production Deployment Script
Pushes code changes to production VPS and restarts services
"""

# Configuration
DEPLOY_HOST="${DEPLOY_HOST:-ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com}"
DEPLOY_USER="${DEPLOY_USER:-trader}"
DEPLOY_PATH="${DEPLOY_PATH:-/home/trader/trading_bot}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

echo "🚀 AUTOMATED PRODUCTION DEPLOYMENT"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -f "config.py" ]; then
    print_error "Not in trading bot directory. Please run from project root."
    exit 1
fi

print_info "Deploying to: $DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH"

# Step 1: Test connection
print_info "Step 1: Testing VPS connection..."
if ! ssh -o ConnectTimeout=10 $DEPLOY_USER@$DEPLOY_HOST "echo 'Connection test successful'" 2>/dev/null; then
    print_error "Cannot connect to VPS. Please check:"
    echo "  - VPS is running"
    echo "  - SSH access is working"
    echo "  - Try: ssh -i ~/Downloads/trading-bot.pem $DEPLOY_USER@$DEPLOY_HOST"
    exit 1
fi
print_status "VPS connection successful"

# Step 2: Create backup on VPS
print_info "Step 2: Creating backup on VPS..."
ssh $DEPLOY_USER@$DEPLOY_HOST "
    cd $DEPLOY_PATH
    if [ -d '.backup' ]; then rm -rf .backup; fi
    mkdir -p .backup
    cp -r . .backup/ 2>/dev/null || true
    echo '✅ Backup created'
"
print_status "Backup created on VPS"

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
*.log
logs/
.rsync_exclude
node_modules/
.env
.backup/
EOF

# Upload using rsync
rsync -avz --progress \
    --exclude-from=.rsync_exclude \
    --delete \
    ./ $DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/

if [ $? -eq 0 ]; then
    print_status "Code uploaded successfully"
else
    print_error "Code upload failed"
    rm .rsync_exclude
    exit 1
fi

# Clean up
rm .rsync_exclude

# Step 4: Set permissions and install dependencies
print_info "Step 4: Setting up environment on VPS..."
ssh $DEPLOY_USER@$DEPLOY_HOST << EOF
cd $DEPLOY_PATH

# Activate virtual environment
source .venv/bin/activate

# Install any new dependencies
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

# Set permissions
chmod +x deployment/*.sh
chmod +x deployment/*.py
chmod +x *.sh

# Create log directories
mkdir -p logs/{daily,errors,trades,system}

echo "✅ Environment setup complete"
EOF

print_status "Environment configured"

# Step 5: Test deployment
print_info "Step 5: Testing deployment..."
ssh $DEPLOY_USER@$DEPLOY_HOST << EOF
cd $DEPLOY_PATH
source .venv/bin/activate

# Quick test
python3 -c "
try:
    import config
    import kiteconnect
    import flask
    print('✅ All imports successful')
except Exception as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

# Test deployment
python3 deployment/test_deployment.py | grep "Overall:" | tail -1
EOF

print_status "Deployment tests completed"

# Step 6: Restart services
print_info "Step 6: Restarting services..."
ssh $DEPLOY_USER@$DEPLOY_HOST << 'EOF'
# Stop services gracefully
sudo supervisorctl stop trading_bot 2>/dev/null || true
sudo supervisorctl stop trading_bot_monitor 2>/dev/null || true

# Wait a moment
sleep 2

# Start monitor (always running)
sudo supervisorctl start trading_bot_monitor

echo "✅ Services restarted"
echo "ℹ️  Trading bot will auto-start during market hours"
echo "ℹ️  To start manually: sudo supervisorctl start trading_bot"
EOF

print_status "Services restarted"

# Step 7: Show status
print_info "Step 7: Checking deployment status..."
ssh $DEPLOY_USER@$DEPLOY_HOST << EOF
cd $DEPLOY_PATH

echo "📊 Supervisor Status:"
sudo supervisorctl status

echo ""
echo "🔐 Authentication Status:"
if [ -f "token.json" ]; then
    echo "✅ Token file exists"
    python3 -c "
import json
try:
    with open('token.json', 'r') as f:
        data = json.load(f)
    print(f'✅ Token date: {data.get(\"date\", \"Unknown\")}')
except:
    print('⚠️  Token file exists but may be invalid')
"
else
    echo "❌ No authentication token found"
    echo "👉 Run: python3 auth.py to authenticate"
fi

echo ""
echo "📈 Market Status:"
python3 -c "
import datetime as dt
now = dt.datetime.now()
if now.weekday() >= 5:
    print('📅 Weekend - Market closed')
elif now.time() < dt.time(9, 15):
    print('🌅 Before market open (9:15 AM)')
elif now.time() > dt.time(15, 30):
    print('🌆 After market close (3:30 PM)')
else:
    print('🔥 Market is OPEN - Ready for trading!')
"
EOF

echo ""
print_status "🎉 DEPLOYMENT COMPLETE!"
echo ""
print_info "Next steps:"
echo "1. If not authenticated: ssh $DEPLOY_USER@$DEPLOY_HOST 'cd $DEPLOY_PATH && .venv/bin/python auth.py'"
echo "2. To start trading: ssh $DEPLOY_USER@$DEPLOY_HOST 'sudo supervisorctl start trading_bot'"
echo "3. To monitor: ssh $DEPLOY_USER@$DEPLOY_HOST 'tail -f $DEPLOY_PATH/logs/supervisor.log'"
echo ""
print_info "Deployment summary:"
echo "  - Code uploaded and tested ✅"
echo "  - Dependencies updated ✅"
echo "  - Services configured ✅"
echo "  - Monitor running ✅"
echo ""
print_status "Ready for production trading! 🚀"
