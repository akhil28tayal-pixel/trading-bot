# Project Structure

**Cleaned and Organized Trading Bot Project**  
**Date**: April 19, 2026

---

## Directory Structure

```
trading_bot/
|-- .env                    # Environment variables
|-- .env.example           # Environment variables template
|-- .gitignore             # Git ignore rules
|-- .venv/                 # Python virtual environment
|-- __pycache__/           # Python cache files
|
|-- auth.py                # Kite authentication handler
|-- broker.py              # Broker interface
|-- config.py              # Configuration settings
|-- logger.py              # Logging utilities
|-- main.py                # Main trading bot entry point
|-- notifier.py            # Telegram notifications
|-- requirements.txt       # Python dependencies
|-- run_backtest.py        # Backtest runner
|-- token.json             # Saved authentication token
|
|-- backtest/              # Backtesting engine
|   |-- engine_v2.py       # Backtesting engine
|   |-- execution.py       # Order execution simulation
|   |-- strategy_adapter.py # Strategy adapter for backtesting
|
|-- backtesting_scripts/   # Backtesting utilities
|   |-- FINAL_WORKING_STRATEGIES.py
|   |-- SOLUTION_SUMMARY.md
|   |-- debug_backtest.py
|   |-- demo_backtest.py
|   |-- test_enhanced_backtest.py
|   |-- test_fixed_strategies.py
|   |-- test_strategy_integration.py
|
|-- deployment/            # Deployment configurations
|   |-- auth/              # Authentication modules
|   |   |-- telegram_auth_handler.py
|   |   |-- telegram_mobile_auth.py
|   |-- telegram_bot.py    # Telegram bot interface
|   |-- telegram_bot.conf  # Supervisor configuration
|
|-- docs/                  # Documentation
|   |-- FINAL_PROJECT_STATUS.md
|   |-- PROJECT_OVERVIEW.md
|   |-- README.md
|   |-- PROJECT_STRUCTURE.md
|
|-- logs/                  # Log files directory
|
|-- risk/                  # Risk management
|   |-- position_sizing.py # Position sizing calculations
|   |-- risk.py           # Risk monitoring
|
|-- scripts/              # Utility scripts
|   |-- auto_push.sh      # Git auto-push script
|   |-- deploy_ec2.sh     # EC2 deployment script
|
|-- strategies/            # Trading strategies
|   |-- breakout_ws.py    # Breakout strategy
|   |-- credit_spread_ws.py # Credit spread strategy
|
|-- utils/                 # Utility functions
|   |-- helpers.py        # Helper functions
|
|-- websocket/             # WebSocket handling
|   -- kite_ws.py         # Kite WebSocket client
```

---

## Core Files Description

### **Main Application**
- **`main.py`** - Main trading bot entry point
- **`config.py`** - Configuration and environment variables
- **`auth.py`** - Kite Connect authentication
- **`broker.py`** - Broker interface for trading operations

### **Trading Components**
- **`strategies/`** - Trading strategies (breakout, credit spread)
- **`risk/`** - Risk management and position sizing
- **`websocket/`** - Real-time data handling

### **Backtesting**
- **`backtest/`** - Backtesting engine and execution
- **`backtesting_scripts/`** - Backtesting utilities and tests
- **`run_backtest.py`** - Backtest runner

### **Deployment**
- **`deployment/`** - Production deployment files
- **`deployment/telegram_bot.py`** - Telegram bot for monitoring
- **`deployment/auth/`** - Authentication handlers

### **Utilities**
- **`scripts/`** - Deployment and utility scripts
- **`utils/`** - Helper functions
- **`logger.py`** - Logging utilities
- **`notifier.py`** - Telegram notifications

---

## Cleaned Up Files

### **Removed Redundant Files:**
- Multiple authentication setup scripts (domain auth variations)
- Duplicate guide files and documentation
- Backup directories and old log files
- Unused test files and temporary scripts
- Redundant setup scripts

### **Organized Structure:**
- **`docs/`** - All documentation files
- **`scripts/`** - Utility and deployment scripts
- **`deployment/auth/`** - Authentication modules

---

## Quick Start

### **Development Setup:**
```bash
# Clone and setup
git clone <repository>
cd trading_bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your credentials

# Run
python main.py
```

### **Deployment:**
```bash
# Deploy to EC2
./scripts/deploy_ec2.sh

# Or manual deployment
cd deployment
python telegram_bot.py
```

---

## Key Features

- **Live Trading**: Real-time trading with WebSocket data
- **Backtesting**: Comprehensive backtesting engine
- **Risk Management**: Position sizing and risk limits
- **Telegram Integration**: Real-time notifications and control
- **Mobile Authentication**: Kite Connect authentication via Telegram
- **Multiple Strategies**: Breakout and credit spread strategies
- **Professional Setup**: Nginx proxy with SSL support

---

## Configuration

### **Environment Variables (.env):**
- `KITE_API_KEY` - Zerodha Kite API key
- `KITE_API_SECRET` - Zerodha Kite API secret
- `TELEGRAM_BOT_TOKEN` - Telegram bot token
- `TELEGRAM_CHAT_ID` - Telegram chat ID
- `TRADING_MODE` - LIVE, PAPER, or BACKTEST
- `CAPITAL` - Trading capital amount

### **Kite Authentication:**
1. Update redirect URL in Kite developer portal
2. Send `/auth` command to Telegram bot
3. Follow authentication link
4. Token automatically saved

---

## Monitoring & Control

### **Telegram Commands:**
- `/status` - Bot status and positions
- `/pnl` - Profit and loss summary
- `/positions` - Current positions
- `/orders` - Recent orders
- `/auth` - Kite authentication
- `/checktoken` - Token validity check

### **Logs:**
- Main bot logs: `logs/main.log`
- Telegram bot logs: `logs/telegram_bot.log`
- Authentication logs: `logs/auth.log`

---

## Deployment Architecture

### **Production Setup:**
- **EC2 Instance**: Ubuntu 24.04 LTS
- **Web Server**: Nginx with SSL
- **Process Manager**: Supervisor
- **Domain**: atcpa.co with HTTPS
- **Authentication**: Mobile-friendly via Telegram

### **Security:**
- SSL/TLS encryption
- Environment variable protection
- Secure token storage
- Risk limits and monitoring

---

This cleaned structure provides a maintainable, production-ready trading bot with professional deployment and monitoring capabilities.
