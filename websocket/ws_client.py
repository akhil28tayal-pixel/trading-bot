#!/usr/bin/env python3
"""
WebSocket Client for Kite Connect
Handles real-time market data subscriptions.
"""

import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from kiteconnect import KiteTicker


kws = None
ticks_callback = None
subscribed_tokens = []


def on_ticks(ws, ticks):
    """Handle incoming ticks."""
    if ticks_callback:
        ticks_callback(ticks)


def on_connect(ws, response):
    """Handle connection and subscribe to tokens."""
    if not subscribed_tokens:
        print("WebSocket connected, but no tokens were provided")
        return

    ws.subscribe(subscribed_tokens)
    ws.set_mode(ws.MODE_LTP, subscribed_tokens)
    print(f"WebSocket connected successfully. Subscribed to {len(subscribed_tokens)} tokens")


def on_close(ws, code, reason):
    """Handle connection close."""
    print(f"WebSocket connection closed: {code} {reason}")


def start_websocket(tokens, callback):
    """Start WebSocket connection with the provided subscriptions."""
    global kws, ticks_callback, subscribed_tokens

    try:
        if not config.API_KEY:
            print("No API key available")
            return False
        if not getattr(config, "ACCESS_TOKEN", ""):
            print("No access token available")
            return False

        ticks_callback = callback
        subscribed_tokens = sorted({int(token) for token in tokens})
        kws = KiteTicker(config.API_KEY, config.ACCESS_TOKEN)

        kws.on_ticks = on_ticks
        kws.on_connect = on_connect
        kws.on_close = on_close

        # Run in a background thread so the main bot loop can stay responsive.
        kws.connect(threaded=True)

        for _ in range(50):
            if kws.is_connected():
                return True
            time.sleep(0.1)

        print("WebSocket connection timed out")
        return False

    except Exception as e:
        print(f"WebSocket error: {e}")
        return False


def stop_websocket():
    """Stop WebSocket connection."""
    global kws, subscribed_tokens
    if kws:
        kws.close()
        kws = None
    subscribed_tokens = []


if __name__ == "__main__":
    print("Testing WebSocket connection...")

    def test_callback(ticks):
        print(f"Received {len(ticks)} ticks")

    if start_websocket([256265], test_callback):
        print("WebSocket test successful")
        time.sleep(5)
        stop_websocket()
    else:
        print("WebSocket test failed")
