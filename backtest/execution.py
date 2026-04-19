"""
Backtesting Execution Engine
Simulates realistic order execution with slippage, delays, and costs
"""

import datetime as dt
import time
from typing import Dict, Any
from .oms import Order, ExecutionResult
from risk.execution import apply_slippage, simulate_execution_delay
from risk.costs import calculate_round_trip_cost, calculate_single_order_cost
from logger import log
import config


class BacktestExecutionEngine:
    """
    Execution engine that simulates realistic order execution in backtesting
    Uses the same slippage and cost models as live trading
    """
    
    def __init__(self, enable_slippage: bool = True, enable_delay: bool = True, 
                 enable_costs: bool = True):
        self.enable_slippage = enable_slippage
        self.enable_delay = enable_delay
        self.enable_costs = enable_costs
        self.current_time = dt.datetime.now()
        
        # Execution statistics
        self.total_executions = 0
        self.total_slippage_cost = 0.0
        self.total_transaction_costs = 0.0
        
        log(f"Backtest execution engine initialized - Slippage: {enable_slippage}, "
            f"Delay: {enable_delay}, Costs: {enable_costs}")
    
    def update_time(self, current_time: dt.datetime):
        """Update current time for time-sensitive calculations"""
        self.current_time = current_time
    
    def execute_order(self, order: Order, market_price: float) -> ExecutionResult:
        """
        Execute an order with realistic simulation
        
        Args:
            order: Order to execute
            market_price: Current market price
            
        Returns:
            ExecutionResult with execution details
        """
        execution_start = time.time()
        
        # Simulate execution delay (but don't actually wait in backtest)
        delay_ms = 0
        if self.enable_delay:
            # Calculate what the delay would be, but don't actually wait
            base_delay = config.EXECUTION_DELAY_MS if hasattr(config, 'EXECUTION_DELAY_MS') else 200
            delay_ms = base_delay * (0.7 + 0.6 * time.time() % 1)  # Simulate random variation
        
        # Apply slippage
        executed_price = market_price
        slippage_bps = 0.0
        
        if self.enable_slippage:
            # Use the same slippage model as live trading
            executed_price = apply_slippage(
                price=market_price,
                side=order.side.value,
                slippage_percent=getattr(config, 'SLIPPAGE_PERCENT', 0.003)
            )
            slippage_bps = abs(executed_price - market_price) / market_price * 10000
            self.total_slippage_cost += abs(executed_price - market_price) * order.quantity
        
        # Calculate transaction costs
        costs = 0.0
        if self.enable_costs:
            cost_breakdown = calculate_single_order_cost(
                price=executed_price,
                qty=order.quantity,
                transaction_type=order.side.value
            )
            costs = cost_breakdown['total']
            self.total_transaction_costs += costs
        
        # Create execution result
        execution_result = ExecutionResult(
            order_id=order.order_id,
            executed_price=executed_price,
            executed_quantity=order.quantity,
            execution_timestamp=self.current_time,
            slippage_bps=slippage_bps,
            costs=costs,
            execution_details={
                'market_price': market_price,
                'slippage_amount': abs(executed_price - market_price),
                'delay_ms': delay_ms,
                'cost_breakdown': cost_breakdown if self.enable_costs else {},
                'execution_time_ms': (time.time() - execution_start) * 1000
            }
        )
        
        self.total_executions += 1
        
        # Log execution (similar to live trading)
        log(f"BACKTEST EXECUTION: {order.side.value} {order.quantity} {order.symbol} "
            f"@ ₹{executed_price:.2f} (Market: ₹{market_price:.2f}, "
            f"Slippage: {slippage_bps:.1f}bps, Costs: ₹{costs:.2f})")
        
        return execution_result
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get execution statistics for analysis"""
        avg_slippage_cost = (self.total_slippage_cost / self.total_executions 
                           if self.total_executions > 0 else 0)
        avg_transaction_cost = (self.total_transaction_costs / self.total_executions 
                              if self.total_executions > 0 else 0)
        
        return {
            'total_executions': self.total_executions,
            'total_slippage_cost': self.total_slippage_cost,
            'total_transaction_costs': self.total_transaction_costs,
            'avg_slippage_cost_per_execution': avg_slippage_cost,
            'avg_transaction_cost_per_execution': avg_transaction_cost,
            'settings': {
                'slippage_enabled': self.enable_slippage,
                'delay_enabled': self.enable_delay,
                'costs_enabled': self.enable_costs
            }
        }


class BacktestBrokerInterface:
    """
    Broker interface for backtesting that replaces live broker calls
    This gets injected into the strategy code during backtesting
    """
    
    def __init__(self, backtest_engine):
        self.backtest_engine = backtest_engine
        self.execution_engine = backtest_engine.execution_engine
        self.oms = backtest_engine.oms
        
    def place_order(self, symbol: str, transaction_type: str, quantity: int, 
                   market_price: float = None) -> Dict[str, Any]:
        """
        Place order in backtest (replaces live broker.place_order)
        
        Args:
            symbol: Trading symbol
            transaction_type: "BUY" or "SELL"
            quantity: Order quantity
            market_price: Current market price
            
        Returns:
            Order execution result
        """
        # Get current price if not provided
        if market_price is None:
            # Try to get from current prices
            instrument_token = self._get_instrument_token(symbol)
            market_price = self.backtest_engine.get_current_price(instrument_token)
            
            if market_price is None:
                return {"status": "FAILED", "error": "No market price available"}
        
        # Create order
        instrument_token = self._get_instrument_token(symbol)
        order = self.oms.create_order(
            symbol=symbol,
            side=transaction_type,
            quantity=quantity,
            order_type="MARKET",
            price=market_price,
            timestamp=self.backtest_engine.current_time,
            instrument_token=instrument_token
        )
        
        # Execute immediately for market orders
        execution_result = self.execution_engine.execute_order(order, market_price)
        self.oms.process_execution(execution_result)
        
        return {
            "status": "EXECUTED",
            "order_id": order.order_id,
            "executed_price": execution_result.executed_price,
            "execution_details": execution_result.execution_details
        }
    
    def place_order_realistic(self, symbol: str, transaction_type: str, quantity: int, 
                            market_price: float, volatility_data=None) -> Dict[str, Any]:
        """
        Realistic order placement (same interface as live trading)
        
        Args:
            symbol: Trading symbol
            transaction_type: "BUY" or "SELL"
            quantity: Order quantity
            market_price: Current market price
            volatility_data: Volatility data (unused in backtest)
            
        Returns:
            Execution details matching live trading format
        """
        result = self.place_order(symbol, transaction_type, quantity, market_price)
        
        if result["status"] == "EXECUTED":
            # Format to match live trading response
            execution_details = result["execution_details"]
            
            return {
                'signal_price': execution_details['market_price'],
                'executed_price': result["executed_price"],
                'side': transaction_type,
                'quantity': quantity,
                'symbol': symbol,
                'slippage_bps': execution_details.get('slippage_amount', 0) / execution_details['market_price'] * 10000,
                'total_delay_ms': execution_details.get('delay_ms', 0),
                'volatility_multiplier': 1.0,  # Not used in backtest
                'execution_time': self.backtest_engine.current_time,
                'order_id': result["order_id"],
                'status': 'COMPLETE'
            }
        
        return result
    
    def get_ltp(self, symbol: str) -> float:
        """
        Get last traded price (replaces live broker.get_ltp)
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Current price
        """
        instrument_token = self._get_instrument_token(symbol)
        return self.backtest_engine.get_current_price(instrument_token)
    
    def _get_instrument_token(self, symbol: str) -> int:
        """
        Map symbol to instrument token
        In production, this would use a proper symbol mapping
        """
        mapped_token = self.backtest_engine.get_symbol_token(symbol)
        if mapped_token is not None:
            return mapped_token

        # Use dedicated synthetic tokens for derivative symbols so we do not
        # accidentally mark option positions to the underlying index price.
        if "CE" in symbol or "PE" in symbol:
            return abs(hash(symbol)) % 1000000 + 1000000
        elif symbol == "NIFTY":
            return 256265
        elif symbol == "BANKNIFTY":
            return 260105
        else:
            return abs(hash(symbol)) % 1000000


class BacktestOrderValidator:
    """
    Validates orders before execution in backtesting
    Ensures realistic order behavior
    """
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
    
    def validate_order(self, order: Order, current_capital: float) -> tuple[bool, str]:
        """
        Validate order before execution
        
        Args:
            order: Order to validate
            current_capital: Current available capital
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if we have enough capital for buy orders
        if order.side.value == "BUY":
            required_capital = order.price * order.quantity
            if required_capital > current_capital:
                return False, f"Insufficient capital: Required ₹{required_capital:.2f}, Available ₹{current_capital:.2f}"
        
        # Check minimum order value
        order_value = order.price * order.quantity
        if order_value < 1:  # Minimum ₹1 order
            return False, f"Order value too small: ₹{order_value:.2f}"
        
        # Check maximum order size (prevent unrealistic orders)
        if order.quantity > 10000:  # Reasonable limit
            return False, f"Order quantity too large: {order.quantity}"
        
        return True, ""
    
    def update_capital(self, new_capital: float):
        """Update current capital"""
        self.current_capital = new_capital
