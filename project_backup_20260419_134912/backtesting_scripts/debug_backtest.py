#!/usr/bin/env python3
"""
Debug backtesting to understand why no trades are generated
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datetime as dt
from backtest.engine_v2 import BacktestEngine, BacktestConfig
from backtest.data import DataProvider
from backtest.strategy_adapter import BacktestContext


def debug_strategy_conditions():
    """Debug why strategies aren't generating trades"""
    
    print("🔍 DEBUGGING STRATEGY CONDITIONS")
    print("=" * 50)
    
    # Create short backtest
    config = BacktestConfig(
        start_date=dt.datetime(2024, 1, 1),
        end_date=dt.datetime(2024, 1, 3),  # Just 2 days
        initial_capital=100000,
        enable_slippage=False,  # Disable for debugging
        enable_costs=False,
        verbose=True
    )
    
    engine = BacktestEngine(config)
    
    # Add data
    data_provider = DataProvider()
    nifty_data = data_provider.get_data(256265, config.start_date, config.end_date)
    engine.add_market_data("NIFTY", nifty_data, 256265)
    
    print(f"✅ Added {len(nifty_data)} bars of NIFTY data")
    print(f"   Price range: ₹{nifty_data['close'].min():.2f} - ₹{nifty_data['close'].max():.2f}")
    
    # Create debug strategy to check conditions
    tick_count = 0
    orb_data = {"NIFTY": {"high": None, "low": None, "prices": []}}
    ema_data = {"NIFTY": []}
    
    def debug_breakout_strategy(ticks):
        """Debug version of breakout strategy"""
        nonlocal tick_count
        
        if not ticks:
            return
            
        tick_count += 1
        symbol = "NIFTY"
        
        # Get index price from tick
        index_price = None
        for tick in ticks:
            if tick['instrument_token'] == 256265:  # NIFTY token
                index_price = tick['last_price']
                break
        
        if index_price is None:
            return
        
        # Debug: Show first few ticks
        if tick_count <= 5:
            print(f"📊 Tick {tick_count}: NIFTY @ ₹{index_price:.2f}")
        
        # Calculate ORB (Opening Range Breakout) - first 15 minutes
        current_time = ticks[0].get('timestamp', dt.datetime.now())
        market_open = current_time.replace(hour=9, minute=15, second=0, microsecond=0)
        orb_end = market_open + dt.timedelta(minutes=15)
        
        if current_time <= orb_end:
            # Building ORB
            orb_data[symbol]["prices"].append(index_price)
            if orb_data[symbol]["high"] is None:
                orb_data[symbol]["high"] = index_price
                orb_data[symbol]["low"] = index_price
            else:
                orb_data[symbol]["high"] = max(orb_data[symbol]["high"], index_price)
                orb_data[symbol]["low"] = min(orb_data[symbol]["low"], index_price)
            
            if tick_count % 20 == 0:  # Log every 20 ticks during ORB
                print(f"🔄 Building ORB: High=₹{orb_data[symbol]['high']:.2f}, Low=₹{orb_data[symbol]['low']:.2f}")
            return
        
        # Calculate EMA
        ema_data[symbol].append(index_price)
        if len(ema_data[symbol]) > 20:
            ema_data[symbol] = ema_data[symbol][-20:]  # Keep last 20
        
        ema = sum(ema_data[symbol]) / len(ema_data[symbol])
        
        # Check breakout conditions
        orb_high = orb_data[symbol]["high"]
        orb_low = orb_data[symbol]["low"]
        
        if orb_high is None or orb_low is None:
            return
        
        # Debug conditions every 50 ticks
        if tick_count % 50 == 0:
            print(f"\n🔍 CONDITION CHECK (Tick {tick_count}):")
            print(f"   Current Price: ₹{index_price:.2f}")
            print(f"   ORB High: ₹{orb_high:.2f}")
            print(f"   ORB Low: ₹{orb_low:.2f}")
            print(f"   EMA: ₹{ema:.2f}")
            print(f"   Breakout threshold: ₹{orb_high * 1.001:.2f}")
            
            # Check conditions
            above_orb = index_price > orb_high * 1.001
            above_ema = index_price > ema
            
            print(f"   Above ORB threshold: {above_orb}")
            print(f"   Above EMA: {above_ema}")
            
            if above_orb and above_ema:
                print("   🚨 BREAKOUT CONDITIONS MET!")
                
                # Simulate option price (5% of underlying)
                ce_price = index_price * 0.05
                print(f"   Simulated CE price: ₹{ce_price:.2f}")
                
                # Try to place order
                try:
                    from broker import place_order_realistic
                    result = place_order_realistic(
                        symbol="NIFTY2642124350CE",
                        transaction_type="BUY",
                        quantity=50,
                        market_price=ce_price
                    )
                    print(f"   ✅ ORDER PLACED: {result}")
                except Exception as e:
                    print(f"   ❌ ORDER FAILED: {e}")
            else:
                print("   ⏳ Waiting for breakout...")
    
    # Run debug backtest
    context = BacktestContext(engine)
    
    with context:
        engine.add_strategy_callback(debug_breakout_strategy)
        print("\n🔄 Running debug backtest...")
        
        results = engine.run()
    
    # Show results
    summary = results['summary']
    print(f"\n📈 DEBUG RESULTS:")
    print(f"   Ticks Processed: {tick_count}")
    print(f"   Trades Generated: {summary['total_trades']}")
    print(f"   Final Capital: ₹{summary['final_capital']:,.2f}")
    
    return results


