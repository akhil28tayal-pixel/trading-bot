#!/usr/bin/env python3
"""
Test the fixed strategies with backtesting engine
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datetime as dt
from backtest.engine_v2 import BacktestEngine, BacktestConfig
from backtest.data import DataProvider
from backtest.strategy_adapter import BacktestContext

# Import fixed strategies
import strategies.breakout_ws as breakout_strategy
import strategies.credit_spread_ws as credit_spread_strategy


def test_fixed_breakout_strategy():
    """Test the fixed breakout strategy"""
    
    print("🧪 TESTING FIXED BREAKOUT STRATEGY")
    print("=" * 60)
    
    # Create config
    config = BacktestConfig(
        start_date=dt.datetime(2024, 1, 1),
        end_date=dt.datetime(2024, 1, 10),  # 10 days
        initial_capital=200000,  # Higher capital for better trades
        enable_slippage=True,
        enable_costs=True,
        verbose=True
    )
    
    # Create engine
    engine = BacktestEngine(config)
    
    # Add market data
    data_provider = DataProvider()
    
    nifty_data = data_provider.get_data(256265, config.start_date, config.end_date)
    engine.add_market_data("NIFTY", nifty_data, 256265)
    
    banknifty_data = data_provider.get_data(260105, config.start_date, config.end_date)
    engine.add_market_data("BANKNIFTY", banknifty_data, 260105)
    
    print(f"✅ NIFTY: {len(nifty_data)} bars")
    print(f"✅ BANKNIFTY: {len(banknifty_data)} bars")
    
    # Create strategy wrappers
    def nifty_breakout(ticks):
        breakout_strategy.process_ticks(ticks, "NIFTY")
    
    def banknifty_breakout(ticks):
        breakout_strategy.process_ticks(ticks, "BANKNIFTY")
    
    # Run backtest
    context = BacktestContext(engine)
    
    with context:
        engine.add_strategy_callback(nifty_breakout)
        engine.add_strategy_callback(banknifty_breakout)
        print("✅ Breakout strategies added")
        
        print("\n🔄 Running breakout backtest...")
        results = engine.run()
    
    # Analyze results
    summary = results['summary']
    print(f"\n📈 BREAKOUT STRATEGY RESULTS:")
    print(f"   Initial Capital: ₹{summary['initial_capital']:,.2f}")
    print(f"   Final Capital: ₹{summary['final_capital']:,.2f}")
    print(f"   Total Return: {summary['total_return']:.2%}")
    print(f"   Total Trades: {summary['total_trades']}")
    
    # Execution stats
    exec_stats = engine.execution_engine.get_execution_statistics()
    print(f"\n⚡ EXECUTION STATS:")
    print(f"   Total Orders: {exec_stats['total_executions']}")
    print(f"   Slippage Cost: ₹{exec_stats['total_slippage_cost']:.2f}")
    print(f"   Transaction Costs: ₹{exec_stats['total_transaction_costs']:.2f}")
    
    return results


def test_fixed_credit_spread_strategy():
    """Test the fixed credit spread strategy"""
    
    print("\n🧪 TESTING FIXED CREDIT SPREAD STRATEGY")
    print("=" * 60)
    
    # Create config
    config = BacktestConfig(
        start_date=dt.datetime(2024, 1, 1),
        end_date=dt.datetime(2024, 1, 15),  # 15 days
        initial_capital=300000,  # Higher capital for spreads
        enable_slippage=True,
        enable_costs=True,
        verbose=True
    )
    
    # Create engine
    engine = BacktestEngine(config)
    
    # Add market data
    data_provider = DataProvider()
    
    nifty_data = data_provider.get_data(256265, config.start_date, config.end_date)
    engine.add_market_data("NIFTY", nifty_data, 256265)
    
    banknifty_data = data_provider.get_data(260105, config.start_date, config.end_date)
    engine.add_market_data("BANKNIFTY", banknifty_data, 260105)
    
    print(f"✅ NIFTY: {len(nifty_data)} bars")
    print(f"✅ BANKNIFTY: {len(banknifty_data)} bars")
    
    # Create strategy wrappers
    def nifty_credit_spread(ticks):
        credit_spread_strategy.process_ticks(ticks, "NIFTY")
    
    def banknifty_credit_spread(ticks):
        credit_spread_strategy.process_ticks(ticks, "BANKNIFTY")
    
    # Run backtest
    context = BacktestContext(engine)
    
    with context:
        engine.add_strategy_callback(nifty_credit_spread)
        engine.add_strategy_callback(banknifty_credit_spread)
        print("✅ Credit spread strategies added")
        
        print("\n🔄 Running credit spread backtest...")
        results = engine.run()
    
    # Analyze results
    summary = results['summary']
    print(f"\n📈 CREDIT SPREAD STRATEGY RESULTS:")
    print(f"   Initial Capital: ₹{summary['initial_capital']:,.2f}")
    print(f"   Final Capital: ₹{summary['final_capital']:,.2f}")
    print(f"   Total Return: {summary['total_return']:.2%}")
    print(f"   Total Trades: {summary['total_trades']}")
    
    # Execution stats
    exec_stats = engine.execution_engine.get_execution_statistics()
    print(f"\n⚡ EXECUTION STATS:")
    print(f"   Total Orders: {exec_stats['total_executions']}")
    print(f"   Slippage Cost: ₹{exec_stats['total_slippage_cost']:.2f}")
    print(f"   Transaction Costs: ₹{exec_stats['total_transaction_costs']:.2f}")
    
    return results


def test_combined_strategies():
    """Test both strategies together"""
    
    print("\n🧪 TESTING COMBINED STRATEGIES")
    print("=" * 60)
    
    # Create config
    config = BacktestConfig(
        start_date=dt.datetime(2024, 1, 1),
        end_date=dt.datetime(2024, 1, 20),  # 20 days
        initial_capital=500000,  # Higher capital for both strategies
        enable_slippage=True,
        enable_costs=True,
        verbose=False  # Less verbose for combined test
    )
    
    # Create engine
    engine = BacktestEngine(config)
    
    # Add market data
    data_provider = DataProvider()
    
    nifty_data = data_provider.get_data(256265, config.start_date, config.end_date)
    engine.add_market_data("NIFTY", nifty_data, 256265)
    
    banknifty_data = data_provider.get_data(260105, config.start_date, config.end_date)
    engine.add_market_data("BANKNIFTY", banknifty_data, 260105)
    
    print(f"✅ NIFTY: {len(nifty_data)} bars")
    print(f"✅ BANKNIFTY: {len(banknifty_data)} bars")
    
    # Create combined strategy
    def combined_strategy(ticks):
        # Run both strategies
        breakout_strategy.process_ticks(ticks, "NIFTY")
        breakout_strategy.process_ticks(ticks, "BANKNIFTY")
        credit_spread_strategy.process_ticks(ticks, "NIFTY")
        credit_spread_strategy.process_ticks(ticks, "BANKNIFTY")
    
    # Run backtest
    context = BacktestContext(engine)
    
    with context:
        engine.add_strategy_callback(combined_strategy)
        print("✅ Combined strategies added")
        
        print("\n🔄 Running combined backtest...")
        results = engine.run()
    
    # Comprehensive analysis
    summary = results['summary']
    print(f"\n📈 COMBINED STRATEGIES RESULTS:")
    print(f"   Initial Capital: ₹{summary['initial_capital']:,.2f}")
    print(f"   Final Capital: ₹{summary['final_capital']:,.2f}")
    print(f"   Total Return: {summary['total_return']:.2%}")
    print(f"   Total P&L: ₹{summary['total_pnl']:,.2f}")
    print(f"   Total Trades: {summary['total_trades']}")
    print(f"   Execution Time: {summary['execution_time']:.2f}s")
    
    # Detailed execution analysis
    exec_stats = engine.execution_engine.get_execution_statistics()
    print(f"\n⚡ DETAILED EXECUTION ANALYSIS:")
    print(f"   Total Orders: {exec_stats['total_executions']}")
    print(f"   Slippage Cost: ₹{exec_stats['total_slippage_cost']:.2f}")
    print(f"   Transaction Costs: ₹{exec_stats['total_transaction_costs']:.2f}")
    print(f"   Avg Cost per Order: ₹{exec_stats['avg_transaction_cost_per_execution']:.2f}")
    
    # Trading statistics
    oms_stats = engine.oms.get_statistics()
    print(f"\n📊 TRADING STATISTICS:")
    print(f"   Completed Trades: {oms_stats['total_trades']}")
    print(f"   Win Rate: {oms_stats.get('win_rate', 0):.2%}")
    print(f"   Profit Factor: {oms_stats.get('profit_factor', 0):.2f}")
    
    if oms_stats.get('total_trades', 0) > 0:
        print(f"   Average Win: ₹{oms_stats.get('avg_win', 0):.2f}")
        print(f"   Average Loss: ₹{oms_stats.get('avg_loss', 0):.2f}")
    
    # Show sample trades
    if results.get('trades'):
        print(f"\n📋 SAMPLE TRADES (First 5):")
        for i, trade in enumerate(results['trades'][:5], 1):
            print(f"   {i}. {trade.side.value} {trade.symbol} | "
                  f"Entry: ₹{trade.entry_price:.2f} | Exit: ₹{trade.exit_price:.2f} | "
                  f"PnL: ₹{trade.net_pnl:.2f}")
    
    return results


if __name__ == "__main__":
    print("🚀 TESTING FIXED STRATEGIES")
    print("=" * 70)
    
    try:
        # Test individual strategies
        breakout_results = test_fixed_breakout_strategy()
        credit_results = test_fixed_credit_spread_strategy()
        
        # Test combined strategies
        combined_results = test_combined_strategies()
        
        print(f"\n🎉 ALL TESTS COMPLETED!")
        print("=" * 70)
        
        # Summary
        print(f"\n📊 SUMMARY:")
        print(f"   Breakout Trades: {breakout_results['summary']['total_trades']}")
        print(f"   Credit Spread Trades: {credit_results['summary']['total_trades']}")
        print(f"   Combined Trades: {combined_results['summary']['total_trades']}")
        print(f"   Combined Return: {combined_results['summary']['total_return']:.2%}")
        
        if combined_results['summary']['total_trades'] > 0:
            print(f"\n✅ SUCCESS: Strategies are now generating trades!")
        else:
            print(f"\n⚠️  No trades generated - may need further tuning")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
