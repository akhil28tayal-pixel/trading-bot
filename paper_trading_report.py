#!/usr/bin/env python3
"""
Paper Trading Report Generator
Analyzes EC2 logs and generates comprehensive paper trading report
"""

import subprocess
import re
import datetime
from collections import defaultdict

def get_trading_logs():
    """Fetch trading logs from EC2"""
    try:
        cmd = ['ssh', '-i', '~/Downloads/trading-bot.pem', 
               'trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com',
               'cd /home/trader/trading_bot && tail -200 logs/main.log']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.split('\n')
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return []

def parse_trading_data(log_lines):
    """Parse trading data from log lines"""
    trades = []
    pnl_records = []
    
    for line in log_lines:
        if "ORDER EXECUTED:" in line and "PAPER REALISTIC:" in line:
            trade = parse_order(line)
            if trade:
                trades.append(trade)
        elif "SPREAD EXIT" in line and "Net PnL:" in line:
            pnl = parse_pnl(line)
            if pnl:
                pnl_records.append(pnl)
    
    return trades, pnl_records

def parse_order(line):
    """Parse individual order execution"""
    try:
        # Extract order details
        action_match = re.search(r'ORDER EXECUTED: (BUY|SELL) (\d+) (\w+) @ \$?([\d.]+)', line)
        if not action_match:
            return None
            
        action, quantity, symbol, price = action_match.groups()
        
        # Extract slippage and delay
        slippage_match = re.search(r'Slippage: ([\d.]+)bps', line)
        delay_match = re.search(r'Delay: (\d+)ms', line)
        
        return {
            'action': action,
            'quantity': int(quantity),
            'symbol': symbol,
            'price': float(price),
            'slippage_bps': float(slippage_match.group(1)) if slippage_match else 0,
            'delay_ms': int(delay_match.group(1)) if delay_match else 0,
            'line': line.strip()
        }
    except:
        return None

def parse_pnl(line):
    """Parse P&L record"""
    try:
        # Extract strategy
        strategy_match = re.search(r'(\w+) SPREAD EXIT', line)
        strategy = strategy_match.group(1) if strategy_match else "UNKNOWN"
        
        # Extract P&L values
        gross_match = re.search(r'Gross PnL: \$?([\d.]+)', line)
        costs_match = re.search(r'Total Costs: \$?([\d.]+)', line)
        net_match = re.search(r'Net PnL: \$?([\d.]+)', line)
        
        if not all([gross_match, costs_match, net_match]):
            return None
            
        return {
            'strategy': strategy,
            'gross_pnl': float(gross_match.group(1)),
            'costs': float(costs_match.group(1)),
            'net_pnl': float(net_match.group(1)),
            'line': line.strip()
        }
    except:
        return None

