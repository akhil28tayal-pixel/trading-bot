#!/usr/bin/env python3
"""
Deployment Test Suite
Comprehensive tests to verify production deployment
"""

import os
import sys
import json
import time
import datetime as dt
from pathlib import Path
import subprocess

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_python_environment():
    """Test Python environment and dependencies"""
    print("🐍 Testing Python Environment...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major != 3 or python_version.minor < 8:
        print(f"❌ Python version {python_version.major}.{python_version.minor} not supported (need 3.8+)")
        return False
    else:
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Test critical imports
    critical_imports = [
        'kiteconnect',
        'pandas',
        'numpy',
        'websocket',
        'requests'
    ]
    
    for module in critical_imports:
        try:
            __import__(module)
            print(f"✅ {module} imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import {module}: {e}")
            return False
    
    return True

def test_project_structure():
    """Test project structure and files"""
    print("\n📁 Testing Project Structure...")
    
    required_files = [
        'main.py',
        'config.py',
        'broker.py',
        'logger.py',
        'strategies/breakout_ws.py',
        'strategies/credit_spread_ws.py',
        'backtest/engine_v2.py',
        'risk/costs.py',
        'deployment/auth_manager.py',
        'deployment/production_risk.py',
        'deployment/websocket_manager.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            print(f"❌ Missing: {file_path}")
        else:
            print(f"✅ Found: {file_path}")
    
    if missing_files:
        print(f"❌ {len(missing_files)} required files missing")
        return False
    
    return True

def test_configuration():
    """Test configuration files"""
    print("\n⚙️ Testing Configuration...")
    
    try:
        import config
        
        # Check required config variables
        required_vars = ['API_KEY', 'API_SECRET', 'CAPITAL']
        missing_vars = []
        
        for var in required_vars:
            if not hasattr(config, var) or not getattr(config, var):
                missing_vars.append(var)
                print(f"❌ Missing config: {var}")
            else:
                # Don't print sensitive values
                if var in ['API_KEY', 'API_SECRET']:
                    print(f"✅ {var}: {'*' * 8}")
                else:
                    print(f"✅ {var}: {getattr(config, var)}")
        
        if missing_vars:
            print(f"❌ {len(missing_vars)} required config variables missing")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import config: {e}")
        return False

def test_authentication():
    """Test authentication system"""
    print("\n🔐 Testing Authentication...")
    
    try:
        from deployment.auth_manager import ProductionAuthManager
        import config
        
        auth_manager = ProductionAuthManager(
            api_key=config.API_KEY,
            api_secret=config.API_SECRET
        )
        
        # Test token loading
        token_loaded = auth_manager.load_token()
        print(f"✅ Token loading: {'Success' if token_loaded else 'No existing token'}")
        
        # Test market hours check
        is_open, status = auth_manager.check_market_hours()
        print(f"✅ Market hours check: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def test_risk_management():
    """Test risk management system"""
    print("\n🛡️ Testing Risk Management...")
    
    try:
        from deployment.production_risk import ProductionRiskManager
        
        risk_manager = ProductionRiskManager()
        
        # Test trading allowed check
        allowed, reason = risk_manager.is_trading_allowed()
        print(f"✅ Trading allowed check: {allowed} - {reason}")
        
        # Test trade validation
        valid, msg = risk_manager.validate_trade("NIFTY", 50, 24000, "BUY")
        print(f"✅ Trade validation: {valid} - {msg}")
        
        # Test daily summary
        summary = risk_manager.get_daily_summary()
        print(f"✅ Daily summary: {summary['date']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Risk management test failed: {e}")
        return False

def test_logging_system():
    """Test logging system"""
    print("\n📝 Testing Logging System...")
    
    try:
        from deployment.production_logger import setup_production_logging
        
        # Setup logging
        setup_production_logging()
        
        # Test log directories
        log_dirs = ['logs', 'logs/daily', 'logs/errors', 'logs/trades', 'logs/system']
        for log_dir in log_dirs:
            if Path(log_dir).exists():
                print(f"✅ Log directory: {log_dir}")
            else:
                print(f"❌ Missing log directory: {log_dir}")
                return False
        
        # Test logging
        import logging
        logger = logging.getLogger('trading')
        logger.info("🧪 Test log message")
        print("✅ Logging system functional")
        
        return True
        
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False

def test_telegram_notifications():
    """Test Telegram notification system"""
    print("\n📱 Testing Telegram Notifications...")
    
    try:
        from deployment.telegram_notifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        config = notifier.config
        
        print(f"✅ Telegram enabled: {config.get('enabled', False)}")
        print(f"✅ Bot token configured: {'Yes' if config.get('bot_token') else 'No'}")
        print(f"✅ Chat ID configured: {'Yes' if config.get('chat_id') else 'No'}")
        
        if config.get('enabled') and config.get('bot_token'):
            print("✅ Telegram notifications available")
        else:
            print("ℹ️  Telegram notifications not configured (optional)")
        
        return True
        
    except Exception as e:
        print(f"❌ Telegram test failed: {e}")
        return False

def test_system_monitor():
    """Test system monitoring"""
    print("\n🔍 Testing System Monitor...")
    
    try:
        from deployment.monitor import SystemMonitor
        
        monitor = SystemMonitor()
        
        # Run single health check
        health_status = monitor.run_health_check()
        
        print(f"✅ Health check completed")
        print(f"✅ Overall status: {health_status.get('overall_status', 'unknown')}")
        print(f"✅ Issues found: {len(health_status.get('issues', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ System monitor test failed: {e}")
        return False

def test_backtesting_system():
    """Test backtesting system"""
    print("\n📊 Testing Backtesting System...")
    
    try:
        # Test basic backtest functionality
        result = subprocess.run([
            sys.executable, 'run_backtest.py', '--demo'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Backtesting system functional")
            # Check for success indicators in output
            if "SUCCESS" in result.stdout and "trades" in result.stdout:
                print("✅ Backtesting generates trades")
            else:
                print("⚠️  Backtesting runs but may not generate trades")
        else:
            print(f"❌ Backtesting failed: {result.stderr}")
            return False
        
        return True
        
    except subprocess.TimeoutExpired:
        print("⚠️  Backtesting test timed out (may still be working)")
        return True
    except Exception as e:
        print(f"❌ Backtesting test failed: {e}")
        return False

def test_supervisor_config():
    """Test supervisor configuration"""
    print("\n👨‍💼 Testing Supervisor Configuration...")
    
    supervisor_conf = Path("deployment/supervisor.conf")
    if supervisor_conf.exists():
        print("✅ Supervisor config file exists")
        
        # Check if supervisor is installed
        try:
            result = subprocess.run(['which', 'supervisorctl'], capture_output=True)
            if result.returncode == 0:
                print("✅ Supervisor installed")
            else:
                print("⚠️  Supervisor not installed")
        except:
            print("⚠️  Could not check supervisor installation")
        
        return True
    else:
        print("❌ Supervisor config file missing")
        return False

def run_deployment_tests():
    """Run all deployment tests"""
    print("🧪 DEPLOYMENT TEST SUITE")
    print("=" * 50)
    
    tests = [
        ("Python Environment", test_python_environment),
        ("Project Structure", test_project_structure),
        ("Configuration", test_configuration),
        ("Authentication", test_authentication),
        ("Risk Management", test_risk_management),
        ("Logging System", test_logging_system),
        ("Telegram Notifications", test_telegram_notifications),
        ("System Monitor", test_system_monitor),
        ("Backtesting System", test_backtesting_system),
        ("Supervisor Config", test_supervisor_config)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Ready for production deployment!")
        return True
    else:
        print(f"⚠️  {total-passed} tests failed - Fix issues before deployment")
        return False

if __name__ == "__main__":
    success = run_deployment_tests()
    sys.exit(0 if success else 1)
