"""
Realistic Order Execution Module
Handles slippage, execution delays, and market impact simulation
"""

import time
import random
import datetime as dt
from logger import log
import config


def apply_slippage(price, side, slippage_percent=None, volatility_multiplier=1.0):
    """
    Apply realistic slippage to order execution
    
    Args:
        price: Market price at signal time
        side: "BUY" or "SELL"
        slippage_percent: Override default slippage
        volatility_multiplier: Adjust slippage based on market conditions
    
    Returns:
        float: Executed price after slippage
    """
    if not config.ENABLE_SLIPPAGE:
        return price
    
    # Use provided slippage or default from config
    base_slippage = slippage_percent or config.SLIPPAGE_PERCENT
    
    # Apply volatility adjustment
    adjusted_slippage = base_slippage * volatility_multiplier
    
    # Add random component (±20% variation)
    random_factor = random.uniform(0.8, 1.2)
    final_slippage = adjusted_slippage * random_factor
    
    if side.upper() == "BUY":
        # BUY orders get filled at higher price (unfavorable)
        executed_price = price * (1 + final_slippage)
    elif side.upper() == "SELL":
        # SELL orders get filled at lower price (unfavorable)
        executed_price = price * (1 - final_slippage)
    else:
        raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")
    
    # Log slippage impact
    slippage_impact = abs(executed_price - price)
    log(f"Slippage applied: {side} {price:.2f} → {executed_price:.2f} (Impact: ₹{slippage_impact:.2f})")
    
    return executed_price


def simulate_execution_delay(delay_ms=None):
    """
    Simulate realistic execution delay
    
    Args:
        delay_ms: Override default delay in milliseconds
    """
    if not config.ENABLE_DELAY:
        return
    
    # Use provided delay or default from config
    delay = delay_ms or config.EXECUTION_DELAY_MS
    
    # Add random variation (±30%)
    random_factor = random.uniform(0.7, 1.3)
    actual_delay = delay * random_factor
    
    # Sleep for the delay period
    time.sleep(actual_delay / 1000)
    
    log(f"Execution delay: {actual_delay:.0f}ms")


def calculate_volatility_multiplier(current_price, price_history, lookback_periods=20):
    """
    Calculate volatility multiplier for dynamic slippage
    
    Args:
        current_price: Current market price
        price_history: List of recent prices
        lookback_periods: Number of periods to calculate volatility
    
    Returns:
        float: Volatility multiplier (1.0 = normal, >1.0 = high volatility)
    """
    if len(price_history) < 2:
        return 1.0
    
    # Calculate recent price changes
    effective_lookback = min(lookback_periods, len(price_history))
    recent_prices = price_history[-effective_lookback:]
    price_changes = []
    
    for i in range(1, len(recent_prices)):
        change = abs(recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1]
        price_changes.append(change)
    
    if not price_changes:
        return 1.0
    
    # Calculate average volatility
    avg_volatility = sum(price_changes) / len(price_changes)
    
    # Normalize to multiplier (1.5% avg volatility = 1.0 multiplier)
    volatility_multiplier = max(0.5, min(3.0, avg_volatility / 0.015))
    
    return volatility_multiplier


def get_market_impact_slippage(quantity, avg_volume, base_slippage):
    """
    Calculate additional slippage based on market impact
    
    Args:
        quantity: Order quantity
        avg_volume: Average trading volume
        base_slippage: Base slippage percentage
    
    Returns:
        float: Adjusted slippage percentage
    """
    if avg_volume <= 0:
        return base_slippage
    
    # Calculate order size as percentage of average volume
    order_impact = quantity / avg_volume
    
    # Apply square root impact model
    impact_multiplier = 1 + (order_impact ** 0.5) * 2
    
    # Cap the impact multiplier
    impact_multiplier = min(impact_multiplier, 3.0)
    
    return base_slippage * impact_multiplier


