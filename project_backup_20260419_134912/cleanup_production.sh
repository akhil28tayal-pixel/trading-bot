#!/bin/bash
"""
Clean Production VPS
Removes all .sh and .md files from production
"""

VPS_IP="159.89.171.105"
VPS_USER="trader"

echo "Cleaning production VPS - removing .sh and .md files..."

# SSH into VPS
ssh $VPS_USER@$VPS_IP << 'EOF'
cd /home/trader/trading_bot

echo "=== PRODUCTION CLEANUP ==="

# 1. List all .sh files before removal
echo "1. .sh files found:"
find . -name "*.sh" -not -path "./.venv/*" | sort

echo -e "\n2. .md files found:"
find . -name "*.md" -not -path "./.venv/*" | sort

echo -e "\n=== REMOVING FILES ==="

# 2. Remove all .sh files
echo "3. Removing .sh files..."
find . -name "*.sh" -not -path "./.venv/*" -delete

# 3. Remove all .md files  
echo "4. Removing .md files..."
find . -name "*.md" -not -path "./.venv/*" -delete

echo -e "\n=== VERIFYING CLEANUP ==="

# 4. Verify files are removed
echo "5. Verifying .sh files are removed:"
sh_files=$(find . -name "*.sh" -not -path "./.venv/*" | wc -l)
echo "   .sh files remaining: $sh_files"

echo "6. Verifying .md files are removed:"
md_files=$(find . -name "*.md" -not -path "./.venv/*" | wc -l)
echo "   .md files remaining: $md_files"

echo -e "\n=== CHECKING ESSENTIAL FILES ==="

# 5. Verify essential files are still present
echo "7. Essential files check:"
essential_files=(
    "main.py"
    "auth.py"
    "config.py"
    "logger.py"
    "notifier.py"
    "broker.py"
    "run_backtest.py"
    "setup_telegram.py"
    "test_costs.py"
    "test_execution.py"
    "websocket/ws_client.py"
    "utils/instruments.py"
    "strategies/breakout_ws.py"
    "strategies/credit_spread_ws.py"
    "risk/risk.py"
    "deployment/monitor.py"
    "deployment/telegram_bot.py"
)

for file in "${essential_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   $file: PRESENT"
    else
        echo "   $file: MISSING"
    fi
done

echo -e "\n=== SYSTEM STATUS ==="

# 6. Check system status
echo "8. System status:"
sudo supervisorctl status 2>/dev/null || echo "   Supervisor requires password"

echo -e "\n=== CLEANUP COMPLETE ==="

echo "9. Production cleanup complete!"
echo ""
echo "Files removed:"
echo "- All .sh files (shell scripts)"
echo "- All .md files (documentation)"
echo ""
echo "Files preserved:"
echo "- Essential Python files"
echo "- Core directories"
echo "- Configuration files"
echo ""
echo "Production is now clean and minimal!"

EOF
