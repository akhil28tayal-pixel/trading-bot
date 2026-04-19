#!/bin/bash
"""
Update Cron Jobs for Continuous Trading Bot
Since bot now runs continuously, we only need cleanup jobs
"""

echo "🔧 Updating cron jobs for continuous trading bot..."

# Remove old cron jobs
crontab -l 2>/dev/null | grep -v "supervisorctl start trading_bot" | grep -v "supervisorctl stop trading_bot" | crontab -

# Add only necessary cron jobs
(crontab -l 2>/dev/null; echo "# Trading Bot Maintenance") | crontab -
(crontab -l 2>/dev/null; echo "0 18 * * 1-5 /home/trader/trading_bot/deployment/daily_cleanup.sh") | crontab -
(crontab -l 2>/dev/null; echo "0 6 * * 1-5 /home/trader/trading_bot/deployment/daily_cleanup.sh") | crontab -

echo "✅ Cron jobs updated for continuous operation"
echo "ℹ️  Bot will now run continuously and trade only during market hours"