def execute_order_with_realism(price, side, quantity, symbol=None, volatility_data=None):
    """
    Execute order with realistic slippage and delay
    
    Args:
        price: Market price at signal time
        side: "BUY" or "SELL"
        quantity: Order quantity
        symbol: Trading symbol (for logging)
        volatility_data: Dict with price history for volatility calculation
    
    Returns:
        dict: Execution details
    """
    start_time = dt.datetime.now()
    
    # Calculate volatility multiplier if data available
    volatility_multiplier = 1.0
    if config.ENABLE_VOLATILITY_ADJUSTMENT and volatility_data and 'price_history' in volatility_data:
        volatility_multiplier = calculate_volatility_multiplier(
            price, 
            volatility_data['price_history']
        )
    if config.ENABLE_TIME_BASED_SLIPPAGE:
        volatility_multiplier *= get_time_based_slippage()
    
    # Simulate execution delay
    simulate_execution_delay()
    
    # Apply slippage
    executed_price = apply_slippage(price, side, volatility_multiplier=volatility_multiplier)
    
    # Calculate execution metrics
    execution_time = dt.datetime.now()
    total_delay = (execution_time - start_time).total_seconds() * 1000
    slippage_bps = abs(executed_price - price) / price * 10000
    
    execution_details = {
        'signal_price': price,
        'executed_price': executed_price,
        'side': side,
        'quantity': quantity,
        'symbol': symbol or 'UNKNOWN',
        'slippage_bps': slippage_bps,
        'total_delay_ms': total_delay,
        'volatility_multiplier': volatility_multiplier,
        'execution_time': execution_time
    }
    
    # Log execution summary
    log(f"ORDER EXECUTED: {side} {quantity} {symbol} @ ₹{executed_price:.2f} "
        f"(Slippage: {slippage_bps:.1f}bps, Delay: {total_delay:.0f}ms)")
    
    return execution_details


def simulate_partial_fill(quantity, fill_probability=0.95):
    """
    Simulate partial order fills (optional advanced feature)
    
    Args:
        quantity: Requested quantity
        fill_probability: Probability of full fill
    
    Returns:
        int: Actually filled quantity
    """
    if random.random() < fill_probability:
        return quantity
    else:
        # Partial fill (80-99% of requested quantity)
        fill_ratio = random.uniform(0.8, 0.99)
        filled_qty = int(quantity * fill_ratio)
        log(f"Partial fill: {filled_qty}/{quantity} ({fill_ratio:.1%})")
        return filled_qty


def get_time_based_slippage():
    """
    Adjust slippage based on time of day
    Higher slippage during market open/close
    
    Returns:
        float: Time-based slippage multiplier
    """
    now = dt.datetime.now()
    hour = now.hour
    minute = now.minute
    
    # Higher slippage during:
    # - Market open (9:15-9:45)
    # - Market close (15:00-15:30)
    # - Lunch time (12:00-13:00)
    
    if (hour == 9 and minute <= 45) or (hour == 15 and minute <= 30):
        return 1.5  # 50% higher slippage
    elif hour == 12:
        return 1.2  # 20% higher slippage
    else:
        return 1.0  # Normal slippage


# Price history storage for volatility calculation
price_history = {
    'NIFTY': [],
    'BANKNIFTY': []
}


def update_price_history(symbol, price, max_history=100):
    """
    Update price history for volatility calculations
    
    Args:
        symbol: Trading symbol
        price: Current price
        max_history: Maximum history to maintain
    """
    if symbol not in price_history:
        price_history[symbol] = []
    
    price_history[symbol].append(price)
    
    # Keep only recent history
    if len(price_history[symbol]) > max_history:
        price_history[symbol] = price_history[symbol][-max_history:]


def get_execution_summary():
    """
    Get summary of execution statistics (for analysis)
    
    Returns:
        dict: Execution statistics
    """
    # This could be expanded to track execution metrics
    return {
        'slippage_enabled': config.ENABLE_SLIPPAGE,
        'delay_enabled': config.ENABLE_DELAY,
        'base_slippage': config.SLIPPAGE_PERCENT,
        'base_delay': config.EXECUTION_DELAY_MS
    }
