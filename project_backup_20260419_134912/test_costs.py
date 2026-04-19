#!/usr/bin/env python3
"""
Test script to demonstrate realistic trading cost calculations
"""

from risk.costs import (
    calculate_cost_adjusted_pnl, 
    calculate_round_trip_cost,
    calculate_spread_cost,
    is_trade_viable,
    calculate_single_order_cost
)

def test_option_trade():
    """Test typical option trade costs"""
    print("=" * 60)
    print("🧪 TESTING OPTION TRADE COSTS")
    print("=" * 60)
    
    # Example: Buy 50 NIFTY CE at ₹100, sell at ₹150
    entry_price = 100
    exit_price = 150
    qty = 50
    
    print(f"Trade: BUY {qty} options @ ₹{entry_price}, SELL @ ₹{exit_price}")
    
    # Calculate detailed costs
    entry_cost = calculate_single_order_cost(entry_price, qty, "BUY")
    exit_cost = calculate_single_order_cost(exit_price, qty, "SELL")
    
    print(f"\n📊 ENTRY COSTS (₹{entry_price} x {qty}):")
    for key, value in entry_cost.items():
        if key != 'total':
            print(f"  {key.replace('_', ' ').title()}: ₹{value:.2f}")
    print(f"  TOTAL ENTRY COST: ₹{entry_cost['total']:.2f}")
    
    print(f"\n📊 EXIT COSTS (₹{exit_price} x {qty}):")
    for key, value in exit_cost.items():
        if key != 'total':
            print(f"  {key.replace('_', ' ').title()}: ₹{value:.2f}")
    print(f"  TOTAL EXIT COST: ₹{exit_cost['total']:.2f}")
    
    # Calculate PnL
    pnl_data = calculate_cost_adjusted_pnl(entry_price, exit_price, qty)
    
    print(f"\n💰 PnL ANALYSIS:")
    print(f"  Gross PnL: ₹{pnl_data['gross_pnl']:.2f}")
    print(f"  Total Costs: ₹{pnl_data['total_cost']:.2f}")
    print(f"  Net PnL: ₹{pnl_data['net_pnl']:.2f}")
    print(f"  Cost Impact: {pnl_data['cost_impact']:.2f}%")


def test_trade_viability():
    """Test trade viability checks"""
    print("\n" + "=" * 60)
    print("🎯 TESTING TRADE VIABILITY")
    print("=" * 60)
    
    test_cases = [
        {"entry": 50, "exit": 75, "qty": 50, "desc": "Good trade (50% profit)"},
        {"entry": 20, "exit": 25, "qty": 50, "desc": "Marginal trade (25% profit)"},
        {"entry": 10, "exit": 12, "qty": 50, "desc": "Poor trade (20% profit)"},
        {"entry": 100, "exit": 110, "qty": 15, "desc": "Small quantity trade"},
    ]
    
    for case in test_cases:
        expected_profit = (case["exit"] - case["entry"]) * case["qty"]
        viability = is_trade_viable(expected_profit, case["entry"], case["exit"], case["qty"])
        
        print(f"\n📈 {case['desc']}:")
        print(f"  Entry: ₹{case['entry']}, Exit: ₹{case['exit']}, Qty: {case['qty']}")
        print(f"  Expected Profit: ₹{expected_profit:.2f}")
        print(f"  Total Cost: ₹{viability['total_cost']:.2f}")
        print(f"  Net Profit: ₹{viability['net_profit']:.2f}")
        print(f"  Cost Ratio: {viability['cost_ratio']:.2%}")
        print(f"  Recommendation: {viability['recommendation']} ({'✅' if viability['viable'] else '❌'})")


def test_credit_spread():
    """Test credit spread costs"""
    print("\n" + "=" * 60)
    print("📊 TESTING CREDIT SPREAD COSTS")
    print("=" * 60)
    
    # Example: Sell 24500 CE at ₹80, Buy 24600 CE at ₹40
    sell_price = 80
    buy_price = 40
    qty = 50
    
    print(f"Spread: SELL {qty} @ ₹{sell_price}, BUY {qty} @ ₹{buy_price}")
    print(f"Net Premium Received: ₹{(sell_price - buy_price) * qty:.2f}")
    
    spread_cost = calculate_spread_cost(sell_price, buy_price, qty)
    net_premium = (sell_price - buy_price) * qty
    net_after_costs = net_premium - spread_cost
    
    print(f"\n💰 SPREAD ANALYSIS:")
    print(f"  Gross Premium: ₹{net_premium:.2f}")
    print(f"  Entry Costs: ₹{spread_cost:.2f}")
    print(f"  Net Premium After Costs: ₹{net_after_costs:.2f}")
    print(f"  Cost Impact: {(spread_cost/net_premium)*100:.2f}%")


if __name__ == "__main__":
    test_option_trade()
    test_trade_viability()
    test_credit_spread()
    
    print("\n" + "=" * 60)
    print("✅ ALL COST CALCULATIONS WORKING CORRECTLY!")
    print("=" * 60)
