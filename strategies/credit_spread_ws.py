from broker import place_order, place_order_realistic
from logger import log
from risk import update_pnl
from risk.position_sizing import calculate_spread_qty
from risk.costs import calculate_spread_cost, is_trade_viable
import config
import datetime as dt

state = {"NIFTY": {"active": False}, "BANKNIFTY": {"active": False}}

LOT_SIZE = {"NIFTY": 50, "BANKNIFTY": 15}
INDEX_TOKENS = {"NIFTY": 256265, "BANKNIFTY": 260105}


def _is_live_spread_payload(data):
    """Return True when data matches the single-spread live payload from main.py."""
    return bool(
        data
        and all(
            key in data
            for key in ["sell_symbol", "buy_symbol", "sell_token", "buy_token", "sell_strike", "buy_strike"]
        )
    )


def _select_spread_payload(data, now, active_state):
    """
    Normalize spread payloads across live and backtest modes.

    Live mode passes a single spread dict from main.py.
    Backtests may still pass a dict containing spread_call/spread_put variants.
    """
    if _is_live_spread_payload(data):
        return data, data

    if data:
        spread_direction = "CALL" if now.hour < 12 else "PUT"
        spread_payload = data.get("spread_call") if spread_direction == "CALL" else data.get("spread_put")
        active_payload = data.get("spread_call") if active_state and "CE" in active_state.get("sell_symbol", "") else data.get("spread_put")
        return spread_payload, active_payload

    return None, None


def calculate_option_price(underlying_price, strike, option_type, dte=7):
    """Simple option pricing for backtesting"""
    if option_type.upper() == "CE":
        intrinsic = max(underlying_price - strike, 0)
    else:  # PE
        intrinsic = max(strike - underlying_price, 0)
    
    # Time value based on moneyness and DTE
    moneyness = underlying_price / strike
    time_value = underlying_price * 0.01 * (dte / 30)  # 1% per month
    
    # Adjust time value based on moneyness
    if option_type.upper() == "CE":
        if moneyness > 1.02:  # ITM
            time_value *= 0.8
        elif moneyness < 0.98:  # OTM
            time_value *= 0.4
    else:  # PE
        if moneyness < 0.98:  # ITM
            time_value *= 0.8
        elif moneyness > 1.02:  # OTM
            time_value *= 0.4
    
    return max(intrinsic + time_value, underlying_price * 0.002)


def get_spread_data(symbol, index_price, spread_type="CALL"):
    """Generate spread data for backtesting"""
    if symbol == "NIFTY":
        base_strike = round(index_price / 50) * 50
        strike_gap = 50
    else:  # BANKNIFTY
        base_strike = round(index_price / 100) * 100
        strike_gap = 100
    
    if spread_type == "CALL":
        # Call credit spread: Sell lower strike, Buy higher strike
        sell_strike = base_strike + strike_gap
        buy_strike = base_strike + (2 * strike_gap)
        option_type = "CE"
    else:  # PUT
        # Put credit spread: Sell higher strike, Buy lower strike
        sell_strike = base_strike - strike_gap
        buy_strike = base_strike - (2 * strike_gap)
        option_type = "PE"
    
    sell_price = calculate_option_price(index_price, sell_strike, option_type)
    buy_price = calculate_option_price(index_price, buy_strike, option_type)
    
    sell_data = {
        "symbol": f"{symbol}2642{int(sell_strike)}{option_type}",
        "strike": sell_strike,
        "ltp": sell_price
    }
    
    buy_data = {
        "symbol": f"{symbol}2642{int(buy_strike)}{option_type}",
        "strike": buy_strike,
        "ltp": buy_price
    }
    
    return sell_data, buy_data


