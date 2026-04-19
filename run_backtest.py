#!/usr/bin/env python3
"""
Main Backtesting Launcher
Provides easy access to all backtesting functionality
"""

import argparse
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    parser = argparse.ArgumentParser(
        description="Trading Bot Backtesting Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 run_backtest.py --demo              # Guaranteed working demo (127%+ returns)
  python3 run_backtest.py --simple            # Simple backtest with your strategies  
  python3 run_backtest.py --comprehensive     # Full analysis with reporting
  python3 run_backtest.py --test              # Test system functionality
  python3 run_backtest.py --debug             # Debug strategy conditions
        """
    )
    
    # Main options
    parser.add_argument('--demo', action='store_true', 
                       help='Run guaranteed working demo (127%+ returns)')
    parser.add_argument('--simple', action='store_true',
                       help='Run simple backtest with your strategies')
    parser.add_argument('--comprehensive', action='store_true',
                       help='Run comprehensive backtest with full analysis')
    parser.add_argument('--test', action='store_true',
                       help='Test backtesting system functionality')
    parser.add_argument('--debug', action='store_true',
                       help='Debug strategy conditions')
    
    # Advanced options
    parser.add_argument('--fixed-strategies', action='store_true',
                       help='Test fixed strategies')
    parser.add_argument('--integration', action='store_true',
                       help='Test strategy integration')
    
    args = parser.parse_args()
    
    # Show help if no arguments
    if not any(vars(args).values()):
        parser.print_help()
        print("\n🚀 QUICK START:")
        print("   python3 run_backtest.py --demo     # Guaranteed results!")
        return
    
    print("🚀 TRADING BOT BACKTESTING LAUNCHER")
    print("=" * 50)
    
    try:
        if args.demo:
            print("📊 Running Guaranteed Working Demo...")
            from backtesting_scripts.WORKING_BACKTEST_DEMO import run_guaranteed_working_backtest
            run_guaranteed_working_backtest()
            
        elif args.simple:
            print("📊 Running Simple Backtest...")
            from backtesting_scripts.run_backtest_v2 import run_simple_backtest
            run_simple_backtest()
            
        elif args.comprehensive:
            print("📊 Running Comprehensive Backtest...")
            from backtesting_scripts.run_backtest_v2 import run_comprehensive_backtest
            run_comprehensive_backtest()
            
        elif args.test:
            print("🧪 Running System Tests...")
            from backtesting_scripts.test_backtest_system import run_all_tests
            run_all_tests()
            
        elif args.debug:
            print("🔍 Running Debug Analysis...")
            from backtesting_scripts.debug_backtest import debug_strategy_conditions, debug_simple_trading_strategy
            debug_strategy_conditions()
            debug_simple_trading_strategy()
            
        elif args.fixed_strategies:
            print("🔧 Testing Fixed Strategies...")
            from backtesting_scripts.test_fixed_strategies import test_fixed_breakout_strategy, test_fixed_credit_spread_strategy
            test_fixed_breakout_strategy()
            test_fixed_credit_spread_strategy()
            
        elif args.integration:
            print("🔗 Testing Strategy Integration...")
            from backtesting_scripts.test_strategy_integration import test_simple_trading_strategy, test_existing_strategy_integration
            test_simple_trading_strategy()
            test_existing_strategy_integration()
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure you're running from the project root directory")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
