"""
Order Management System for Backtesting
Tracks positions, orders, and executions exactly like live trading
"""

import datetime as dt
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from logger import log


class OrderStatus(Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Order:
    """Represents a trading order"""
    order_id: str
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    price: float
    timestamp: dt.datetime
    instrument_token: int
    status: OrderStatus = OrderStatus.PENDING
    executed_price: Optional[float] = None
    executed_quantity: int = 0
    execution_timestamp: Optional[dt.datetime] = None
    
    def __post_init__(self):
        if isinstance(self.side, str):
            self.side = OrderSide(self.side)
        if isinstance(self.order_type, str):
            self.order_type = OrderType(self.order_type)
        if isinstance(self.status, str):
            self.status = OrderStatus(self.status)


@dataclass
class Position:
    """Represents a trading position"""
    symbol: str
    instrument_token: int
    side: OrderSide
    quantity: int
    entry_price: float
    entry_timestamp: dt.datetime
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    
    def update_current_price(self, price: float):
        """Update current price and unrealized PnL"""
        self.current_price = price
        
        if self.side == OrderSide.BUY:
            self.unrealized_pnl = (price - self.entry_price) * self.quantity
        else:  # SELL
            self.unrealized_pnl = (self.entry_price - price) * self.quantity


@dataclass
class Trade:
    """Represents a completed trade"""
    trade_id: str
    symbol: str
    instrument_token: int
    side: OrderSide
    quantity: int
    entry_price: float
    exit_price: float
    entry_timestamp: dt.datetime
    exit_timestamp: dt.datetime
    gross_pnl: float
    costs: float
    net_pnl: float
    slippage_bps: float = 0.0
    execution_details: Dict = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of order execution"""
    order_id: str
    executed_price: float
    executed_quantity: int
    execution_timestamp: dt.datetime
    slippage_bps: float
    costs: float
    execution_details: Dict = field(default_factory=dict)


class OrderManagementSystem:
    """
    Comprehensive Order Management System for backtesting
    Tracks all orders, positions, and trades
    """
    
    def __init__(self):
        # Order tracking
        self.orders: Dict[str, Order] = {}
        self.pending_orders: List[Order] = []
        
        # Position tracking
        self.active_positions: Dict[str, Position] = {}  # symbol -> position
        self.position_history: List[Position] = []
        
        # Trade tracking
        self.trade_history: List[Trade] = []
        self.realized_pnl = 0.0
        self.daily_pnl = 0.0
        
        # Statistics
        self.total_orders = 0
        self.executed_orders = 0
        self.cancelled_orders = 0
        
        log("Order Management System initialized")
    
    def create_order(self, symbol: str, side: str, quantity: int, 
                    order_type: str, price: float, timestamp: dt.datetime,
                    instrument_token: int) -> Order:
        """
        Create a new order
        
        Args:
            symbol: Trading symbol
            side: "BUY" or "SELL"
            quantity: Order quantity
            order_type: "MARKET", "LIMIT", etc.
            price: Order price
            timestamp: Order timestamp
            instrument_token: Instrument token
            
        Returns:
            Order object
        """
        order_id = str(uuid.uuid4())[:8]  # Short UUID
        
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=OrderSide(side),
            quantity=quantity,
            order_type=OrderType(order_type),
            price=price,
            timestamp=timestamp,
            instrument_token=instrument_token
        )
        
        self.orders[order_id] = order
        self.pending_orders.append(order)
        self.total_orders += 1
        
        log(f"Order created: {order_id} - {side} {quantity} {symbol} @ ₹{price:.2f}")
        return order
    
    def process_execution(self, execution_result: ExecutionResult):
        """
        Process order execution result
        
        Args:
            execution_result: Execution details
        """
        order_id = execution_result.order_id
        order = self.orders.get(order_id)
        
        if not order:
            log(f"Error: Order {order_id} not found for execution")
            return
        
        # Update order status
        order.status = OrderStatus.EXECUTED
        order.executed_price = execution_result.executed_price
        order.executed_quantity = execution_result.executed_quantity
        order.execution_timestamp = execution_result.execution_timestamp
        
        # Remove from pending orders
        if order in self.pending_orders:
            self.pending_orders.remove(order)
        
        self.executed_orders += 1
        
        # Update positions
        self._update_positions(order, execution_result)
        
        log(f"Order executed: {order_id} - {order.side.value} {order.executed_quantity} "
            f"{order.symbol} @ ₹{order.executed_price:.2f}")
    
    def _update_positions(self, order: Order, execution_result: ExecutionResult):
        """Update positions based on order execution"""
        symbol = order.symbol
        
        if symbol in self.active_positions:
            # Existing position
            position = self.active_positions[symbol]
            
            if order.side == position.side:
                # Adding to position
                total_quantity = position.quantity + order.executed_quantity
                weighted_price = ((position.entry_price * position.quantity) + 
                                (order.executed_price * order.executed_quantity)) / total_quantity
                
                position.quantity = total_quantity
                position.entry_price = weighted_price
                
            else:
                # Reducing or closing position
                if order.executed_quantity >= position.quantity:
                    # Closing position (and potentially opening opposite)
                    self._close_position(position, order, execution_result)
                    
                    # If quantity exceeds position, open new opposite position
                    remaining_qty = order.executed_quantity - position.quantity
                    if remaining_qty > 0:
                        self._open_position(order, remaining_qty, execution_result)
                else:
                    # Partial close
                    position.quantity -= order.executed_quantity
        else:
            # New position
            self._open_position(order, order.executed_quantity, execution_result)
    
    def _open_position(self, order: Order, quantity: int, execution_result: ExecutionResult):
        """Open a new position"""
        position = Position(
            symbol=order.symbol,
            instrument_token=order.instrument_token,
            side=order.side,
            quantity=quantity,
            entry_price=order.executed_price,
            entry_timestamp=order.execution_timestamp,
            current_price=order.executed_price
        )
        
        self.active_positions[order.symbol] = position
        log(f"Position opened: {order.side.value} {quantity} {order.symbol} @ ₹{order.executed_price:.2f}")
    
    def _close_position(self, position: Position, order: Order, execution_result: ExecutionResult):
        """Close an existing position"""
        # Calculate PnL
        if position.side == OrderSide.BUY:
            gross_pnl = (order.executed_price - position.entry_price) * position.quantity
        else:
            gross_pnl = (position.entry_price - order.executed_price) * position.quantity
        
        net_pnl = gross_pnl - execution_result.costs
        
        # Create trade record
        trade = Trade(
            trade_id=str(uuid.uuid4())[:8],
            symbol=position.symbol,
            instrument_token=position.instrument_token,
            side=position.side,
            quantity=position.quantity,
            entry_price=position.entry_price,
            exit_price=order.executed_price,
            entry_timestamp=position.entry_timestamp,
            exit_timestamp=order.execution_timestamp,
            gross_pnl=gross_pnl,
            costs=execution_result.costs,
            net_pnl=net_pnl,
            slippage_bps=execution_result.slippage_bps,
            execution_details=execution_result.execution_details
        )
        
        self.trade_history.append(trade)
        self.realized_pnl += net_pnl
        self.daily_pnl += net_pnl
        
        # Move to history and remove from active
        self.position_history.append(position)
        del self.active_positions[position.symbol]
        
        log(f"Position closed: {position.side.value} {position.quantity} {position.symbol} "
            f"| PnL: ₹{net_pnl:.2f} (Gross: ₹{gross_pnl:.2f}, Costs: ₹{execution_result.costs:.2f})")
    
    def process_pending_orders(self, current_prices: Dict[int, float], execution_engine):
        """
        Process pending orders against current market prices
        
        Args:
            current_prices: Dict of instrument_token -> current_price
            execution_engine: Execution engine for order processing
        """
        executed_orders = []
        
        for order in self.pending_orders[:]:  # Copy list to avoid modification during iteration
            current_price = current_prices.get(order.instrument_token)
            
            if current_price is None:
                continue
            
            should_execute = False
            
            # Market orders execute immediately
            if order.order_type == OrderType.MARKET:
                should_execute = True
            
            # Limit orders execute when price is favorable
            elif order.order_type == OrderType.LIMIT:
                if order.side == OrderSide.BUY and current_price <= order.price:
                    should_execute = True
                elif order.side == OrderSide.SELL and current_price >= order.price:
                    should_execute = True
            
            if should_execute:
                # Execute order
                execution_result = execution_engine.execute_order(order, current_price)
                self.process_execution(execution_result)
                executed_orders.append(order)
        
        return executed_orders
    
    def update_position_prices(self, current_prices: Dict[int, float]):
        """Update current prices for all active positions"""
        for position in self.active_positions.values():
            current_price = current_prices.get(position.instrument_token)
            if current_price:
                position.update_current_price(current_price)
    
    def get_unrealized_pnl(self, current_prices: Dict[int, float]) -> float:
        """Calculate total unrealized PnL"""
        self.update_position_prices(current_prices)
        return sum(pos.unrealized_pnl for pos in self.active_positions.values())
    
    def get_daily_pnl(self) -> float:
        """Get daily realized PnL"""
        return self.daily_pnl
    
    def reset_daily_pnl(self):
        """Reset daily PnL counter"""
        self.daily_pnl = 0.0
    
    def close_all_positions(self, current_prices: Dict[int, float], execution_engine):
        """Close all active positions at current market prices"""
        positions_to_close = list(self.active_positions.values())
        
        for position in positions_to_close:
            current_price = current_prices.get(position.instrument_token)
            if current_price is None:
                log(f"Warning: No current price for {position.symbol}, using entry price")
                current_price = position.entry_price
            
            opposite_side = OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY

            # Register the closing order with the OMS so execution updates become real trades.
            closing_order = self.create_order(
                symbol=position.symbol,
                side=opposite_side.value,
                quantity=position.quantity,
                order_type=OrderType.MARKET.value,
                price=current_price,
                timestamp=dt.datetime.now(),
                instrument_token=position.instrument_token,
            )

            # Execute closing order
            execution_result = execution_engine.execute_order(closing_order, current_price)
            self.process_execution(execution_result)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive trading statistics"""
        if not self.trade_history:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'total_pnl': self.realized_pnl
            }
        
        winning_trades = [t for t in self.trade_history if t.net_pnl > 0]
        losing_trades = [t for t in self.trade_history if t.net_pnl < 0]
        
        total_trades = len(self.trade_history)
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        avg_win = sum(t.net_pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.net_pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        total_wins = sum(t.net_pnl for t in winning_trades)
        total_losses = abs(sum(t.net_pnl for t in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_pnl': self.realized_pnl,
            'total_costs': sum(t.costs for t in self.trade_history),
            'avg_slippage_bps': sum(t.slippage_bps for t in self.trade_history) / total_trades if total_trades > 0 else 0
        }
