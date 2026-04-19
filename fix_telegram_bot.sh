#!/bin/bash
# Fix Telegram Bot Spawn Error on EC2

echo "🔧 Diagnosing Telegram Bot Error"
echo "================================"
echo ""

cd /home/trader/trading_bot

echo "1. Check supervisor error logs:"
sudo supervisorctl tail telegram_bot stderr | tail -30

echo ""
echo "2. Try running manually to see error:"
.venv/bin/python deployment/telegram_bot.py &
MANUAL_PID=$!
sleep 3
kill $MANUAL_PID 2>/dev/null

echo ""
echo "3. Check if file exists:"
ls -lh deployment/telegram_bot.py

echo ""
echo "4. Check Python syntax:"
.venv/bin/python -m py_compile deployment/telegram_bot.py

echo ""
echo "5. Check imports:"
.venv/bin/python -c "import sys; sys.path.insert(0, '.'); import deployment.telegram_bot" 2>&1 | head -20

echo ""
echo "=== Diagnostic Complete ==="
