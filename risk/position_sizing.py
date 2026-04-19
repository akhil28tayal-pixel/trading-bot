def calculate_qty(capital, risk_percent, entry_price, sl_price, lot_size):

    risk_amount = capital * risk_percent

    sl_distance = abs(entry_price - sl_price)

    if sl_distance == 0:
        return lot_size

    qty = risk_amount / sl_distance

    # convert to lots
    lots = int(qty // lot_size)

    return max(lots * lot_size, lot_size)


def calculate_spread_qty(capital, risk_percent, sell_price, buy_price, strike_diff, lot_size):
    """Calculate quantity for credit spreads based on risk management"""
    
    risk_amount = capital * risk_percent
    
    # Max loss for credit spread = strike difference - net premium received
    net_premium = sell_price - buy_price
    max_loss = strike_diff - net_premium
    
    if max_loss <= 0:
        return lot_size
    
    qty = risk_amount / max_loss
    
    # Convert to lots
    lots = int(qty // lot_size)
    
    return max(lots * lot_size, lot_size)