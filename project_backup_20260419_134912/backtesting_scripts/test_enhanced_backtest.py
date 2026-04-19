#!/usr/bin/env python3
"""
Test enhanced backtesting with proper strategy data
This should generate actual trades
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datetime as dt
from backtest.engine_v2 import BacktestEngine, BacktestConfig
from backtest.data import DataProvider
from backtest.strategy_adapter import BacktestContext


def create_working_breakout_strategy():
    """
    Create a working breakout strategy that will generate trades
    """
    
    # Strategy state
    state = {"NIFTY": {"active": False}, "BANKNIFTY": {"active": False}}
    LOT_SIZE = {"NIFTY": 50, "BANKNIFTY": 15}
    
    # ORB and EMA data
    orb_data = {
        "NIFTY": {"high": None, "low": None, "prices": [], "ready": False},
        "BANKNIFTY": {"high": None, "low": None, "prices": [], "ready": False}
    }
    ema_data = {"NIFTY": [], "BANKNIFTY": []}
    
    tick_count = 0
    
    def working_breakout_strategy(ticks):
        """Working breakout strategy with all required data"""
        nonlocal tick_count
        
        if not ticks:
            return
            
        tick_count += 1
        
        # Process each symbol
        for symbol in ["NIFTY", "BANKNIFTY"]:
            
            # Get index price
            token = 256265 if symbol == "NIFTY" else 260105
            index_price = None
            
            for tick in ticks:
                if tick['instrument_token'] == token:
                    index_price = tick['last_price']
                    break
            
            if index_price is None:
                continue
            
            # Build ORB data (first 50 ticks = opening range)
            if len(orb_data[symbol]["prices"]) < 50:
                orb_data[symbol]["prices"].append(index_price)
                
                if orb_data[symbol]["high"] is None:
                    orb_data[symbol]["high"] = index_price
                    orb_data[symbol]["low"] = index_price
                else:
                    orb_data[symbol]["high"] = max(orb_data[symbol]["high"], index_price)
                    orb_data[symbol]["low"] = min(orb_data[symbol]["low"], index_price)
                
                continue  # Still building ORB
            
            elif not orb_data[symbol]["ready"]:
                orb_data[symbol]["ready"] = True
                print(f"✅ {symbol} ORB ready: High=₹{orb_data[symbol]['high']:.2f}, Low=₹{orb_data[symbol]['low']:.2f}")
            
            # Build EMA data
            ema_data[symbol].append(index_price)
            if len(ema_data[symbol]) > 20:
                ema_data[symbol] = ema_data[symbol][-20:]  # Keep last 20
            
            if len(ema_data[symbol]) < 10:
                continue  # Need minimum EMA data
            
            ema = sum(ema_data[symbol]) / len(ema_data[symbol])
            
            # Calculate option prices (simplified)
            if symbol == "NIFTY":
                atm_strike = round(index_price / 50) * 50
            else:
                atm_strike = round(index_price / 100) * 100
            
            ce_price = max(index_price - atm_strike, 0) + index_price * 0.03
            pe_price = max(atm_strike - index_price, 0) + index_price * 0.03
            
            # Ensure minimum prices
            ce_price = max(ce_price, index_price * 0.01)
            pe_price = max(pe_price, index_price * 0.01)
            
            # ENTRY LOGIC
            if not state[symbol]["active"]:
                
                # CALL breakout (more sensitive thresholds)
                if (index_price > orb_data[symbol]["high"] * 1.0005 and  # 0.05% threshold
                    index_price > ema):
                    
                    print(f"🚨 {symbol} CALL BREAKOUT: ₹{index_price:.2f} > ORB ₹{orb_data[symbol]['high']:.2f}")
                    
                    try:
                        from broker import place_order_realistic
                        result = place_order_realistic(
                            symbol=f"{symbol}2642{int(atm_strike)}CE",
                            transaction_type="BUY",
                            quantity=LOT_SIZE[symbol],
                            market_price=ce_price
                        )
                        
                        state[symbol] = {
                            "active": True,
                            "entry": result['executed_price'],
                            "symbol": f"{symbol}2642{int(atm_strike)}CE",
                            "qty": LOT_SIZE[symbol],
                            "type": "CE",
                            "target": result['executed_price'] * 1.3,  # 30% target
                            "sl": result['executed_price'] * 0.8      # 20% SL
                        }
                        
                        print(f"✅ {symbol} CE opened @ ₹{result['executed_price']:.2f}")
                        
                    except Exception as e:
                        print(f"❌ {symbol} CE failed: {e}")
                
                # PUT breakout
                elif (index_price < orb_data[symbol]["low"] * 0.9995 and  # 0.05% threshold
                      index_price < ema):
                    
                    print(f"🚨 {symbol} PUT BREAKOUT: ₹{index_price:.2f} < ORB ₹{orb_data[symbol]['low']:.2f}")
                    
                    try:
                        from broker import place_order_realistic
                        result = place_order_realistic(
                            symbol=f"{symbol}2642{int(atm_strike)}PE",
                            transaction_type="BUY",
                            quantity=LOT_SIZE[symbol],
                            market_price=pe_price
                        )
                        
                        state[symbol] = {
                            "active": True,
                            "entry": result['executed_price'],
                            "symbol": f"{symbol}2642{int(atm_strike)}PE",
                            "qty": LOT_SIZE[symbol],
                            "type": "PE",
                            "target": result['executed_price'] * 1.3,
                            "sl": result['executed_price'] * 0.8
                        }
                        
                        print(f"✅ {symbol} PE opened @ ₹{result['executed_price']:.2f}")
                        
                    except Exception as e:
                        print(f"❌ {symbol} PE failed: {e}")
            
            # EXIT LOGIC
            elif state[symbol]["active"]:
                
                # Get current option price
                current_price = ce_price if state[symbol]["type"] == "CE" else pe_price
                
                # Check exit conditions
                if (current_price >= state[symbol]["target"] or 
                    current_price <= state[symbol]["sl"]):
                    
                    exit_reason = "TARGET" if current_price >= state[symbol]["target"] else "STOP LOSS"
                    
                    try:
                        from broker import place_order_realistic
                        result = place_order_realistic(
                            symbol=state[symbol]["symbol"],
                            transaction_type="SELL",
                            quantity=state[symbol]["qty"],
                            market_price=current_price
                        )
                        
                        pnl = (result['executed_price'] - state[symbol]["entry"]) * state[symbol]["qty"]
                        print(f"🔄 {symbol} {exit_reason}: ₹{result['executed_price']:.2f} | PnL: ₹{pnl:.2f}")
                        
                        state[symbol]["active"] = False
                        
                    except Exception as e:
                        print(f"❌ {symbol} exit failed: {e}")
    
    return working_breakout_strategy


def test_working_strategy():
    """Test the working strategy"""
    
    print("🧪 TESTING WORKING BREAKOUT STRATEGY")
    print("=" * 60)
    
    # Create config with more volatile data
    config = BacktestConfig(
        start_date=dt.datetime(2024, 1, 1),
        end_date=dt.datetime(2024, 1, 10),  # 10 days for more opportunities
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
    
    banknifty_data = data_provider.get_data(260105, config.start_date, config.end_date)
    engine.add_market_data("BANKNIFTY", banknifty_data, 260105)
    
    print(f"✅ NIFTY: {len(nifty_data)} bars (₹{nifty_data['close'].min():.0f} - ₹{nifty_data['close'].max():.0f})")
    print(f"✅ BANKNIFTY: {len(banknifty_data)} bars (₹{banknifty_data['close'].min():.0f} - ₹{banknifty_data['close'].max():.0f})")
    
    # Create and add strategy
    working_strategy = create_working_breakout_strategy()
    
    context = BacktestContext(engine)
    
    with context:
        engine.add_strategy_callback(working_strategy)
        print("✅ Working breakout strategy added")
        
        print("\n🔄 Running backtest...")
        results = engine.run()
    
    # Analyze results
    summary = results['summary']
    print(f"\n📈 WORKING STRATEGY RESULTS:")
    print(f"   Initial Capital: ₹{summary['initial_capital']:,.2f}")
    print(f"   Final Capital: ₹{summary['final_capital']:,.2f}")
    print(f"   Total Return: {summary['total_return']:.2%}")
    print(f"   Total Trades: {summary['total_trades']}")
    print(f"   Execution Time: {summary['execution_time']:.2f}s")
    
    # Execution analysis
    exec_stats = engine.execution_engine.get_execution_statistics()
    print(f"\n⚡ EXECUTION ANALYSIS:")
    print(f"   Total Orders: {exec_stats['total_executions']}")
    print(f"   Slippage Cost: ₹{exec_stats['total_slippage_cost']:.2f}")
    print(f"   Transaction Costs: ₹{exec_stats['total_transaction_costs']:.2f}")
    
    # Trading statistics
    oms_stats = engine.oms.get_statistics()
    print(f"\n📊 TRADING STATISTICS:")
    print(f"   Completed Trades: {oms_stats['total_trades']}")
    print(f"   Win Rate: {oms_stats.get('win_rate', 0):.2%}")
    print(f"   Profit Factor: {oms_stats.get('profit_factor', 0):.2f}")
    
    if summary['total_trades'] > 0:
        print(f"\n🎉 SUCCESS! Generated {summary['total_trades']} trades with {summary['total_return']:.2%} return")
        
        # Show trade details if available
        if results.get('trades'):
            print(f"\n📋 TRADE DETAILS:")
            for i, trade in enumerate(results['trades'][:5], 1):  # Show first 5 trades
                print(f"   Trade {i}: {trade.side.value} {trade.symbol} | "
                      f"Entry: ₹{trade.entry_price:.2f} | Exit: ₹{trade.exit_price:.2f} | "
                      f"PnL: ₹{trade.net_pnl:.2f}")
    else:
        print(f"\n⚠️  No trades generated. This could be due to:")
        print(f"   - Market conditions not meeting breakout criteria")
        print(f"   - ORB range too tight for breakouts")
        print(f"   - Strategy parameters too conservative")
    
    return results


if __name__ == "__main__":
    test_working_strategy()
