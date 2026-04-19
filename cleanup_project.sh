#!/bin/bash
# Project Cleanup Script
# Removes redundant and obsolete files while keeping essential components

set -e

echo "🧹 Trading Bot Project Cleanup"
echo "=============================="
echo ""
echo "This script will remove redundant files from the project."
echo "A backup will be created before deletion."
echo ""

# Create backup directory
BACKUP_DIR="project_backup_$(date +%Y%m%d_%H%M%S)"
echo "📦 Creating backup in: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Function to backup and remove file
backup_and_remove() {
    local file="$1"
    if [ -e "$file" ]; then
        echo "  Removing: $file"
        # Create parent directory in backup
        local parent_dir=$(dirname "$file")
        mkdir -p "$BACKUP_DIR/$parent_dir"
        # Move to backup
        cp -r "$file" "$BACKUP_DIR/$file" 2>/dev/null || true
        rm -rf "$file"
    fi
}

echo ""
echo "🗑️  Removing Duplicate Deployment Scripts..."
backup_and_remove "deploy.sh"
backup_and_remove "deploy_to_ec2.sh"
backup_and_remove "deployment/deploy_to_vps.sh"
backup_and_remove "deployment/upload_code.sh"
backup_and_remove "push.sh"
backup_and_remove "quick_deploy.sh"
backup_and_remove "quick_fix.sh"
backup_and_remove "deploy_with_github_sync.sh"

echo ""
echo "📄 Removing Duplicate/Old Documentation..."
backup_and_remove "AWS_DEPLOYMENT.md"
backup_and_remove "EC2_DEPLOYMENT_GUIDE.md"
backup_and_remove "PROJECT_STRUCTURE.md"
backup_and_remove "PROJECT_SUMMARY.md"
backup_and_remove "final_solution.md"
backup_and_remove "MANUAL_SUPERVISOR_FIX.md"
backup_and_remove "GITHUB_SETUP.md"

echo ""
echo "🔧 Removing Setup/Temporary Scripts..."
backup_and_remove "setup_github.sh"
backup_and_remove "setup_telegram.py"
backup_and_remove "fix_ssh_ec2.sh"
backup_and_remove "cleanup_production.sh"

echo ""
echo "📦 Removing Redundant Deployment Files..."
backup_and_remove "deployment/auth_manager.py"
backup_and_remove "deployment/manual_auth.py"
backup_and_remove "deployment/production_logger.py"
backup_and_remove "deployment/production_risk.py"
backup_and_remove "deployment/websocket_manager.py"
backup_and_remove "deployment/telegram_notifier.py"
backup_and_remove "deployment/monitor.py"
backup_and_remove "deployment/test_deployment.py"
backup_and_remove "deployment/daily_cleanup.sh"
backup_and_remove "deployment/update_cron.sh"
backup_and_remove "deployment/telegram_bot.conf"
backup_and_remove "deployment/risk_config.json"
backup_and_remove "deployment/telegram_config.json"

echo ""
echo "🧪 Removing Old Test Files..."
backup_and_remove "test_costs.py"
backup_and_remove "test_execution.py"
backup_and_remove "backtesting_scripts/demo_backtest.py"
backup_and_remove "backtesting_scripts/debug_backtest.py"
backup_and_remove "backtesting_scripts/test_enhanced_backtest.py"
backup_and_remove "backtesting_scripts/test_fixed_strategies.py"
backup_and_remove "backtesting_scripts/test_strategy_integration.py"
backup_and_remove "backtesting_scripts/FINAL_WORKING_STRATEGIES.py"
backup_and_remove "backtesting_scripts/BACKTEST_TEST_RESULTS.md"
backup_and_remove "backtesting_scripts/SOLUTION_SUMMARY.md"

echo ""
echo "🗂️  Removing Empty __pycache__ Directories..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo ""
echo "✅ Cleanup Complete!"
echo ""
echo "📊 Summary:"
echo "  - Backup created: $BACKUP_DIR"
echo "  - Removed: ~45 redundant files"
echo "  - Kept: ~30 essential files"
echo ""
echo "📁 Essential Files Remaining:"
echo "  ✅ Core system (main.py, auth.py, broker.py, config.py, etc.)"
echo "  ✅ Strategies (breakout_ws.py, credit_spread_ws.py)"
echo "  ✅ Risk management (risk/, 4 files)"
echo "  ✅ Backtesting engine (backtest/, 7 files)"
echo "  ✅ Backtesting scripts (5 essential files)"
echo "  ✅ Utilities (utils/, websocket/)"
echo "  ✅ Deployment (deploy_ec2.sh, telegram_bot.py, supervisor.conf)"
echo "  ✅ Documentation (README.md, PROJECT_OVERVIEW.md)"
echo "  ✅ Git integration (auto_push.sh, .gitignore)"
echo ""
echo "🔄 Next Steps:"
echo "  1. Review the backup in: $BACKUP_DIR"
echo "  2. Test the system: python3 run_backtest.py --demo"
echo "  3. If everything works, delete backup: rm -rf $BACKUP_DIR"
echo "  4. Commit changes: ./auto_push.sh"
echo ""
echo "⚠️  If you need to restore, the backup is in: $BACKUP_DIR"
