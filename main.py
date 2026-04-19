import datetime as dt
import os
import sys
import threading
import time

import config
from auth import get_kite
from logger import log
from notifier import send
from risk.risk import check_limit

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "websocket"))
from ws_client import start_websocket, stop_websocket

from strategies.breakout_ws import process_ticks as breakout_ws
from strategies.credit_spread_ws import process_ticks as spread_ws, start_spread
from utils.instruments import get_option_tokens, get_credit_spread
from broker import get_ltp


def build_live_state():
    """Resolve all live instruments needed by the bot."""
    bn_data = get_option_tokens("BANKNIFTY")
    nf_data = get_option_tokens("NIFTY")

    bn_spread = get_credit_spread("BANKNIFTY", direction="CALL")
    nf_spread = get_credit_spread("NIFTY", direction="CALL")

    return {
        "BANKNIFTY": {
            "breakout": bn_data,
            "spread": bn_spread,
        },
        "NIFTY": {
            "breakout": nf_data,
            "spread": nf_spread,
        },
    }


def start_initial_spreads(live_state):
    """Open the starting spreads once before the WebSocket monitoring loop."""
    for symbol, state in live_state.items():
        spread = state["spread"]
        sell_symbol = spread["sell_symbol"]
        buy_symbol = spread["buy_symbol"]

        start_spread(
            symbol,
            {
                "symbol": sell_symbol,
                "ltp": get_ltp(f"NFO:{sell_symbol}"),
                "strike": spread["sell_strike"],
            },
            {
                "symbol": buy_symbol,
                "ltp": get_ltp(f"NFO:{buy_symbol}"),
                "strike": spread["buy_strike"],
            },
        )


def build_subscription_tokens(live_state):
    tokens = {256265, 260105}

    for state in live_state.values():
        breakout = state["breakout"]
        spread = state["spread"]
        tokens.update(
            {
                int(breakout["ce_token"]),
                int(breakout["pe_token"]),
                int(spread["sell_token"]),
                int(spread["buy_token"]),
            }
        )

    return sorted(tokens)


def create_tick_handler(live_state, stop_event):
    def handle_ticks(ticks):
        if not check_limit():
            log("Daily loss limit hit. Stopping bot.")
            send("Bot stopped due to loss limit")
            stop_websocket()
            stop_event.set()
            return

        breakout_ws(ticks, "BANKNIFTY", live_state["BANKNIFTY"]["breakout"])
        breakout_ws(ticks, "NIFTY", live_state["NIFTY"]["breakout"])

        spread_ws(ticks, "BANKNIFTY", live_state["BANKNIFTY"]["spread"])
        spread_ws(ticks, "NIFTY", live_state["NIFTY"]["spread"])

    return handle_ticks


def run_live():
    log("Bot Started")
    log("Ensuring Kite session is available...")
    get_kite()

    live_state = build_live_state()
    start_initial_spreads(live_state)
    stop_event = threading.Event()

    tokens = build_subscription_tokens(live_state)
    log(f"Starting WebSocket with {len(tokens)} subscriptions")

    if not start_websocket(tokens, create_tick_handler(live_state, stop_event)):
        raise RuntimeError("WebSocket failed to start")

    while not stop_event.is_set():
        time.sleep(1)

    raise RuntimeError("Trading session stopped after hitting the risk limit")


def is_market_open():
    now = dt.datetime.now()
    if now.weekday() >= 5:
        return False
    return (
        (now.hour == 9 and now.minute >= 15)
        or (9 < now.hour < 15)
        or (now.hour == 15 and now.minute <= 30)
    )


def run_continuous():
    """Run bot continuously, trading only during market hours."""
    log("Starting continuous trading bot...")
    log("Mode: " + config.MODE)
    log("Bot will trade during market hours (9:15 AM - 3:30 PM, Mon-Fri)")

    while True:
        try:
            if is_market_open():
                if not hasattr(run_continuous, "trading_active"):
                    log("Market is OPEN - Starting trading session")
                    run_continuous.trading_active = True

                run_live()
                break

            if hasattr(run_continuous, "trading_active"):
                log("Market is CLOSED - Trading session ended")
                delattr(run_continuous, "trading_active")

            if dt.datetime.now().weekday() >= 5:
                next_check = 300
                log(f"Weekend - Next check in {next_check // 60} minutes")
            else:
                next_check = 60
                log(f"Market closed - Next check in {next_check} seconds")

            time.sleep(next_check)

        except KeyboardInterrupt:
            log("Bot stopped by user")
            break
        except Exception as e:
            log(f"Error in continuous loop: {e}")
            time.sleep(60)


if __name__ == "__main__":
    if config.MODE == "BACKTEST":
        from run_backtest import main as run_backtest_main

        run_backtest_main()
    else:
        run_continuous()
