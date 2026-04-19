# Manual Supervisor Fix Required

## Issue
The `trading_system` process group exists in configuration but supervisor hasn't loaded it yet.

## Solution: Manual Commands Required

SSH into your VPS and run these commands manually:

```bash
ssh trader@159.89.171.105
# Password: TradingBot2024!

cd /home/trader/trading_bot
```

### Step 1: Reload Supervisor Configuration
```bash
sudo supervisorctl reread
sudo supervisorctl update
```

### Step 2: Start Individual Processes
```bash
sudo supervisorctl start trading_bot
sudo supervisorctl start trading_bot_monitor
sudo supervisorctl start telegram_bot
```

### Step 3: Start Process Group
```bash
sudo supervisorctl start trading_system
```

### Step 4: Check Status
```bash
sudo supervisorctl status
```

## Expected Output
You should see:
```
trading_system:trading_bot           RUNNING   pid 12345
trading_system:trading_bot_monitor   RUNNING   pid 12346
trading_system:telegram_bot          RUNNING   pid 12347
```

## If Process Group Still Fails

If `trading_system` still doesn't work, use individual processes:

```bash
sudo supervisorctl start trading_bot
sudo supervisorctl start trading_bot_monitor
sudo supervisorctl start telegram_bot
```

## Configuration Status
Your supervisor configuration is correct:
- Individual programs: trading_bot, trading_bot_monitor, telegram_bot
- Process group: trading_system (includes all 3 programs)
- All paths and permissions are correct

## Market Timing Status
The market timing module is working correctly:
- Current: WEEKEND (Saturday)
- Next market open: Monday 9:15 AM

## Next Steps After Fix
1. Run the manual commands above
2. Verify all processes are running
3. Monitor logs: `tail -f logs/supervisor.log`
4. Test WebSocket when market opens

The issue is simply that supervisor needs to be reloaded with the new configuration.
