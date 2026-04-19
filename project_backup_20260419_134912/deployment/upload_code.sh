#!/bin/bash
"""
Upload Trading Bot Code to VPS
Uploads your local code to the production server
"""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

echo "📤 UPLOADING TRADING BOT CODE TO VPS"
echo "===================================="

# Check if VPS IP is provided
if [ -z "$1" ]; then
    print_error "Usage: ./upload_code.sh <VPS_IP_ADDRESS>"
    print_info "Example: ./upload_code.sh 192.168.1.100"
    exit 1
fi

VPS_IP=$1
VPS_USER="${DEPLOY_USER:-trader}"
VPS_PATH="${DEPLOY_PATH:-/home/trader/trading_bot}"

print_info "Uploading to: $VPS_USER@$VPS_IP:$VPS_PATH"

# Test connection
print_info "Testing connection to VPS..."
if ! ssh -o ConnectTimeout=10 $VPS_USER@$VPS_IP "echo 'Connection successful'" 2>/dev/null; then
    print_error "Cannot connect to VPS. Please check:"
    echo "  - VPS IP address is correct"
    echo "  - SSH is enabled on VPS"
    echo "  - You can login as 'trader' user"
    echo "  - Try: ssh $VPS_USER@$VPS_IP"
    exit 1
fi
print_status "Connection successful"

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
token.json
EOF

print_info "Uploading code files..."

# Upload code using rsync
rsync -avz --progress \
    --exclude-from=.rsync_exclude \
    --delete \
    ./ $VPS_USER@$VPS_IP:$VPS_PATH/

if [ $? -eq 0 ]; then
    print_status "Code uploaded successfully"
else
    print_error "Upload failed"
    exit 1
fi

# Clean up
rm .rsync_exclude

# Set proper permissions on VPS
print_info "Setting permissions..."
ssh $VPS_USER@$VPS_IP << EOF
cd $VPS_PATH
chmod +x deployment/*.sh
chmod +x deployment/*.py
mkdir -p logs/{daily,errors,trades,system}
echo "✅ Permissions set"
EOF

print_status "Permissions configured"

# Show next steps
echo ""
print_status "🎉 CODE UPLOAD COMPLETE!"
echo ""
print_info "Next steps:"
echo "1. SSH into your VPS: ssh $VPS_USER@$VPS_IP"
echo "2. Configure API credentials in .env on the server"
echo "3. Test the system: python3 deployment/test_deployment.py"
echo "4. Authenticate: .venv/bin/python auth.py"
echo "5. Start trading: sudo supervisorctl start trading_bot"
echo ""
print_info "To monitor: tail -f logs/supervisor.log"
print_status "Ready for production trading! 🚀"
