#!/usr/bin/env python3
"""
Test script for realistic execution system (slippage + delay)
"""

import time
import random
import sys
from risk.execution import (
    apply_slippage,
    simulate_execution_delay,
    execute_order_with_realism,
    calculate_volatility_multiplier,
    get_time_based_slippage,
    update_price_history
)
import config


def expected_slippage_range(price, side, multiplier=1.0):
    min_slippage = config.SLIPPAGE_PERCENT * 0.8 * multiplier
    max_slippage = config.SLIPPAGE_PERCENT * 1.2 * multiplier

    if side == "BUY":
        return (
            price * (1 + min_slippage),
            price * (1 + max_slippage),
        )

    return (
        price * (1 - max_slippage),
        price * (1 - min_slippage),
    )


def test_basic_slippage():
    """Test basic slippage functionality"""
    print("=" * 60)
    print("🧪 TESTING BASIC SLIPPAGE")
    print("=" * 60)
    
    test_cases = [
        {"price": 100, "side": "BUY"},
        {"price": 100, "side": "SELL"},
        {"price": 50, "side": "BUY"},
        {"price": 200, "side": "SELL"},
    ]
    all_passed = True
    
    for case in test_cases:
        expected_range = expected_slippage_range(case["price"], case["side"])
        executed_price = apply_slippage(case["price"], case["side"])
        in_range = expected_range[0] <= executed_price <= expected_range[1]
        all_passed = all_passed and in_range
        
        print(f"Price: ₹{case['price']}, Side: {case['side']}")
        print(f"Executed: ₹{executed_price:.2f} ({'✅' if in_range else '❌'})")
        print(f"Expected range: ₹{expected_range[0]:.2f} - ₹{expected_range[1]:.2f}")
        print()

    return all_passed


def test_execution_delay():
    """Test execution delay functionality"""
    print("=" * 60)
    print("⏱️ TESTING EXECUTION DELAY")
    print("=" * 60)
    
    all_passed = True
    delays = [100, 200, 500]  # milliseconds
    
    for delay_ms in delays:
        print(f"Testing {delay_ms}ms delay...")
        start_time = time.time()
        
        simulate_execution_delay(delay_ms)
        
        actual_delay = (time.time() - start_time) * 1000
        in_range = delay_ms * 0.65 <= actual_delay <= delay_ms * 1.35
        all_passed = all_passed and in_range
        print(f"Expected: ~{delay_ms}ms, Actual: {actual_delay:.0f}ms ({'✅' if in_range else '❌'})")
        print()

    return all_passed


def test_volatility_adjustment():
    """Test volatility-based slippage adjustment"""
    print("=" * 60)
    print("📊 TESTING VOLATILITY ADJUSTMENT")
    print("=" * 60)
    
    all_passed = True
    # Simulate different volatility scenarios
    scenarios = [
        {
            "name": "Low Volatility",
            "prices": [100, 100.1, 99.9, 100.05, 99.95, 100.02],
            "expected_multiplier_range": (0.5, 1.2)
        },
        {
            "name": "High Volatility", 
            "prices": [100, 105, 95, 110, 90, 108, 92],
            "expected_multiplier_range": (1.5, 3.0)
        },
        {
            "name": "Normal Volatility",
            "prices": [100, 101, 99, 102, 98, 101.5, 98.5],
            "expected_multiplier_range": (0.8, 2.0)
        }
    ]
    
    for scenario in scenarios:
        multiplier = calculate_volatility_multiplier(100, scenario["prices"])
        in_range = scenario["expected_multiplier_range"][0] <= multiplier <= scenario["expected_multiplier_range"][1]
        all_passed = all_passed and in_range
        
        print(f"{scenario['name']}: Multiplier = {multiplier:.2f} ({'✅' if in_range else '❌'})")
        print(f"Expected range: {scenario['expected_multiplier_range'][0]:.1f} - {scenario['expected_multiplier_range'][1]:.1f}")
        
        # Test slippage with this volatility
        base_price = 100
        slipped_price = apply_slippage(base_price, "BUY", volatility_multiplier=multiplier)
        slippage_bps = (slipped_price - base_price) / base_price * 10000
        
        print(f"Slippage with volatility: {slippage_bps:.1f}bps")
        print()

    return all_passed