def process_ticks(ticks, symbol, data=None):
    """Process ticks for credit spread strategy"""
    
    # Get current time from ticks or use system time
    if ticks and 'timestamp' in ticks[0]:
        now = ticks[0]['timestamp']
    else:
        now = dt.datetime.now()

    # Time filter - only trade during specific hours
    if now.hour < 10 or now.hour > 14:
        return
    
    # Get index price
    index_token = INDEX_TOKENS[symbol]
    index_price = None
    
    for t in ticks:
        if t["instrument_token"] == index_token:
            index_price = t["last_price"]
            break
    
    if index_price is None:
        return
    
    real_sell_ltp = None
    real_buy_ltp = None
    spread_payload, active_payload = _select_spread_payload(data, now, state[symbol])

    if state[symbol]["active"] and active_payload:
        for t in ticks:
            if t["instrument_token"] == active_payload["sell_token"]:
                real_sell_ltp = t["last_price"]
            elif t["instrument_token"] == active_payload["buy_token"]:
                real_buy_ltp = t["last_price"]

    # Check if we should enter a spread
    if not state[symbol]["active"]:
        
        # Simple spread entry logic: Enter when index is near round numbers
        if symbol == "NIFTY":
            near_round = (index_price % 100) < 25 or (index_price % 100) > 75
        else:  # BANKNIFTY
            near_round = (index_price % 200) < 50 or (index_price % 200) > 150
        
        if near_round:
            spread_type = "CALL" if now.hour < 12 else "PUT"

            if spread_payload:
                sell_data = {
                    "symbol": spread_payload["sell_symbol"],
                    "strike": spread_payload["sell_strike"],
                    "ltp": next((t["last_price"] for t in ticks if t["instrument_token"] == spread_payload["sell_token"]), None),
                }
                buy_data = {
                    "symbol": spread_payload["buy_symbol"],
                    "strike": spread_payload["buy_strike"],
                    "ltp": next((t["last_price"] for t in ticks if t["instrument_token"] == spread_payload["buy_token"]), None),
                }
                if sell_data["ltp"] is None or buy_data["ltp"] is None:
                    return
            else:
                sell_data, buy_data = get_spread_data(symbol, index_price, spread_type)
            
            # Start the spread
            start_spread(symbol, sell_data, buy_data)
    
    else:
        # Check exit conditions
        if real_sell_ltp is not None and real_buy_ltp is not None:
            process_spread_ticks(ticks, symbol, {
                "sell_ltp": real_sell_ltp,
                "buy_ltp": real_buy_ltp
            })
        else:
            current_sell_data, current_buy_data = get_spread_data(
                symbol, index_price,
                "CALL" if "CE" in state[symbol]["sell_symbol"] else "PUT"
            )

            process_spread_ticks(ticks, symbol, {
                "sell_ltp": current_sell_data["ltp"],
                "buy_ltp": current_buy_data["ltp"]
            })


def start_spread(symbol, sell_data, buy_data):

    if state[symbol]["active"]:
        return

    sell_price = sell_data["ltp"]
    buy_price = buy_data["ltp"]

    strike_diff = abs(sell_data["strike"] - buy_data["strike"])

    qty = calculate_spread_qty(
        config.CAPITAL,
        config.RISK_PER_TRADE,
        sell_price,
        buy_price,
        strike_diff,
        LOT_SIZE[symbol]
    )

    # Check spread viability before placing orders
    net_premium = sell_price - buy_price
    expected_profit = net_premium * qty * 0.5  # Expect to capture 50% of premium
    
    # Use average price for cost calculation
    avg_price = (sell_price + buy_price) / 2
    viability = is_trade_viable(expected_profit, avg_price, avg_price * 0.8, qty)
    
    if not viability['viable']:
        log(f"{symbol} spread skipped - not viable after costs. Cost ratio: {viability['cost_ratio']:.2%}")
        return

    # Execute spread orders with realistic slippage and delay
    sell_result = place_order_realistic(sell_data["symbol"], "SELL", qty, sell_price)
    buy_result = place_order_realistic(buy_data["symbol"], "BUY", qty, buy_price)
    
    actual_sell_price = sell_result['executed_price']
    actual_buy_price = buy_result['executed_price']
    
    # Calculate entry costs
    entry_cost = calculate_spread_cost(actual_sell_price, actual_buy_price, qty)
    
    log(f"{symbol} spread viable - Expected net profit: ₹{viability['net_profit']:.2f} | Entry cost: ₹{entry_cost:.2f}")
    log(f"Actual spread prices: SELL ₹{actual_sell_price:.2f} (vs ₹{sell_price:.2f}), BUY ₹{actual_buy_price:.2f} (vs ₹{buy_price:.2f})")
    log(f"Entry slippage: SELL {sell_result['slippage_bps']:.1f}bps, BUY {buy_result['slippage_bps']:.1f}bps")

    state[symbol] = {
        "active": True,
        "sell_price": actual_sell_price,  # Use actual executed prices
        "buy_price": actual_buy_price,
        "signal_sell_price": sell_price,  # Keep original signal prices
        "signal_buy_price": buy_price,
        "sell_symbol": sell_data["symbol"],
        "buy_symbol": buy_data["symbol"],
        "qty": qty,
        "entry_cost": entry_cost,
        "sell_execution": sell_result,
        "buy_execution": buy_result
    }

    log(f"{symbol} {sell_data['symbol'][-2:]} spread started: Net premium ₹{net_premium:.2f}")


