#!/bin/bash
"""
Quick Deployment Commands
Common deployment tasks in one script
"""

DEPLOY_HOST="${DEPLOY_HOST:-159.89.171.105}"
DEPLOY_USER="${DEPLOY_USER:-trader}"
DEPLOY_PATH="${DEPLOY_PATH:-/home/trader/trading_bot}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

show_help() {
    echo "🚀 QUICK DEPLOYMENT COMMANDS"
    echo "============================"
    echo ""
    echo "Usage: ./quick_deploy.sh [command]"
    echo ""
    echo "Commands:"
    echo "  deploy          - Full deployment (upload code + restart)"
    echo "  upload          - Upload code only"
    echo "  restart         - Restart services only"
    echo "  status          - Check system status"
    echo "  logs            - View live logs"
    echo "  auth            - Start authentication server"
    echo "  start           - Start trading bot"
    echo "  stop            - Stop trading bot"
    echo "  test            - Run deployment tests"
    echo ""
    echo "Examples:"
    echo "  ./quick_deploy.sh deploy     # Full deployment"
    echo "  ./quick_deploy.sh status     # Check status"
    echo "  ./quick_deploy.sh logs       # View logs"
}

case "$1" in
    "deploy")
        print_info "Running full deployment..."
        ./deploy.sh
        ;;
    
    "upload")
        print_info "Uploading code only..."
        DEPLOY_USER="$DEPLOY_USER" DEPLOY_PATH="$DEPLOY_PATH" ./deployment/upload_code.sh "$DEPLOY_HOST"
        ;;
    
    "restart")
        print_info "Restarting services..."
        ssh $DEPLOY_USER@$DEPLOY_HOST "
            sudo supervisorctl restart trading_bot_monitor
            echo '✅ Services restarted'
        "
        ;;
    
    "status")
        print_info "Checking system status..."
        ssh $DEPLOY_USER@$DEPLOY_HOST "
            cd $DEPLOY_PATH
            echo '📊 Supervisor Status:'
            sudo supervisorctl status
            echo ''
            echo '🔍 System Health:'
            source .venv/bin/activate
            python3 deployment/monitor.py --check
        "
        ;;
    
    "logs")
        print_info "Viewing live logs (Ctrl+C to exit)..."
        ssh $DEPLOY_USER@$DEPLOY_HOST "tail -f $DEPLOY_PATH/logs/supervisor.log"
        ;;
    
    "auth")
        print_info "Starting authentication server..."
        ssh $DEPLOY_USER@$DEPLOY_HOST "
            cd $DEPLOY_PATH
            source .venv/bin/activate
            echo '🚀 Starting Flask authentication...'
            echo '📡 Access via SSH tunnel: http://127.0.0.1:5001'
            python3 auth.py
        "
        ;;
    
    "start")
        print_info "Starting trading bot..."
        ssh $DEPLOY_USER@$DEPLOY_HOST "
            sudo supervisorctl start trading_bot
            sudo supervisorctl status trading_bot
        "
        ;;
    
    "stop")
        print_info "Stopping trading bot..."
        ssh $DEPLOY_USER@$DEPLOY_HOST "
            sudo supervisorctl stop trading_bot
            sudo supervisorctl status trading_bot
        "
        ;;
    
    "test")
        print_info "Running deployment tests..."
        ssh $DEPLOY_USER@$DEPLOY_HOST "
            cd $DEPLOY_PATH
            source .venv/bin/activate
            python3 deployment/test_deployment.py
        "
        ;;
    
    *)
        show_help
        ;;
esac
