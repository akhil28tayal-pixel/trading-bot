#!/bin/bash
"""
Daily Cleanup Script
Runs daily maintenance tasks for the trading bot
"""

# Set script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Log file
LOG_FILE="$PROJECT_DIR/logs/daily_cleanup.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_message "🧹 Starting daily cleanup..."

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# 1. Archive old log files (older than 30 days)
log_message "📁 Archiving old log files..."
find logs/ -name "*.log" -type f -mtime +30 -exec gzip {} \;

# 2. Remove very old compressed logs (older than 90 days)
log_message "🗑️  Removing old compressed logs..."
find logs/ -name "*.log.gz" -type f -mtime +90 -delete

# 3. Clean up temporary files
log_message "🧽 Cleaning temporary files..."
find . -name "*.tmp" -type f -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -type f -delete

# 4. Reset daily risk state if needed
log_message "🛡️  Checking risk state..."
if [ -f "logs/risk_state.json" ]; then
    # Check if risk state is from previous day
    RISK_DATE=$(python3 -c "
import json
try:
    with open('logs/risk_state.json', 'r') as f:
        data = json.load(f)
    print(data.get('date', ''))
except:
    print('')
")
    
    TODAY=$(date '+%Y-%m-%d')
    if [ "$RISK_DATE" != "$TODAY" ]; then
        log_message "📊 Risk state is from previous day, will be reset on next run"
    fi
fi

# 5. Check disk space
log_message "💾 Checking disk space..."
DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    log_message "⚠️  WARNING: Disk usage is ${DISK_USAGE}%"
    # Send alert if telegram is configured
    python3 -c "
try:
    from deployment.telegram_notifier import send_alert
    send_alert('⚠️ High disk usage: ${DISK_USAGE}%', 'warning')
except:
    pass
" 2>/dev/null || true
fi

# 6. Generate daily summary
log_message "📊 Generating daily summary..."
python3 -c "
import sys
import os
sys.path.append('$PROJECT_DIR')

try:
    from deployment.production_risk import production_risk
    from deployment.telegram_notifier import send_daily_summary
    
    # Get daily summary
    summary = production_risk.get_daily_summary()
    
    # Send telegram summary if configured
    send_daily_summary(summary)
    
    # Log summary
    print(f'Daily Summary: PnL=₹{summary[\"daily_pnl\"]:.2f}, Trades={summary[\"trade_count\"]}')
    
except Exception as e:
    print(f'Error generating summary: {e}')
" | tee -a "$LOG_FILE"

# 7. Check for alerts that need attention
log_message "🚨 Checking for active alerts..."

# Check for authentication alerts
if [ -f "logs/auth_required.alert" ]; then
    log_message "⚠️  Authentication required alert is active"
fi

# Check for emergency stop
if [ -f ".emergency_stop" ]; then
    log_message "🚨 Emergency stop is active"
fi

# Check WebSocket status
if [ -f "logs/websocket_status.json" ]; then
    WS_CONNECTED=$(python3 -c "
import json
try:
    with open('logs/websocket_status.json', 'r') as f:
        data = json.load(f)
    print('true' if data.get('connected', False) else 'false')
except:
    print('unknown')
")
    log_message "📡 WebSocket status: $WS_CONNECTED"
fi

# 8. Update system status
log_message "🖥️  System status:"
echo "  CPU: $(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')" | tee -a "$LOG_FILE"
echo "  Memory: $(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')" | tee -a "$LOG_FILE"
echo "  Disk: ${DISK_USAGE}%" | tee -a "$LOG_FILE"

# 9. Backup important configuration files
log_message "💾 Backing up configuration..."
BACKUP_DIR="$PROJECT_DIR/backups/$(date '+%Y%m%d')"
mkdir -p "$BACKUP_DIR"

# Backup config files
cp config.py "$BACKUP_DIR/" 2>/dev/null || true
cp deployment/*.json "$BACKUP_DIR/" 2>/dev/null || true
cp token.json "$BACKUP_DIR/" 2>/dev/null || true

# Keep only last 7 days of backups
find "$PROJECT_DIR/backups" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true

log_message "✅ Daily cleanup completed successfully"

# 10. Optional: Send completion notification
python3 -c "
try:
    from deployment.telegram_notifier import send_alert
    import datetime as dt
    send_alert(f'🧹 Daily cleanup completed at {dt.datetime.now().strftime(\"%H:%M\")}', 'info')
except:
    pass
" 2>/dev/null || true

log_message "📝 Cleanup log saved to: $LOG_FILE"