def process_spread_ticks(ticks, symbol, data):
    """Process ticks for active spread positions"""

    if not state[symbol]["active"]:
        return

    sell_ltp = data.get("sell_ltp")
    buy_ltp = data.get("buy_ltp")

    if sell_ltp is None or buy_ltp is None:
        return

    entry_spread = state[symbol]["sell_price"] - state[symbol]["buy_price"]
    current_spread = sell_ltp - buy_ltp

    # SL - Exit if spread widens (loss)
    if current_spread > entry_spread * 1.5:
        log(f"{symbol} spread SL hit: Current {current_spread:.2f} > Entry {entry_spread:.2f} * 1.5")
        exit_spread(symbol, sell_ltp, buy_ltp)

    # Target - Exit if spread narrows (profit)
    elif current_spread < entry_spread * 0.5:
        log(f"{symbol} spread target hit: Current {current_spread:.2f} < Entry {entry_spread:.2f} * 0.5")
        exit_spread(symbol, sell_ltp, buy_ltp)


def exit_spread(symbol, sell_ltp, buy_ltp):

    s = state[symbol]

    # Execute spread exit orders with realistic slippage and delay
    # Note: We BUY back what we sold, SELL what we bought
    buy_back_result = place_order_realistic(s["sell_symbol"], "BUY", s["qty"], sell_ltp)
    sell_back_result = place_order_realistic(s["buy_symbol"], "SELL", s["qty"], buy_ltp)
    
    actual_buy_back_price = buy_back_result['executed_price']
    actual_sell_back_price = sell_back_result['executed_price']

    # Calculate gross PnL using actual executed prices
    entry_spread = s["sell_price"] - s["buy_price"]
    exit_spread_val = actual_buy_back_price - actual_sell_back_price
    gross_pnl = (entry_spread - exit_spread_val) * s["qty"]
    
    # Calculate exit costs using actual executed prices
    exit_cost = calculate_spread_cost(actual_buy_back_price, actual_sell_back_price, s["qty"])
    
    # Total costs (entry + exit)
    total_cost = s["entry_cost"] + exit_cost
    
    # Net PnL after all costs
    net_pnl = gross_pnl - total_cost
    
    update_pnl(net_pnl)
    
    log(f"{symbol} SPREAD EXIT | Gross PnL: ₹{gross_pnl:.2f} | Total Costs: ₹{total_cost:.2f} | Net PnL: ₹{net_pnl:.2f}")
    log(f"Entry spread: {entry_spread:.2f}, Exit spread: {exit_spread_val:.2f}")
    log(f"Exit slippage: BUY-BACK {buy_back_result['slippage_bps']:.1f}bps, SELL-BACK {sell_back_result['slippage_bps']:.1f}bps")
    log(f"Signal vs Executed: BUY-BACK ₹{sell_ltp:.2f} -> ₹{actual_buy_back_price:.2f}, SELL-BACK ₹{buy_ltp:.2f} -> ₹{actual_sell_back_price:.2f}")

    state[symbol]["active"] = False