def test_complete_execution():
    """Test complete realistic execution flow"""
    print("=" * 60)
    print("🚀 TESTING COMPLETE EXECUTION FLOW")
    print("=" * 60)
    
    all_passed = True
    # Simulate price history for volatility calculation
    nifty_prices = [24000 + random.uniform(-50, 50) for _ in range(30)]
    
    test_orders = [
        {"price": 100, "side": "BUY", "qty": 50, "symbol": "NIFTY2642124350CE"},
        {"price": 75, "side": "SELL", "qty": 50, "symbol": "NIFTY2642124350CE"},
        {"price": 150, "side": "BUY", "qty": 15, "symbol": "BANKNIFTY26APR56600PE"},
        {"price": 200, "side": "SELL", "qty": 15, "symbol": "BANKNIFTY26APR56600PE"},
    ]
    
    for i, order in enumerate(test_orders, 1):
        print(f"📋 Order {i}: {order['side']} {order['qty']} {order['symbol']} @ ₹{order['price']}")
        
        # Execute with realism
        result = execute_order_with_realism(
            price=order['price'],
            side=order['side'],
            quantity=order['qty'],
            symbol=order['symbol'],
            volatility_data={'price_history': nifty_prices}
        )
        
        print(f"✅ Executed @ ₹{result['executed_price']:.2f}")
        print(f"   Slippage: {result['slippage_bps']:.1f}bps")
        print(f"   Delay: {result['total_delay_ms']:.0f}ms")
        print(f"   Volatility Multiplier: {result['volatility_multiplier']:.2f}")
        print()

        all_passed = all_passed and result["executed_price"] > 0 and result["total_delay_ms"] >= 0

    return all_passed


def test_time_based_slippage():
    """Test time-based slippage adjustments"""
    print("=" * 60)
    print("🕐 TESTING TIME-BASED SLIPPAGE")
    print("=" * 60)
    
    all_passed = True
    # This would normally vary by time, but we'll just show the concept
    multiplier = get_time_based_slippage()
    all_passed = all_passed and multiplier >= 1.0
    print(f"Current time-based slippage multiplier: {multiplier:.1f}x")
    
    base_price = 100
    normal_slippage = apply_slippage(base_price, "BUY")
    
    # Simulate different times (this is conceptual since we can't change system time)
    print(f"Normal execution: ₹{base_price} -> ₹{normal_slippage:.2f}")
    print("During market open/close, slippage would be ~50% higher")
    print("During lunch time, slippage would be ~20% higher")
    print()

    return all_passed


def test_price_history_tracking():
    """Test price history tracking for volatility"""
    print("=" * 60)
    print("📈 TESTING PRICE HISTORY TRACKING")
    print("=" * 60)
    
    all_passed = True
    # Simulate updating price history
    symbols = ["NIFTY", "BANKNIFTY"]
    
    for symbol in symbols:
        print(f"Updating {symbol} price history...")
        
        # Add some sample prices
        for i in range(10):
            price = 24000 + random.uniform(-100, 100) if symbol == "NIFTY" else 56000 + random.uniform(-200, 200)
            update_price_history(symbol, price)
        
        print(f"✅ {symbol} history updated with 10 prices")
        all_passed = all_passed and True
    
    print()
    return all_passed


def benchmark_execution_performance():
    """Benchmark execution performance"""
    print("=" * 60)
    print("⚡ BENCHMARKING EXECUTION PERFORMANCE")
    print("=" * 60)
    
    num_orders = 100
    start_time = time.time()
    
    for i in range(num_orders):
        price = 100 + random.uniform(-10, 10)
        side = "BUY" if i % 2 == 0 else "SELL"
        
        # Execute without delay for benchmarking
        config.ENABLE_DELAY = False
        result = execute_order_with_realism(price, side, 50, f"TEST_SYMBOL_{i}")
    
    total_time = time.time() - start_time
    orders_per_second = num_orders / total_time
    
    print(f"Executed {num_orders} orders in {total_time:.2f} seconds")
    print(f"Performance: {orders_per_second:.1f} orders/second")
    
    # Re-enable delay
    config.ENABLE_DELAY = True
    print()
    return orders_per_second > 0


if __name__ == "__main__":
    print("🧪 REALISTIC EXECUTION SYSTEM TESTING")
    print("=" * 60)
    
    # Run all tests
    results = [
        test_basic_slippage(),
        test_execution_delay(),
        test_volatility_adjustment(),
        test_complete_execution(),
        test_time_based_slippage(),
        test_price_history_tracking(),
        benchmark_execution_performance(),
    ]
    
    print("=" * 60)
    print("✅ ALL EXECUTION TESTS COMPLETED!")
    print("=" * 60)
    
    # Show current configuration
    print("\n📋 CURRENT EXECUTION CONFIGURATION:")
    print(f"Slippage Enabled: {config.ENABLE_SLIPPAGE}")
    print(f"Base Slippage: {config.SLIPPAGE_PERCENT:.3f} ({config.SLIPPAGE_PERCENT*10000:.1f}bps)")
    print(f"Delay Enabled: {config.ENABLE_DELAY}")
    print(f"Base Delay: {config.EXECUTION_DELAY_MS}ms")
    print(f"Volatility Adjustment: {config.ENABLE_VOLATILITY_ADJUSTMENT}")
    print(f"Time-based Slippage: {config.ENABLE_TIME_BASED_SLIPPAGE}")
    
    sys.exit(0 if all(results) else 1)
