#!/usr/bin/env python3
"""
Test script for the complete backtesting system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datetime as dt
from backtest.engine_v2 import BacktestEngine, BacktestConfig
from backtest.data import DataProvider
from backtest.strategy_adapter import BacktestContext


def test_basic_functionality():
    """Test basic backtesting functionality"""
    print("🧪 Testing Basic Backtesting Functionality")
    print("=" * 50)
    
    # Create minimal config
    config = BacktestConfig(
        start_date=dt.datetime(2024, 1, 1),
        end_date=dt.datetime(2024, 1, 3),  # Just 2 days
        initial_capital=10000,
        enable_slippage=True,
        enable_costs=True,
        verbose=False
    )
    
    print(f"✅ Config created: {config.start_date} to {config.end_date}")
    
    # Create engine
    engine = BacktestEngine(config)
    print("✅ BacktestEngine created")
    
    # Add test data
    data_provider = DataProvider()
    nifty_data = data_provider.get_data(256265, config.start_date, config.end_date)
    engine.add_market_data("NIFTY", nifty_data, 256265)
    
    print(f"✅ Added {len(nifty_data)} bars of NIFTY data")
    
    # Create a simple test strategy
    def simple_test_strategy(ticks):
        """Simple test strategy that just logs ticks"""
        if ticks:
            print(f"📊 Received {len(ticks)} ticks")
            for tick in ticks[:2]:  # Show first 2 ticks
                print(f"   Tick: {tick['instrument_token']} @ ₹{tick['last_price']:.2f}")
    
    engine.add_strategy_callback(simple_test_strategy)
    print("✅ Test strategy added")
    
    # Run backtest
    print("\n🔄 Running backtest...")
    results = engine.run()
    
    # Check results
    summary = results['summary']
    print(f"\n📈 Results:")
    print(f"   Initial Capital: ₹{summary['initial_capital']:,.2f}")
    print(f"   Final Capital: ₹{summary['final_capital']:,.2f}")
    print(f"   Total Return: {summary['total_return']:.2%}")
    print(f"   Execution Time: {summary['execution_time']:.2f}s")
    
    print("✅ Basic functionality test passed!")
    return True


def test_tick_generation():
    """Test tick generation from OHLC"""
    print("\n🧪 Testing Tick Generation")
    print("=" * 30)
    
    from backtest.data import TickSimulator
    
    tick_sim = TickSimulator()
    
    # Test OHLC to ticks
    ohlc = {'open': 100, 'high': 105, 'low': 95, 'close': 102}
    ticks = tick_sim.generate_ticks_from_ohlc(
        ohlc['open'], ohlc['high'], ohlc['low'], ohlc['close'], 10
    )
    
    print(f"✅ Generated {len(ticks)} ticks from OHLC")
    print(f"   OHLC: O={ohlc['open']}, H={ohlc['high']}, L={ohlc['low']}, C={ohlc['close']}")
    print(f"   Tick range: {min(ticks):.2f} - {max(ticks):.2f}")
    
    # Verify ticks hit OHLC points
    assert ohlc['open'] in ticks, "Open price not in ticks"
    assert ohlc['close'] in ticks, "Close price not in ticks"
    assert min(ticks) <= ohlc['low'], "Low not respected"
    assert max(ticks) >= ohlc['high'], "High not respected"
    
    print("✅ Tick generation test passed!")
    return True


def test_order_management():
    """Test order management system"""
    print("\n🧪 Testing Order Management")
    print("=" * 30)
    
    from backtest.oms import OrderManagementSystem
    from backtest.execution import BacktestExecutionEngine
    
    oms = OrderManagementSystem()
    execution_engine = BacktestExecutionEngine()
    
    # Create test order
    order = oms.create_order(
        symbol="TEST",
        side="BUY",
        quantity=50,
        order_type="MARKET",
        price=100.0,
        timestamp=dt.datetime.now(),
        instrument_token=123456
    )
    
    print(f"✅ Created order: {order.order_id}")
    
    # Execute order
    execution_result = execution_engine.execute_order(order, 100.0)
    oms.process_execution(execution_result)
    
    print(f"✅ Executed order at ₹{execution_result.executed_price:.2f}")
    print(f"   Slippage: {execution_result.slippage_bps:.1f}bps")
    print(f"   Costs: ₹{execution_result.costs:.2f}")
    
    # Check position
    assert len(oms.active_positions) == 1, "Position not created"
    position = list(oms.active_positions.values())[0]
    print(f"✅ Position created: {position.side.value} {position.quantity} @ ₹{position.entry_price:.2f}")
    
    print("✅ Order management test passed!")
    return True


def test_performance_metrics():
    """Test performance metrics calculation"""
    print("\n🧪 Testing Performance Metrics")
    print("=" * 30)
    
    from backtest.metrics import PerformanceAnalyzer
    
    analyzer = PerformanceAnalyzer(10000)
    
    # Add some sample equity points
    base_time = dt.datetime(2024, 1, 1)
    for i in range(10):
        equity_point = {
            'timestamp': base_time + dt.timedelta(days=i),
            'equity': 10000 + i * 100 + (i % 3 - 1) * 50,  # Some variation
            'realized_pnl': i * 50,
            'unrealized_pnl': (i % 3 - 1) * 50,
            'daily_pnl': 50,
            'positions': 1 if i % 2 == 0 else 0
        }
        analyzer.add_equity_point(equity_point)
    
    # Calculate metrics
    metrics = analyzer.calculate_metrics()
    
    print(f"✅ Calculated metrics:")
    print(f"   Total Return: {metrics.total_return:.2%}")
    print(f"   Volatility: {metrics.volatility:.2%}")
    print(f"   Max Drawdown: {metrics.max_drawdown:.2%}")
    
    print("✅ Performance metrics test passed!")
    return True


def run_all_tests():
    """Run all tests"""
    print("🚀 Running Complete Backtesting System Tests")
    print("=" * 60)
    
    tests = [
        test_tick_generation,
        test_order_management,
        test_performance_metrics,
        test_basic_functionality
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            failed += 1
    
    print(f"\n🎯 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Backtesting system is ready!")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return failed == 0


if __name__ == "__main__":
    run_all_tests()