def generate_report(trades, pnl_records):
    """Generate comprehensive trading report"""
    print("=" * 80)
    print("PAPER TRADING PERFORMANCE REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: PAPER TRADING (Realistic Simulation)")
    print()
    
    # P&L Summary
    print("PROFIT & LOSS SUMMARY")
    print("-" * 50)
    
    if not pnl_records:
        print("No completed trades found in recent logs.")
        return
    
    total_gross = sum(pnl['gross_pnl'] for pnl in pnl_records)
    total_costs = sum(pnl['costs'] for pnl in pnl_records)
    total_net = sum(pnl['net_pnl'] for pnl in pnl_records)
    
    winning_trades = [pnl for pnl in pnl_records if pnl['net_pnl'] > 0]
    losing_trades = [pnl for pnl in pnl_records if pnl['net_pnl'] < 0]
    
    print(f"Total Completed Trades: {len(pnl_records)}")
    print(f"Winning Trades: {len(winning_trades)}")
    print(f"Losing Trades: {len(losing_trades)}")
    print(f"Win Rate: {len(winning_trades)/len(pnl_records)*100:.1f}%")
    print()
    print(f"Gross P&L: ${total_gross:,.2f}")
    print(f"Total Costs: ${total_costs:,.2f}")
    print(f"Net P&L: ${total_net:,.2f}")
    print()
    
    if winning_trades:
        avg_win = sum(pnl['net_pnl'] for pnl in winning_trades) / len(winning_trades)
        max_win = max(pnl['net_pnl'] for pnl in winning_trades)
        print(f"Average Win: ${avg_win:,.2f}")
        print(f"Maximum Win: ${max_win:,.2f}")
    
    if losing_trades:
        avg_loss = sum(pnl['net_pnl'] for pnl in losing_trades) / len(losing_trades)
        max_loss = min(pnl['net_pnl'] for pnl in losing_trades)
        print(f"Average Loss: ${avg_loss:,.2f}")
        print(f"Maximum Loss: ${max_loss:,.2f}")
    
    print()
    
    # Order Execution Analysis
    print("ORDER EXECUTION ANALYSIS")
    print("-" * 50)
    
    if trades:
        slippages = [trade['slippage_bps'] for trade in trades]
        delays = [trade['delay_ms'] for trade in trades]
        
        buy_orders = [t for t in trades if t['action'] == "BUY"]
        sell_orders = [t for t in trades if t['action'] == "SELL"]
        
        print(f"Total Orders Executed: {len(trades)}")
        print(f"Buy Orders: {len(buy_orders)}")
        print(f"Sell Orders: {len(sell_orders)}")
        print()
        print(f"Average Slippage: {sum(slippages)/len(slippages):.1f} bps")
        print(f"Maximum Slippage: {max(slippages):.1f} bps")
        print(f"Minimum Slippage: {min(slippages):.1f} bps")
        print()
        print(f"Average Execution Delay: {sum(delays)/len(delays):.0f} ms")
        print(f"Maximum Delay: {max(delays):.0f} ms")
        print(f"Minimum Delay: {min(delays):.0f} ms")
    else:
        print("No order executions found.")
    
    print()
    
    # Strategy Performance
    print("STRATEGY PERFORMANCE")
    print("-" * 50)
    
    strategy_stats = defaultdict(list)
    for pnl in pnl_records:
        strategy_stats[pnl['strategy']].append(pnl['net_pnl'])
    
    for strategy, pnls in strategy_stats.items():
        total = sum(pnls)
        trades = len(pnls)
        wins = len([p for p in pnls if p > 0])
        win_rate = wins / trades * 100 if trades > 0 else 0
        
        print(f"{strategy}:")
        print(f"  Net P&L: ${total:,.2f}")
        print(f"  Trades: {trades}")
        print(f"  Win Rate: {win_rate:.1f}%")
        print()
    
    # Recent Completed Trades
    print("RECENT COMPLETED TRADES")
    print("-" * 50)
    
    for pnl in pnl_records[-5:]:  # Last 5 trades
        print(f"{pnl['strategy']} | Net: ${pnl['net_pnl']:7.2f} | "
              f"Gross: ${pnl['gross_pnl']:7.2f} | Costs: ${pnl['costs']:6.2f}")
    
    print()
    
    # Recent Order Executions
    print("RECENT ORDER EXECUTIONS")
    print("-" * 50)
    
    for trade in trades[-10:]:  # Last 10 orders
        print(f"{trade['action']} {trade['quantity']} {trade['symbol']} @ ${trade['price']:.2f} | "
              f"Slippage: {trade['slippage_bps']:.1f}bps | Delay: {trade['delay_ms']}ms")
    
    print()
    
    # Paper Trading Simulation Details
    print("PAPER TRADING SIMULATION DETAILS")
    print("-" * 50)
    print("Realistic Simulation Features:")
    print("  - Real-time market data processing")
    print("  - Realistic slippage modeling (20-40 bps)")
    print("  - Execution delay simulation (150-300ms)")
    print("  - Transaction cost calculation")
    print("  - Options pricing with Greeks")
    print("  - Risk management and position sizing")
    print()
    print("Cost Components:")
    print("  - Brokerage charges")
    print("  - Transaction taxes")
    print("  - GST")
    print("  - SEBI charges")
    print("  - Slippage impact")
    print()
    
    # Performance Metrics
    print("KEY PERFORMANCE METRICS")
    print("-" * 50)
    
    if pnl_records:
        # Profit Factor
        gross_profit = sum(pnl['gross_pnl'] for pnl in winning_trades)
        gross_loss = abs(sum(pnl['gross_pnl'] for pnl in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Average Return per Trade
        avg_return = total_net / len(pnl_records)
        
        print(f"Profit Factor: {profit_factor:.2f}")
        print(f"Average Return per Trade: ${avg_return:.2f}")
        print(f"Cost Efficiency: {(total_gross/total_costs)*100:.1f}% (Gross/Costs ratio)")
        print()
    
    print("Trading Session Analysis:")
    print(f"  - All trades executed in paper mode")
    print(f"  - Real market conditions simulated")
    print(f"  - No actual capital at risk")
    print(f"  - Ready for LIVE trading when profitable")

def main():
    """Main function"""
    print("Fetching paper trading data from EC2...")
    
    # Get trading logs
    log_lines = get_trading_logs()
    
    if not log_lines:
        print("No trading logs found. Is the bot running?")
        return
    
    # Parse data
    trades, pnl_records = parse_trading_data(log_lines)
    
    # Generate report
    generate_report(trades, pnl_records)

if __name__ == "__main__":
    main()
