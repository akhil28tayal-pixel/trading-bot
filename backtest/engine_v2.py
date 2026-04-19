"""
Event-Driven Backtesting Engine
Mimics live WebSocket-based trading system exactly
"""

import datetime as dt
import pandas as pd
import numpy as np
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import time

from .execution import BacktestExecutionEngine
from .oms import OrderManagementSystem
from .data import TickSimulator
from .metrics import PerformanceAnalyzer
from logger import log
import config


@dataclass
class BacktestConfig:
    """Backtesting configuration"""
    start_date: dt.datetime
    end_date: dt.datetime
    initial_capital: float = 100000
    enable_slippage: bool = True
    enable_delay: bool = True
    enable_costs: bool = True
    tick_frequency: str = "1min"  # How often to generate ticks
    market_open: dt.time = dt.time(9, 15)
    market_close: dt.time = dt.time(15, 30)
    
    # Risk management
    max_daily_loss: float = 0.03  # 3%
    max_positions: int = 10
    
    # Logging
    verbose: bool = True
    log_trades: bool = True


class BacktestEngine:
    """
    Event-driven backtesting engine that exactly mimics live trading
    """
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.current_time = config.start_date
        self.initial_capital = config.initial_capital
        self.current_capital = config.initial_capital
        
        # Core components
        self.oms = OrderManagementSystem()
        self.execution_engine = BacktestExecutionEngine(
            enable_slippage=config.enable_slippage,
            enable_delay=config.enable_delay,
            enable_costs=config.enable_costs
        )
        self.tick_simulator = TickSimulator()
        self.performance_analyzer = PerformanceAnalyzer(config.initial_capital)
        
        # Strategy callbacks
        self.strategy_callbacks: List[Callable] = []
        
        # Market data
        self.market_data: Dict[str, pd.DataFrame] = {}
        self.symbol_tokens: Dict[str, int] = {}
        self.current_prices: Dict[int, float] = {}  # token -> price
        
        # State tracking
        self.is_market_open = False
        self.daily_pnl = 0
        self.trade_count = 0
        self.equity_curve = []
        
        # Event queue for realistic timing
        self.event_queue = []
        
        log(f"Backtesting engine initialized: {config.start_date} to {config.end_date}")
    
    def add_market_data(self, symbol: str, data: pd.DataFrame, instrument_token: int):
        """
        Add market data for backtesting
        
        Args:
            symbol: Trading symbol (e.g., "NIFTY", "BANKNIFTY")
            data: OHLC data with datetime index
            instrument_token: Instrument token for tick generation
        """
        # Ensure data is properly indexed
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
        
        # Filter data to backtest period
        mask = (data.index >= self.config.start_date) & (data.index <= self.config.end_date)
        filtered_data = data[mask].copy()
        
        if filtered_data.empty:
            raise ValueError(f"No data found for {symbol} in backtest period")
        
        self.market_data[symbol] = filtered_data
        self.symbol_tokens[symbol] = instrument_token
        log(f"Added market data for {symbol}: {len(filtered_data)} bars")
    
    def add_strategy_callback(self, callback: Callable):
        """
        Add strategy callback function
        
        Args:
            callback: Function that processes ticks (same as live trading)
        """
        self.strategy_callbacks.append(callback)
        log(f"Added strategy callback: {callback.__name__}")
    
    def is_market_hours(self, timestamp: dt.datetime) -> bool:
        """Check if timestamp is within market hours"""
        time_only = timestamp.time()
        return self.config.market_open <= time_only <= self.config.market_close
    
    def update_current_time(self, new_time: dt.datetime):
        """Update current time and market status"""
        self.current_time = new_time
        
        # Check market status
        was_open = self.is_market_open
        self.is_market_open = self.is_market_hours(new_time)
        
        # Reset daily PnL at market open
        if self.is_market_open and not was_open:
            self.daily_pnl = 0
            log(f"Market opened at {new_time}")
        
        # Log market close
        if was_open and not self.is_market_open:
            log(f"Market closed at {new_time}. Daily PnL: ₹{self.daily_pnl:.2f}")
    
    def generate_ticks_for_timestamp(self, timestamp: dt.datetime) -> List[Dict]:
        """
        Generate realistic ticks for a given timestamp
        
        Returns:
            List of tick dictionaries matching WebSocket format
        """
        ticks = []
        
        for symbol, data in self.market_data.items():
            # Find the closest data point
            try:
                # Get the bar for this timestamp (or closest)
                if timestamp in data.index:
                    bar = data.loc[timestamp]
                else:
                    # Find closest bar
                    closest_idx = data.index.get_indexer([timestamp], method='ffill')[0]
                    if closest_idx == -1:
                        continue
                    bar = data.iloc[closest_idx]
                
                # Generate multiple ticks from OHLC
                tick_prices = self.tick_simulator.generate_ticks_from_ohlc(
                    open_price=bar['open'],
                    high_price=bar['high'],
                    low_price=bar['low'],
                    close_price=bar['close'],
                    num_ticks=5  # Generate 5 ticks per bar
                )
                
                # Convert to WebSocket tick format
                for price in tick_prices:
                    instrument_token = self.symbol_tokens.get(symbol)
                    if instrument_token is None:
                        continue
                    
                    tick = {
                        'instrument_token': instrument_token,
                        'last_price': price,
                        'timestamp': timestamp,
                        'volume': bar.get('volume', 0),
                        'oi': bar.get('oi', 0)
                    }
                    
                    ticks.append(tick)
                    self.current_prices[instrument_token] = price
                    
            except Exception as e:
                if self.config.verbose:
                    log(f"Error generating tick for {symbol} at {timestamp}: {e}")
                continue
        
        return ticks
    
    def process_tick_batch(self, ticks: List[Dict]):
        """
        Process a batch of ticks through all strategy callbacks
        Exactly mimics live WebSocket processing
        """
        if not ticks:
            return
        
        # Update execution engine with current time
        self.execution_engine.update_time(self.current_time)
        
        # Call each strategy callback with the tick batch
        for callback in self.strategy_callbacks:
            try:
                # This is the EXACT same call as in live trading
                callback(ticks)
            except Exception as e:
                log(f"Error in strategy callback {callback.__name__}: {e}")
    
    def check_risk_limits(self) -> bool:
        """Check if risk limits are breached"""
        # Daily loss limit
        if self.daily_pnl <= -self.initial_capital * self.config.max_daily_loss:
            log(f"Daily loss limit hit: ₹{self.daily_pnl:.2f}")
            return False
        
        # Max positions
        if len(self.oms.active_positions) >= self.config.max_positions:
            log(f"Max positions limit hit: {len(self.oms.active_positions)}")
            return False
        
        return True
    
    def update_equity(self):
        """Update equity curve"""
        # Calculate current equity
        unrealized_pnl = self.oms.get_unrealized_pnl(self.current_prices)
        current_equity = self.initial_capital + self.oms.realized_pnl + unrealized_pnl
        
        # Update capital
        self.current_capital = current_equity
        
        # Record equity point
        equity_point = {
            'timestamp': self.current_time,
            'equity': current_equity,
            'realized_pnl': self.oms.realized_pnl,
            'unrealized_pnl': unrealized_pnl,
            'daily_pnl': self.daily_pnl,
            'positions': len(self.oms.active_positions)
        }
        
        self.equity_curve.append(equity_point)
        self.performance_analyzer.add_equity_point(equity_point)
    
    def run(self) -> Dict[str, Any]:
        """
        Run the backtest
        
        Returns:
            Dictionary with backtest results
        """
        log("Starting backtest...")
        start_time = time.time()
        
        # Generate time series for the entire backtest period
        if not self.market_data:
            raise ValueError("No market data added. Use add_market_data() first.")
        
        # Get all unique timestamps from market data
        all_timestamps = set()
        for data in self.market_data.values():
            all_timestamps.update(data.index)
        
        # Sort timestamps
        timestamps = sorted(all_timestamps)
        timestamps = [ts for ts in timestamps if self.config.start_date <= ts <= self.config.end_date]
        
        log(f"Processing {len(timestamps)} timestamps...")
        
        # Main backtest loop
        for i, timestamp in enumerate(timestamps):
            self.update_current_time(timestamp)
            
            # Skip if market is closed
            if not self.is_market_open:
                continue
            
            # Check risk limits
            if not self.check_risk_limits():
                log("Risk limits breached. Stopping backtest.")
                break
            
            # Generate ticks for this timestamp
            ticks = self.generate_ticks_for_timestamp(timestamp)
            
            if ticks:
                # Process ticks through strategies (EXACT same as live)
                self.process_tick_batch(ticks)
                
                # Process any pending orders
                self.oms.process_pending_orders(self.current_prices, self.execution_engine)
                
                # Update daily PnL
                self.daily_pnl = self.oms.get_daily_pnl()
                
                # Update equity curve
                self.update_equity()
            
            # Progress logging
            if i % 1000 == 0 and self.config.verbose:
                progress = (i / len(timestamps)) * 100
                log(f"Progress: {progress:.1f}% - {timestamp} - Equity: ₹{self.current_capital:.2f}")
        
        # Finalize backtest
        execution_time = time.time() - start_time
        results = self.finalize_backtest(execution_time)
        
        log(f"Backtest completed in {execution_time:.2f} seconds")
        return results
    
    def finalize_backtest(self, execution_time: float) -> Dict[str, Any]:
        """Finalize backtest and generate results"""
        
        # Close any remaining positions at final prices
        self.oms.close_all_positions(self.current_prices, self.execution_engine)
        
        # Calculate final metrics
        final_equity = self.initial_capital + self.oms.realized_pnl
        total_return = (final_equity - self.initial_capital) / self.initial_capital
        
        # Generate comprehensive results
        results = {
            'summary': {
                'initial_capital': self.initial_capital,
                'final_capital': final_equity,
                'total_return': total_return,
                'total_pnl': self.oms.realized_pnl,
                'total_trades': len(self.oms.trade_history),
                'execution_time': execution_time
            },
            'trades': self.oms.trade_history,
            'equity_curve': self.equity_curve,
            'performance_metrics': self.performance_analyzer.calculate_metrics(),
            'positions': self.oms.position_history,
            'config': self.config
        }
        
        return results
    
    def get_current_price(self, instrument_token: int) -> Optional[float]:
        """Get current price for an instrument token"""
        return self.current_prices.get(instrument_token)

    def get_symbol_token(self, symbol: str) -> Optional[int]:
        """Resolve a tracked symbol to its instrument token."""
        return self.symbol_tokens.get(symbol)
    
    def place_backtest_order(self, symbol: str, side: str, quantity: int, 
                           instrument_token: int, order_type: str = "MARKET") -> Dict:
        """
        Place order in backtest (called by broker.py)
        
        This replaces the live order placement during backtesting
        """
        current_price = self.get_current_price(instrument_token)
        if current_price is None:
            return {"status": "FAILED", "error": "No current price available"}
        
        # Create order
        order = self.oms.create_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            price=current_price,
            timestamp=self.current_time,
            instrument_token=instrument_token
        )
        
        # Execute immediately for market orders
        if order_type == "MARKET":
            execution_result = self.execution_engine.execute_order(order, current_price)
            self.oms.process_execution(execution_result)
            
            return {
                "status": "EXECUTED",
                "order_id": order.order_id,
                "executed_price": execution_result.executed_price,
                "execution_details": execution_result
            }
        
        return {"status": "PLACED", "order_id": order.order_id}
