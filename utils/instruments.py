#!/usr/bin/env python3
"""
Instrument helpers for live trading.
Selects an ATM option pair for breakout trades and a simple defined-risk
credit spread for spread trading.
"""

import datetime as dt
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from auth import get_kite


UNDERLYING_CONFIG = {
    "NIFTY": {
        "index_quote": "NSE:NIFTY 50",
        "strike_step": 50,
        "spread_width": 50,
    },
    "BANKNIFTY": {
        "index_quote": "NSE:NIFTY BANK",
        "strike_step": 100,
        "spread_width": 100,
    },
}


_kite_client = None


def _get_kite_client():
    global _kite_client

    if not config.API_KEY:
        raise ValueError("KITE_API_KEY is not configured")
    if not config.API_SECRET:
        raise ValueError("KITE_API_SECRET is not configured")

    if _kite_client is None:
        _kite_client = get_kite()

    if _kite_client is None:
        raise ValueError("Kite client could not be initialized")

    return _kite_client


def _get_underlying_config(underlying):
    symbol = underlying.upper()
    if symbol not in UNDERLYING_CONFIG:
        raise ValueError(f"Unsupported underlying: {underlying}")
    return UNDERLYING_CONFIG[symbol]


def _round_to_strike(price, strike_step):
    return int(round(price / strike_step) * strike_step)


def _get_nearest_expiry(instruments):
    today = dt.date.today()
    expiries = sorted({instrument["expiry"] for instrument in instruments if instrument["expiry"] >= today})
    if not expiries:
        raise ValueError("No valid option expiry found")
    return expiries[0]


def _load_option_chain(underlying, expiry=None):
    kite = _get_kite_client()
    instruments = kite.instruments("NFO")
    filtered = [
        instrument
        for instrument in instruments
        if instrument.get("name") == underlying
        and instrument.get("instrument_type") in {"CE", "PE"}
    ]

    if not filtered:
        raise ValueError(f"No option instruments found for {underlying}")

    selected_expiry = expiry or _get_nearest_expiry(filtered)
    chain = [instrument for instrument in filtered if instrument["expiry"] == selected_expiry]

    if not chain:
        raise ValueError(f"No options found for {underlying} expiry {selected_expiry}")

    return chain, selected_expiry


def _get_index_ltp(underlying):
    kite = _get_kite_client()
    details = _get_underlying_config(underlying)
    quote_symbol = details["index_quote"]
    quote = kite.ltp(quote_symbol)
    return quote[quote_symbol]["last_price"]


def get_option_tokens(underlying, expiry=None, strike_count=5):
    """
    Return the selected ATM CE/PE pair for an underlying.

    The result matches what `main.py` and the breakout strategy expect.
    """
    symbol = underlying.upper()
    details = _get_underlying_config(symbol)
    option_chain, selected_expiry = _load_option_chain(symbol, expiry)
    index_ltp = _get_index_ltp(symbol)
    atm_strike = _round_to_strike(index_ltp, details["strike_step"])

    strikes = sorted({instrument["strike"] for instrument in option_chain})
    nearest_strikes = sorted(
        strikes,
        key=lambda strike: (abs(strike - atm_strike), strike),
    )[: max(strike_count, 1)]

    candidate_chain = [instrument for instrument in option_chain if instrument["strike"] in nearest_strikes]
    ce_candidates = [instrument for instrument in candidate_chain if instrument["instrument_type"] == "CE"]
    pe_candidates = [instrument for instrument in candidate_chain if instrument["instrument_type"] == "PE"]

    if not ce_candidates or not pe_candidates:
        raise ValueError(f"Incomplete ATM option pair for {symbol} expiry {selected_expiry}")

    ce = min(ce_candidates, key=lambda instrument: abs(instrument["strike"] - atm_strike))
    pe = min(pe_candidates, key=lambda instrument: abs(instrument["strike"] - atm_strike))

    return {
        "underlying": symbol,
        "expiry": selected_expiry,
        "spot_price": index_ltp,
        "strike": atm_strike,
        "ce_symbol": ce["tradingsymbol"],
        "pe_symbol": pe["tradingsymbol"],
        "ce_token": int(ce["instrument_token"]),
        "pe_token": int(pe["instrument_token"]),
    }


def get_credit_spread(underlying, expiry=None, direction="CALL", spread_width=None):
    """
    Return a single live credit spread definition.
    """
    symbol = underlying.upper()
    spread_direction = direction.upper()
    details = _get_underlying_config(symbol)
    option_chain, selected_expiry = _load_option_chain(symbol, expiry)
    index_ltp = _get_index_ltp(symbol)
    atm_strike = _round_to_strike(index_ltp, details["strike_step"])
    width = spread_width or details["spread_width"]

    option_type = "CE" if spread_direction == "CALL" else "PE"
    option_lookup = {
        (instrument["strike"], instrument["instrument_type"]): instrument
        for instrument in option_chain
    }

    if spread_direction == "CALL":
        sell_strike = atm_strike + details["strike_step"]
        buy_strike = sell_strike + width
    elif spread_direction == "PUT":
        sell_strike = atm_strike - details["strike_step"]
        buy_strike = sell_strike - width
    else:
        raise ValueError(f"Unsupported spread direction: {direction}")

    sell_leg = option_lookup.get((sell_strike, option_type))
    buy_leg = option_lookup.get((buy_strike, option_type))

    if not sell_leg or not buy_leg:
        raise ValueError(
            f"Could not build {spread_direction} spread for {symbol} expiry {selected_expiry} "
            f"using strikes {sell_strike}/{buy_strike}"
        )

    return {
        "underlying": symbol,
        "expiry": selected_expiry,
        "direction": spread_direction,
        "sell_symbol": sell_leg["tradingsymbol"],
        "buy_symbol": buy_leg["tradingsymbol"],
        "sell_token": int(sell_leg["instrument_token"]),
        "buy_token": int(buy_leg["instrument_token"]),
        "sell_strike": sell_strike,
        "buy_strike": buy_strike,
    }


def get_ltp(symbol):
    """Get last traded price for a fully qualified quote symbol."""
    kite = _get_kite_client()
    quote = kite.ltp(symbol)
    return quote[symbol]["last_price"]


if __name__ == "__main__":
    print("Testing instruments utility...")
    option_data = get_option_tokens("NIFTY")
    print(f"Selected ATM pair: {option_data}")

    spread = get_credit_spread("NIFTY", direction="CALL")
    print(f"Selected spread: {spread}")
