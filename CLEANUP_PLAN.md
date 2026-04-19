# 🧹 Project Cleanup Analysis

## Files to KEEP (Essential)

### Core Trading System
- ✅ `main.py` - Live trading entry point
- ✅ `auth.py` - Zerodha authentication
- ✅ `broker.py` - Broker interface
- ✅ `config.py` - Configuration
- ✅ `logger.py` - Logging
- ✅ `notifier.py` - Notifications
- ✅ `requirements.txt` - Dependencies
- ✅ `.env.example` - Environment template
- ✅ `.gitignore` - Git ignore rules

### Strategies
- ✅ `strategies/breakout_ws.py` - ORB breakout strategy
- ✅ `strategies/credit_spread_ws.py` - Credit spread strategy

### Risk Management
- ✅ `risk/risk.py` - Core risk management
- ✅ `risk/position_sizing.py` - Position sizing
- ✅ `risk/costs.py` - Cost calculations
- ✅ `risk/execution.py` - Realistic execution

### Backtesting Engine
- ✅ `backtest/engine_v2.py` - Backtesting engine
- ✅ `backtest/execution.py` - Execution simulation
- ✅ `backtest/oms.py` - Order management
- ✅ `backtest/data.py` - Data handling
- ✅ `backtest/metrics.py` - Performance metrics
- ✅ `backtest/report.py` - Report generation
- ✅ `backtest/strategy_adapter.py` - Strategy adapter

### Backtesting Scripts (Keep Main Ones)
- ✅ `run_backtest.py` - Main launcher
- ✅ `backtesting_scripts/run_backtest_v2.py` - Main backtest
- ✅ `backtesting_scripts/WORKING_BACKTEST_DEMO.py` - Demo
- ✅ `backtesting_scripts/test_backtest_system.py` - Tests
- ✅ `backtesting_scripts/README.md` - Documentation

### Utilities
- ✅ `utils/instruments.py` - Instrument helpers
- ✅ `websocket/ws_client.py` - WebSocket client

### Deployment (Essential)
- ✅ `deploy_ec2.sh` - EC2 deployment (MAIN)
- ✅ `deployment/telegram_bot.py` - Telegram monitoring
- ✅ `deployment/supervisor.conf` - Process management
- ✅ `deployment/systemd.service` - System service

### Documentation (Keep Main)
- ✅ `README.md` - Main documentation
- ✅ `PROJECT_OVERVIEW.md` - Comprehensive overview

### Git/GitHub
- ✅ `auto_push.sh` - Auto-push script
- ✅ `.git/` - Git repository
- ✅ `.gitignore` - Git ignore

---

## Files to REMOVE (Redundant/Obsolete)

### ❌ Duplicate Deployment Scripts
- ❌ `deploy.sh` - OLD VPS script (replaced by deploy_ec2.sh)
- ❌ `deploy_to_ec2.sh` - Duplicate EC2 script
- ❌ `deployment/deploy_to_vps.sh` - OLD VPS script
- ❌ `deployment/upload_code.sh` - Redundant
- ❌ `push.sh` - Replaced by auto_push.sh
- ❌ `quick_deploy.sh` - VPS-specific, not needed
- ❌ `quick_fix.sh` - Temporary fix script

### ❌ Duplicate/Old Documentation
- ❌ `AWS_DEPLOYMENT.md` - Covered in PROJECT_OVERVIEW.md
- ❌ `EC2_DEPLOYMENT_GUIDE.md` - Covered in PROJECT_OVERVIEW.md
- ❌ `PROJECT_STRUCTURE.md` - Covered in PROJECT_OVERVIEW.md
- ❌ `PROJECT_SUMMARY.md` - Covered in PROJECT_OVERVIEW.md
- ❌ `final_solution.md` - Old documentation
- ❌ `MANUAL_SUPERVISOR_FIX.md` - Temporary fix doc
- ❌ `GITHUB_SETUP.md` - Minimal file, not needed

### ❌ Setup/Temporary Scripts
- ❌ `setup_github.sh` - Already set up
- ❌ `setup_telegram.py` - Already set up
- ❌ `fix_ssh_ec2.sh` - Troubleshooting script, not needed
- ❌ `cleanup_production.sh` - VPS-specific
- ❌ `deploy_with_github_sync.sh` - Can use auto_push.sh + deploy_ec2.sh

### ❌ Redundant Deployment Files
- ❌ `deployment/auth_manager.py` - Redundant with auth.py
- ❌ `deployment/manual_auth.py` - Redundant with auth.py
- ❌ `deployment/production_logger.py` - Redundant with logger.py
- ❌ `deployment/production_risk.py` - Redundant with risk/
- ❌ `deployment/websocket_manager.py` - Redundant with websocket/
- ❌ `deployment/telegram_notifier.py` - Redundant with notifier.py
- ❌ `deployment/monitor.py` - Can be simplified or removed
- ❌ `deployment/test_deployment.py` - Test file
- ❌ `deployment/daily_cleanup.sh` - VPS-specific
- ❌ `deployment/update_cron.sh` - VPS-specific
- ❌ `deployment/telegram_bot.conf` - Can be in supervisor.conf
- ❌ `deployment/risk_config.json` - Use .env instead
- ❌ `deployment/telegram_config.json` - Use .env instead

### ❌ Test Files (Keep Only Essential)
- ❌ `test_costs.py` - Development test
- ❌ `test_execution.py` - Development test
- ❌ `backtesting_scripts/demo_backtest.py` - Duplicate of WORKING_BACKTEST_DEMO.py
- ❌ `backtesting_scripts/debug_backtest.py` - Debug tool
- ❌ `backtesting_scripts/test_enhanced_backtest.py` - Old test
- ❌ `backtesting_scripts/test_fixed_strategies.py` - Old test
- ❌ `backtesting_scripts/test_strategy_integration.py` - Old test
- ❌ `backtesting_scripts/FINAL_WORKING_STRATEGIES.py` - Old version
- ❌ `backtesting_scripts/BACKTEST_TEST_RESULTS.md` - Old results
- ❌ `backtesting_scripts/SOLUTION_SUMMARY.md` - Old summary

### ❌ Cache/Runtime Files
- ❌ `__pycache__/` - Python cache (gitignored)
- ❌ `bot.log` - Log file (gitignored)
- ❌ `logs/` - Log directory (gitignored)
- ❌ `data_cache/` - Cache directory (gitignored)
- ❌ `.venv/` - Virtual environment (gitignored)
- ❌ `token.json` - Auth token (gitignored, but keep for runtime)

---

## Summary

### Files to Keep: ~30 essential files
- Core system: 9 files
- Strategies: 2 files
- Risk: 4 files
- Backtest: 7 files
- Backtest scripts: 5 files
- Utils: 2 files
- Deployment: 4 files
- Documentation: 2 files
- Git: 2 files

### Files to Remove: ~45 redundant files
- Duplicate deployment scripts: 10 files
- Duplicate documentation: 8 files
- Setup/temporary scripts: 7 files
- Redundant deployment files: 13 files
- Old test files: 10 files
- Cache/runtime: 5 directories

### Space Savings: ~200+ KB of redundant code/docs
