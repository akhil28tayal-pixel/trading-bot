from broker import place_order, place_order_realistic
from logger import log
from risk import update_pnl
from risk.position_sizing import calculate_qty
import config
import datetime as dt
from risk.costs import calculate_cost_adjusted_pnl, is_trade_viable, calculate_round_trip_cost

state = {"NIFTY": {"active": False}, "BANKNIFTY": {"active": False}}
orb_data = {"NIFTY": {"high": None, "low": None, "prices": []},
            "BANKNIFTY": {"high": None, "low": None, "prices": []}}
ema_data = {"NIFTY": [], "BANKNIFTY": []}

INDEX_TOKENS = {"NIFTY": 256265, "BANKNIFTY": 260105}
LOT_SIZE = {"NIFTY": 50, "BANKNIFTY": 15}
EMA_PERIOD = 20


def calculate_ema(prices):
    if len(prices) < EMA_PERIOD:
        return None
    multiplier = 2 / (EMA_PERIOD + 1)
    ema = prices[0]
    for p in prices[1:]:
        ema = (p - ema) * multiplier + ema
    return ema


def process_ticks(ticks, symbol, data=None):

    # Get current time from ticks or use system time
    if ticks and 'timestamp' in ticks[0]:
        now = ticks[0]['timestamp']
    else:
        now = dt.datetime.now()

    # time filter
    if now.hour < 9 or (now.hour == 9 and now.minute < 20):
        return
    if now.hour > 14 or (now.hour == 14 and now.minute > 30):
        return

    index_token = INDEX_TOKENS[symbol]

    index_price = None
    ce_price = None
    pe_price = None

    # Get index price from ticks
    for t in ticks:
        if t["instrument_token"] == index_token:
            index_price = t["last_price"]
            break

    if index_price is None:
        return
    
    # Calculate option prices if not provided in data
    if data and "ce_token" in data:
        # Live trading - get from ticks
        for t in ticks:
            if t["instrument_token"] == data["ce_token"]:
                ce_price = t["last_price"]
            elif t["instrument_token"] == data["pe_token"]:
                pe_price = t["last_price"]
    else:
        # Backtesting - calculate option prices
        if symbol == "NIFTY":
            atm_strike = round(index_price / 50) * 50
        else:  # BANKNIFTY
            atm_strike = round(index_price / 100) * 100
        
        # Simple option pricing for backtesting
        ce_intrinsic = max(index_price - atm_strike, 0)
        pe_intrinsic = max(atm_strike - index_price, 0)
        time_value = index_price * 0.02  # 2% time value
        
        ce_price = max(ce_intrinsic + time_value, index_price * 0.005)
        pe_price = max(pe_intrinsic + time_value, index_price * 0.005)
        
        # Create data structure for backtesting
        if data is None:
            data = {}
        data.update({
            "ce_symbol": f"{symbol}2642{int(atm_strike)}CE",
            "pe_symbol": f"{symbol}2642{int(atm_strike)}PE",
            "ce_token": index_token,  # Simplified for backtesting
            "pe_token": index_token,
            "strike": atm_strike
        })

    # ORB build - Enhanced for backtesting
    if now.hour == 9 and now.minute <= 30:
        orb_data[symbol]["prices"].append(index_price)
        return
    elif now.hour == 9 and now.minute == 31 and orb_data[symbol]["high"] is None:
        # ORB period just ended, calculate ORB
        prices = orb_data[symbol]["prices"]
        if prices:
            orb_data[symbol]["high"] = max(prices)
            orb_data[symbol]["low"] = min(prices)
            log(f"{symbol} ORB calculated → High: ₹{orb_data[symbol]['high']:.2f}, Low: ₹{orb_data[symbol]['low']:.2f}")
    
    # For backtesting: if no ORB data yet, build it from first few ticks
    if orb_data[symbol]["high"] is None:
        orb_data[symbol]["prices"].append(index_price)
        if len(orb_data[symbol]["prices"]) >= 30:  # Use first 30 ticks as ORB
            prices = orb_data[symbol]["prices"]
            orb_data[symbol]["high"] = max(prices)
            orb_data[symbol]["low"] = min(prices)
            log(f"{symbol} ORB built from ticks → High: ₹{orb_data[symbol]['high']:.2f}, Low: ₹{orb_data[symbol]['low']:.2f}")
        return

    # EMA
    ema_data[symbol].append(index_price)
    ema = calculate_ema(ema_data[symbol])
    if ema is None:
        return

    # ENTRY
    if not state[symbol]["active"]:

        qty = LOT_SIZE[symbol]

        # CALL - Reduced threshold for backtesting
        breakout_threshold = 1.0005  # 0.05% instead of 0.1%
        if index_price > orb_data[symbol]["high"] * breakout_threshold and index_price > ema and ce_price:
            entry = ce_price
            sl_price = entry * 0.7
            target_price = entry * 1.5

            qty = calculate_qty(config.CAPITAL, config.RISK_PER_TRADE,
                                entry, sl_price, LOT_SIZE[symbol])

            # Check trade viability before placing order
            expected_profit = (target_price - entry) * qty
            viability = is_trade_viable(expected_profit, entry, target_price, qty)
            
            if not viability['viable']:
                log(f"{symbol} CE trade skipped - not viable after costs. Cost ratio: {viability['cost_ratio']:.2%}")
                return

            # Execute order with realistic slippage and delay
            execution_result = place_order_realistic(data["ce_symbol"], "BUY", qty, ce_price)
            actual_entry = execution_result['executed_price']
            
            log(f"{symbol} CE trade viable - Expected net profit: ₹{viability['net_profit']:.2f}")
            log(f"Actual entry after slippage: ₹{actual_entry:.2f} (vs signal: ₹{entry:.2f})")

            state[symbol] = {
                "active": True,
                "entry": actual_entry,  # Use actual executed price
                "signal_entry": entry,  # Keep original signal price for analysis
                "symbol": data["ce_symbol"],
                "qty": qty,
                "remaining_qty": qty,
                "partial": False,
                "trail_sl": actual_entry * 0.7,  # Adjust SL based on actual entry
                "target": actual_entry * 1.5,
                "final": actual_entry * 2.5,
                "execution_details": execution_result
            }

        # PUT - Reduced threshold for backtesting  
        elif index_price < orb_data[symbol]["low"] * 0.9995 and index_price < ema and pe_price:
            entry = pe_price
            sl_price = entry * 0.7
            target_price = entry * 1.5

            qty = calculate_qty(config.CAPITAL, config.RISK_PER_TRADE,
                                entry, sl_price, LOT_SIZE[symbol])

            # Check trade viability before placing order
            expected_profit = (target_price - entry) * qty
            viability = is_trade_viable(expected_profit, entry, target_price, qty)
            
            if not viability['viable']:
                log(f"{symbol} PE trade skipped - not viable after costs. Cost ratio: {viability['cost_ratio']:.2%}")
                return

            # Execute order with realistic slippage and delay
            execution_result = place_order_realistic(data["pe_symbol"], "BUY", qty, pe_price)
            actual_entry = execution_result['executed_price']
            
            log(f"{symbol} PE trade viable - Expected net profit: ₹{viability['net_profit']:.2f}")
            log(f"Actual entry after slippage: ₹{actual_entry:.2f} (vs signal: ₹{entry:.2f})")

            state[symbol] = {
                "active": True,
                "entry": actual_entry,  # Use actual executed price
                "signal_entry": entry,  # Keep original signal price for analysis
                "symbol": data["pe_symbol"],
                "qty": qty,
                "remaining_qty": qty,
                "partial": False,
                "trail_sl": actual_entry * 0.7,  # Adjust SL based on actual entry
                "target": actual_entry * 1.5,
                "final": actual_entry * 2.5,
                "execution_details": execution_result
            }

    # EXIT
    if state[symbol]["active"]:
        s = state[symbol]
        price = ce_price if "CE" in s["symbol"] else pe_price
        if price is None:
            return

        # SL
        if price <= s["trail_sl"]:
            # Execute exit with realistic slippage and delay
            exit_result = place_order_realistic(s["symbol"], "SELL", s["remaining_qty"], price)
            actual_exit = exit_result['executed_price']
            
            # Calculate cost-adjusted PnL using actual executed prices
            pnl_data = calculate_cost_adjusted_pnl(s["entry"], actual_exit, s["remaining_qty"])
            update_pnl(pnl_data['net_pnl'])
            
            log(f"{symbol} SL HIT @ signal: ₹{price:.2f}, executed: ₹{actual_exit:.2f}")
            log(f"Gross PnL: ₹{pnl_data['gross_pnl']:.2f} | Costs: ₹{pnl_data['total_cost']:.2f} | Net PnL: ₹{pnl_data['net_pnl']:.2f}")
            log(f"Slippage impact: ₹{abs(actual_exit - price):.2f} ({exit_result['slippage_bps']:.1f}bps)")
            
            state[symbol]["active"] = False
            return

        # Partial
        if not s["partial"] and price >= s["target"]:
            half = s["qty"] // 2
            
            # Execute partial exit with realistic slippage and delay
            exit_result = place_order_realistic(s["symbol"], "SELL", half, price)
            actual_exit = exit_result['executed_price']
            
            # Calculate partial PnL with costs using actual executed prices
            pnl_data = calculate_cost_adjusted_pnl(s["entry"], actual_exit, half)
            update_pnl(pnl_data['net_pnl'])
            
            log(f"{symbol} PARTIAL TARGET @ signal: ₹{price:.2f}, executed: ₹{actual_exit:.2f}")
            log(f"Net PnL: ₹{pnl_data['net_pnl']:.2f} (50% position) | Slippage: {exit_result['slippage_bps']:.1f}bps")
            
            s["remaining_qty"] -= half
            s["partial"] = True
            s["trail_sl"] = s["entry"]

        # Trail
        if s["partial"]:
            s["trail_sl"] = max(s["trail_sl"], price * 0.8)

        # Final
        if price >= s["final"]:
            # Execute final exit with realistic slippage and delay
            exit_result = place_order_realistic(s["symbol"], "SELL", s["remaining_qty"], price)
            actual_exit = exit_result['executed_price']
            
            # Calculate final exit PnL with costs using actual executed prices
            pnl_data = calculate_cost_adjusted_pnl(s["entry"], actual_exit, s["remaining_qty"])
            update_pnl(pnl_data['net_pnl'])
            
            log(f"{symbol} FINAL TARGET @ signal: ₹{price:.2f}, executed: ₹{actual_exit:.2f}")
            log(f"Net PnL: ₹{pnl_data['net_pnl']:.2f} (remaining 50%) | Slippage: {exit_result['slippage_bps']:.1f}bps")
            
            state[symbol]["active"] = False