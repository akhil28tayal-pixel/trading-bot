# WebSocket and Supervisor Issues - SOLUTION

## Issues Identified & Fixed

### 1. Dependencies Status: FIXED
- kiteconnect: INSTALLED
- websocket-client: ALREADY INSTALLED  
- psutil: ALREADY INSTALLED
- requests: ALREADY INSTALLED

### 2. WebSocket Subscription Issue: IDENTIFIED
The WebSocket `start_websocket()` function now requires both tokens and a callback parameter.

### 3. Supervisor Configuration: READY
Configuration exists but needs manual reload due to sudo password.

## Immediate Fix Steps

### Step 1: SSH into VPS and Fix Supervisor
```bash
ssh trader@159.89.171.105
# Password: TradingBot2024!

cd /home/trader/trading_bot

# Reload supervisor configuration
sudo supervisorctl reread
sudo supervisorctl update

# Start trading system
sudo supervisorctl start trading_system

# Check status
sudo supervisorctl status
```

### Step 2: Test WebSocket Connection
```bash
# Test WebSocket with proper callback
python3 -c "
import sys
sys.path.append('/home/trader/trading_bot')
from websocket.ws_client import start_websocket

def handle_ticks(ticks):
    print(f'Received {len(ticks)} ticks')

print('Testing WebSocket...')
result = start_websocket([256265], handle_ticks)
print(f'WebSocket result: {result}')
"
```

### Step 3: Monitor Logs
```bash
# Monitor bot logs
tail -f logs/supervisor.log

# Check for WebSocket connection
grep -i "websocket" logs/supervisor.log
```

## Expected Output

### Supervisor Status Should Show:
```
trading_system:trading_bot           RUNNING   pid 12345
trading_system:trading_bot_monitor   RUNNING   pid 12346
trading_system:telegram_bot          RUNNING   pid 12347
```

### WebSocket Test Should Show:
```
Testing WebSocket...
WebSocket result: True
Received X ticks
```

## Alternative: Manual Startup

If supervisor still has issues, use the manual startup script:

```bash
# Use the created startup script
./start_trading_bot.sh
```

## Troubleshooting

### If WebSocket Fails:
1. Check authentication: `python3 auth.py`
2. Verify token is not expired
3. Check network connectivity

### If Supervisor Fails:
1. Check config syntax: `sudo supervisorctl reread`
2. Check logs: `sudo supervisorctl tail trading_bot`
3. Restart supervisor: `sudo systemctl restart supervisor`

### If Port 5000 is in Use:
```bash
# Find what's using port 5000
sudo lsof -i :5000

# Kill the process if needed
sudo kill -9 <PID>
```

## Market Timing Status

The market timing module is working correctly:
- Market Status: WEEKEND (Saturday)
- Trading Allowed: False
- Next market open: Monday 9:15 AM

## Next Steps

1. **Fix supervisor** with the manual commands above
2. **Test WebSocket** when market opens (Monday 9:15 AM)
3. **Monitor logs** for connection status
4. **Verify trading** activates during market hours

## Success Indicators

- [ ] Supervisor shows all processes RUNNING
- [ ] WebSocket connects successfully
- [ ] Bot shows "Market OPEN" at 9:15 AM Monday
- [ ] Trading logic activates during market hours
- [ ] Bot sleeps properly after 3:30 PM

## Contact for Help

If issues persist:
1. Check logs: `tail -f logs/supervisor.log`
2. Verify dependencies: `pip list | grep kiteconnect`
3. Test authentication: `python3 auth.py`
4. Check market timing: `python3 -c "from utils.market_timing import market_timing; print(market_timing.get_market_status())"`

The system is ready - just needs the manual supervisor reload!