def debug_simple_trading_strategy():
    """Test with a guaranteed trading strategy"""
    
    print("\n🔍 TESTING SIMPLE GUARANTEED TRADING")
    print("=" * 50)
    
    config = BacktestConfig(
        start_date=dt.datetime(2024, 1, 1),
        end_date=dt.datetime(2024, 1, 2),
        initial_capital=50000,
        enable_slippage=True,
        enable_costs=True,
        verbose=False
    )
    
    engine = BacktestEngine(config)
    
    # Add data
    data_provider = DataProvider()
    nifty_data = data_provider.get_data(256265, config.start_date, config.end_date)
    engine.add_market_data("NIFTY", nifty_data, 256265)
    
    trade_count = 0
    
    def guaranteed_trading_strategy(ticks):
        """Strategy that will definitely trade"""
        nonlocal trade_count
        
        if not ticks:
            return
            
        trade_count += 1
        
        # Trade every 100 ticks
        if trade_count % 100 == 50:  # Buy
            current_price = ticks[0]['last_price']
            option_price = current_price * 0.04  # 4% of underlying
            
            print(f"📈 FORCED BUY at tick {trade_count}: Option ₹{option_price:.2f}")
            
            try:
                from broker import place_order_realistic
                result = place_order_realistic(
                    symbol="NIFTY2642124350CE",
                    transaction_type="BUY",
                    quantity=50,
                    market_price=option_price
                )
                print(f"   ✅ BUY executed: ₹{result['executed_price']:.2f}")
            except Exception as e:
                print(f"   ❌ BUY failed: {e}")
                
        elif trade_count % 100 == 80:  # Sell
            current_price = ticks[0]['last_price']
            option_price = current_price * 0.045  # 4.5% of underlying
            
            print(f"📉 FORCED SELL at tick {trade_count}: Option ₹{option_price:.2f}")
            
            try:
                from broker import place_order_realistic
                result = place_order_realistic(
                    symbol="NIFTY2642124350CE",
                    transaction_type="SELL",
                    quantity=50,
                    market_price=option_price
                )
                print(f"   ✅ SELL executed: ₹{result['executed_price']:.2f}")
            except Exception as e:
                print(f"   ❌ SELL failed: {e}")
    
    # Run guaranteed trading test
    context = BacktestContext(engine)
    
    with context:
        engine.add_strategy_callback(guaranteed_trading_strategy)
        results = engine.run()
    
    summary = results['summary']
    print(f"\n📈 GUARANTEED TRADING RESULTS:")
    print(f"   Ticks Processed: {trade_count}")
    print(f"   Trades Generated: {summary['total_trades']}")
    print(f"   Return: {summary['total_return']:.2%}")
    print(f"   Final Capital: ₹{summary['final_capital']:,.2f}")
    
    if summary['total_trades'] > 0:
        print("✅ Trading mechanism is working!")
    else:
        print("❌ Trading mechanism has issues")
    
    return results


if __name__ == "__main__":
    print("🔍 DEBUGGING WHY NO TRADES ARE GENERATED")
    print("=" * 60)
    
    # Test 1: Debug strategy conditions
    debug_strategy_conditions()
    
    # Test 2: Test with guaranteed trading
    debug_simple_trading_strategy()
    
    print("\n🎯 DEBUGGING COMPLETE")
    print("Check the output above to see why trades aren't being generated.")
