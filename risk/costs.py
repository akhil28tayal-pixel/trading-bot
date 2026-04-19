"""
Realistic Trading Cost Calculator for Indian Options Trading (Zerodha)
"""

def calculate_single_order_cost(price, qty, transaction_type="BUY"):
    """
    Calculate cost for a single order (entry OR exit)
    
    Args:
        price: Option price per unit
        qty: Quantity
        transaction_type: "BUY" or "SELL"
    
    Returns:
        dict: Breakdown of costs
    """
    turnover = price * qty
    
    # Zerodha costs
    brokerage = 20  # ₹20 per order
    
    # STT: 0.05% on sell side only for options
    stt = turnover * 0.0005 if transaction_type == "SELL" else 0
    
    # Transaction charges: ~0.053% of turnover
    transaction_charges = turnover * 0.00053
    
    # SEBI charges: ₹10 per crore (negligible for most trades)
    sebi_charges = max(turnover * 0.000001, 0.01)  # Min ₹0.01
    
    # Stamp duty: 0.003% on buy side (options)
    stamp_duty = turnover * 0.00003 if transaction_type == "BUY" else 0
    
    # GST: 18% on (brokerage + transaction charges + SEBI charges)
    taxable_amount = brokerage + transaction_charges + sebi_charges
    gst = taxable_amount * 0.18
    
    total_cost = brokerage + stt + transaction_charges + sebi_charges + stamp_duty + gst
    
    return {
        'brokerage': brokerage,
        'stt': stt,
        'transaction_charges': transaction_charges,
        'sebi_charges': sebi_charges,
        'stamp_duty': stamp_duty,
        'gst': gst,
        'total': total_cost
    }


def calculate_round_trip_cost(entry_price, exit_price, qty):
    """
    Calculate total cost for complete trade (entry + exit)
    
    Args:
        entry_price: Entry price per unit
        exit_price: Exit price per unit  
        qty: Quantity
    
    Returns:
        float: Total round-trip cost
    """
    entry_cost = calculate_single_order_cost(entry_price, qty, "BUY")
    exit_cost = calculate_single_order_cost(exit_price, qty, "SELL")
    
    return entry_cost['total'] + exit_cost['total']


def calculate_spread_cost(sell_price, buy_price, qty):
    """
    Calculate cost for credit spread (sell higher strike, buy lower strike)
    
    Args:
        sell_price: Price of sold option
        buy_price: Price of bought option
        qty: Quantity
    
    Returns:
        float: Total spread cost
    """
    sell_cost = calculate_single_order_cost(sell_price, qty, "SELL")
    buy_cost = calculate_single_order_cost(buy_price, qty, "BUY")
    
    return sell_cost['total'] + buy_cost['total']


def is_trade_viable(expected_profit, entry_price, exit_price, qty, min_profit_ratio=0.1):
    """
    Check if trade is viable after costs
    
    Args:
        expected_profit: Expected gross profit
        entry_price: Entry price
        exit_price: Expected exit price
        qty: Quantity
        min_profit_ratio: Minimum profit ratio after costs (10% default)
    
    Returns:
        dict: Viability analysis
    """
    total_cost = calculate_round_trip_cost(entry_price, exit_price, qty)
    net_profit = expected_profit - total_cost
    
    # Check if net profit meets minimum threshold
    viable = net_profit > (total_cost * min_profit_ratio)
    
    return {
        'viable': viable,
        'gross_profit': expected_profit,
        'total_cost': total_cost,
        'net_profit': net_profit,
        'cost_ratio': total_cost / abs(expected_profit) if expected_profit != 0 else float('inf'),
        'recommendation': 'TAKE' if viable else 'SKIP'
    }


def calculate_cost_adjusted_pnl(entry_price, exit_price, qty):
    """
    Calculate PnL after deducting all trading costs
    
    Args:
        entry_price: Entry price per unit
        exit_price: Exit price per unit
        qty: Quantity
    
    Returns:
        dict: Detailed PnL breakdown
    """
    gross_pnl = (exit_price - entry_price) * qty
    total_cost = calculate_round_trip_cost(entry_price, exit_price, qty)
    net_pnl = gross_pnl - total_cost
    
    return {
        'gross_pnl': gross_pnl,
        'total_cost': total_cost,
        'net_pnl': net_pnl,
        'cost_impact': (total_cost / abs(gross_pnl) * 100) if gross_pnl != 0 else 0
    }


# Legacy function for backward compatibility
def calculate_cost(option_price, qty):
    """
    Legacy function - calculates approximate round-trip cost
    """
    return calculate_round_trip_cost(option_price, option_price, qty)
