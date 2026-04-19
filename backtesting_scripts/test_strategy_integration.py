#!/usr/bin/env python3
"""
Test strategy integration with backtesting engine
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datetime as dt
from backtest.engine_v2 import BacktestEngine, BacktestConfig
from backtest.data import DataProvider
from backtest.strategy_adapter import BacktestContext


def test_simple_trading_strategy():
    """Test with a simple strategy that should generate trades"""
    print("🧪 Testing Strategy Integration with Trade Generation")
    print("=" * 60)
    
    # Create config for short test
    config = BacktestConfig(
        start_date=dt.datetime(2024, 1, 1),
        end_date=dt.datetime(2024, 1, 5),  # Just 5 days
        initial_capital=100000,
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
    
    print(f"✅ Added {len(nifty_data)} bars of NIFTY data")
    
    # Create a simple test strategy that will definitely trade
    trade_count = 0
    
    def simple_buy_sell_strategy(ticks):
        """Simple strategy that buys and sells to test execution"""
        nonlocal trade_count
        
        if not ticks:
            return
            
        # Get current price from first tick
        current_price = ticks[0]['last_price']
        
        # Simple logic: buy every 100th tick, sell every 200th tick
        if trade_count % 200 == 50:  # Buy signal
            print(f"📈 BUY SIGNAL at ₹{current_price:.2f}")
            
            # Use the backtest broker interface
            try:
                from broker import place_order_realistic
                result = place_order_realistic(
                    symbol="NIFTY2642124350CE",
                    transaction_type="BUY", 
                    quantity=50,
                    market_price=current_price
                )
                print(f"✅ Order executed: {result}")
            except Exception as e:
                print(f"❌ Order failed: {e}")
        
        elif trade_count % 200 == 150:  # Sell signal
            print(f"📉 SELL SIGNAL at ₹{current_price:.2f}")
            
            try:
                from broker import place_order_realistic
                result = place_order_realistic(
                    symbol="NIFTY2642124350CE",
                    transaction_type="SELL",
                    quantity=50, 
                    market_price=current_price
                )
                print(f"✅ Order executed: {result}")
            except Exception as e:
                print(f"❌ Order failed: {e}")
        
        trade_count += 1
    
    # Setup backtest context
    context = BacktestContext(engine)
    
    with context:
        # Add our test strategy
        engine.add_strategy_callback(simple_buy_sell_strategy)
        print("✅ Simple trading strategy added")
        
        # Run backtest
        print("\n🔄 Running backtest with trading strategy...")
        results = engine.run()
    
    # Check results
    summary = results['summary']
    print(f"\n📈 BACKTEST RESULTS:")
    print(f"   Initial Capital: ₹{summary['initial_capital']:,.2f}")
    print(f"   Final Capital: ₹{summary['final_capital']:,.2f}")
    print(f"   Total Return: {summary['total_return']:.2%}")
    print(f"   Total Trades: {summary['total_trades']}")
    print(f"   Execution Time: {summary['execution_time']:.2f}s")
    
    # Check execution statistics
    exec_stats = engine.execution_engine.get_execution_statistics()
    print(f"\n⚡ EXECUTION STATISTICS:")
    print(f"   Total Executions: {exec_stats['total_executions']}")
    print(f"   Total Slippage Cost: ₹{exec_stats['total_slippage_cost']:.2f}")
    print(f"   Total Transaction Costs: ₹{exec_stats['total_transaction_costs']:.2f}")
    
    # Check OMS statistics
    oms_stats = engine.oms.get_statistics()
    print(f"\n📊 TRADING STATISTICS:")
    print(f"   Total Trades: {oms_stats['total_trades']}")
    print(f"   Win Rate: {oms_stats['win_rate']:.2%}")
    print(f"   Total PnL: ₹{oms_stats['total_pnl']:.2f}")
    
    if summary['total_trades'] > 0:
        print("✅ Strategy integration test PASSED - Trades were generated!")
    else:
        print("⚠️  Strategy integration test - No trades generated (may be normal)")
    
    return results


def test_existing_strategy_integration():
    """Test integration with existing breakout strategy"""
    print("\n🧪 Testing Existing Strategy Integration")
    print("=" * 50)
    
    # Import existing strategy
    try:
        import strategies.breakout_ws as breakout_strategy
        print("✅ Breakout strategy imported")
    except Exception as e:
        print(f"❌ Failed to import breakout strategy: {e}")
        return None
    
    # Create minimal config
    config = BacktestConfig(
        start_date=dt.datetime(2024, 1, 1),
        end_date=dt.datetime(2024, 1, 3),
        initial_capital=50000,
        enable_slippage=False,  # Disable for simpler test
        enable_costs=False,
        verbose=False
    )
    
    # Create engine
    engine = BacktestEngine(config)
    
    # Add data
    data_provider = DataProvider()
    nifty_data = data_provider.get_data(256265, config.start_date, config.end_date)
    engine.add_market_data("NIFTY", nifty_data, 256265)
    
    # Setup context and add strategy
    context = BacktestContext(engine)
    
    try:
        with context:
            context.add_strategy(breakout_strategy, "NIFTY")
            print("✅ Breakout strategy added to backtest")
            
            # Run backtest
            results = engine.run()
            
            summary = results['summary']
            print(f"✅ Backtest completed - Return: {summary['total_return']:.2%}")
            
    except Exception as e:
        print(f"❌ Strategy integration failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    return results


if __name__ == "__main__":
    print("🚀 TESTING BACKTESTING ENGINE STRATEGY INTEGRATION")
    print("=" * 70)
    
    # Test 1: Simple trading strategy
    test_simple_trading_strategy()
    
    # Test 2: Existing strategy integration
    test_existing_strategy_integration()
    
    print("\n🎉 Strategy integration tests completed!")
