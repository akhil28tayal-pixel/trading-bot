#!/usr/bin/env python3
"""
Persistent production risk state used by deployment utilities.
"""

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, Tuple

import config


class ProductionRiskManager:
    """Manage daily production risk state on disk."""

    def __init__(self, state_file: str = "logs/risk_state.json"):
        self.state_path = Path(state_file)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.emergency_stop_path = Path(".emergency_stop")
        self.state = self._load_state()
        self._roll_state_if_needed()

    def _default_state(self, for_date: str | None = None) -> Dict[str, Any]:
        return {
            "date": for_date or dt.date.today().isoformat(),
            "daily_pnl": 0.0,
            "trade_count": 0,
            "consecutive_losses": 0,
            "max_drawdown": 0.0,
            "peak_pnl": 0.0,
            "last_updated": dt.datetime.now().isoformat(),
        }

    def _load_state(self) -> Dict[str, Any]:
        if not self.state_path.exists():
            state = self._default_state()
            self._save_state(state)
            return state

        try:
            with self.state_path.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if not isinstance(loaded, dict):
                raise ValueError("risk state must be a JSON object")
            return {**self._default_state(), **loaded}
        except Exception:
            state = self._default_state()
            self._save_state(state)
            return state

    def _save_state(self, state: Dict[str, Any]):
        state["last_updated"] = dt.datetime.now().isoformat()
        with self.state_path.open("w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)

    def _roll_state_if_needed(self):
        today = dt.date.today().isoformat()
        if self.state.get("date") != today:
            self.state = self._default_state(today)
            self._save_state(self.state)

    def is_trading_allowed(self) -> Tuple[bool, str]:
        self._roll_state_if_needed()

        if self.emergency_stop_path.exists():
            return False, "Emergency stop is active"

        daily_limit = config.CAPITAL * config.DAILY_LOSS_LIMIT
        if self.state["daily_pnl"] <= -daily_limit:
            return False, f"Daily loss limit reached (₹{daily_limit:.2f})"

        return True, "Trading allowed"

    def validate_trade(self, symbol: str, quantity: int, price: float, side: str) -> Tuple[bool, str]:
        allowed, reason = self.is_trading_allowed()
        if not allowed:
            return False, reason

        if symbol not in config.LOT_SIZE:
            return False, f"Unsupported symbol: {symbol}"

        lot_size = config.LOT_SIZE[symbol]
        if quantity <= 0:
            return False, "Quantity must be positive"
        if quantity % lot_size != 0:
            return False, f"Quantity must be a multiple of lot size {lot_size}"
        if price <= 0:
            return False, "Price must be positive"
        if side not in {"BUY", "SELL"}:
            return False, "Side must be BUY or SELL"

        position_value = quantity * price
        max_position_value = config.CAPITAL * 2
        if position_value > max_position_value:
            return False, f"Position value ₹{position_value:.2f} exceeds cap ₹{max_position_value:.2f}"

        return True, "Trade validated"

    def update_daily_pnl(self, pnl_delta: float):
        self._roll_state_if_needed()
        self.state["daily_pnl"] += pnl_delta
        self.state["trade_count"] += 1
        if pnl_delta < 0:
            self.state["consecutive_losses"] += 1
        else:
            self.state["consecutive_losses"] = 0
        self.state["peak_pnl"] = max(self.state["peak_pnl"], self.state["daily_pnl"])
        drawdown = self.state["peak_pnl"] - self.state["daily_pnl"]
        self.state["max_drawdown"] = max(self.state["max_drawdown"], drawdown)
        self._save_state(self.state)

    def get_daily_summary(self) -> Dict[str, Any]:
        self._roll_state_if_needed()
        return dict(self.state)


production_risk = ProductionRiskManager()
