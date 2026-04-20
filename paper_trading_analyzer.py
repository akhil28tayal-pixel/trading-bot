#!/usr/bin/env python3
"""
Paper Trading Analyzer
Comprehensive analysis of paper trading performance, order execution, and PnL
"""

import os
import sys
import json
import datetime
import re
from collections import defaultdict, namedtuple
import pandas as pd

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Data structures
Trade = namedtuple('Trade', ['timestamp', 'symbol', 'action', 'quantity', 'price', 'slippage_bps', 'delay_ms', 'type'])
PnLRecord = namedtuple('PnLRecord', ['timestamp', 'strategy', 'symbol', 'gross_pnl', 'costs', 'net_pnl', 'entry_spread', 'exit_spread'])

class PaperTradingAnalyzer:
    def __init__(self, log_file_path="logs/main.log"):
        self.log_file_path = log_file_path
        self.trades = []
        self.pnl_records = []
        self.current_positions = {}
        
    def parse_logs(self):
        """Parse trading logs to extract trades and PnL data"""
        try:
            with open(self.log_file_path, 'r') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"Log file not found: {self.log_file_path}")
            return
            
        for line in lines:
            self._parse_line(line.strip())
    
    def _parse_line(self, line):
        """Parse individual log line"""
        timestamp = self._extract_timestamp(line)
        
        # Parse order executions
        if "ORDER EXECUTED:" in line and "PAPER REALISTIC:" in line:
            trade = self._parse_order_execution(line, timestamp)
            if trade:
                self.trades.append(trade)
        
        # Parse PnL records
        elif "SPREAD EXIT" in line and "Net PnL:" in line:
            pnl = self._parse_pnl_record(line, timestamp)
            if pnl:
                self.pnl_records.append(pnl)
    
    def _extract_timestamp(self, line):
        """Extract timestamp from log line"""
        # Assuming format like "2024-04-20 10:15:30"
        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
        if timestamp_match:
            return datetime.datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
        return datetime.datetime.now()
    
    def _parse_order_execution(self, line, timestamp):
        """Parse order execution details"""
        try:
            # Extract order details
            action_match = re.search(r'ORDER EXECUTED: (BUY|SELL) (\d+) (\w+) @ \$?([\d.]+)', line)
            if not action_match:
                return None
                
            action, quantity, symbol, price = action_match.groups()
            
            # Extract slippage
            slippage_match = re.search(r'Slippage: ([\d.]+)bps', line)
            slippage_bps = float(slippage_match.group(1)) if slippage_match else 0
            
            # Extract delay
            delay_match = re.search(r'Delay: (\d+)ms', line)
            delay_ms = int(delay_match.group(1)) if delay_match else 0
            
            return Trade(
                timestamp=timestamp,
                symbol=symbol,
                action=action,
                quantity=int(quantity),
                price=float(price),
                slippage_bps=slippage_bps,
                delay_ms=delay_ms,
                type="PAPER_REALISTIC"
            )
        except Exception as e:
            print(f"Error parsing order execution: {e}")
            return None
    
    def _parse_pnl_record(self, line, timestamp):
        """Parse PnL record details"""
        try:
            # Extract strategy and symbol
            strategy_symbol_match = re.search(r'(\w+) SPREAD EXIT', line)
            if not strategy_symbol_match:
                return None
            strategy = strategy_symbol_match.group(1)
            
            # Extract PnL details
            gross_match = re.search(r'Gross PnL: \$?([\d.]+)', line)
            costs_match = re.search(r'Total Costs: \$?([\d.]+)', line)
            net_match = re.search(r'Net PnL: \$?([\d.]+)', line)
            entry_match = re.search(r'Entry spread: ([\d.]+)', line)
            exit_match = re.search(r'Exit spread: ([\d.]+)', line)
            
            if not all([gross_match, costs_match, net_match]):
                return None
                
            return PnLRecord(
                timestamp=timestamp,
                strategy=strategy,
                symbol=f"{strategy}_SPREAD",
                gross_pnl=float(gross_match.group(1)),
                costs=float(costs_match.group(1)),
                net_pnl=float(net_match.group(1)),
                entry_spread=float(entry_match.group(1)) if entry_match else 0,
                exit_spread=float(exit_match.group(1)) if exit_match else 0
            )
        except Exception as e:
            print(f"Error parsing PnL record: {e}")
            return None
    
    def generate_summary_report(self):
        """Generate comprehensive trading summary"""
        if not self.trades and not self.pnl_records:
            print("No trading data found. Make sure the bot is running and logs are available.")
            return
        
        print("=" * 80)
        print("PAPER TRADING PERFORMANCE ANALYSIS")
        print("=" * 80)
        print(f"Analysis Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Log File: {self.log_file_path}")
        print()
        
        # Overall PnL Summary
        self._print_pnl_summary()
        
        # Order Execution Analysis
        self._print_execution_analysis()
        
        # Recent Trades
        self._print_recent_trades()
        
        # Performance Metrics
        self._print_performance_metrics()
    
    def _print_pnl_summary(self):
        """Print PnL summary"""
        print("PROFIT & LOSS SUMMARY")
        print("-" * 40)
        
        if not self.pnl_records:
            print("No completed trades found.")
            return
        
        total_gross = sum(pnl.gross_pnl for pnl in self.pnl_records)
        total_costs = sum(pnl.costs for pnl in self.pnl_records)
        total_net = sum(pnl.net_pnl for pnl in self.pnl_records)
        
        winning_trades = [pnl for pnl in self.pnl_records if pnl.net_pnl > 0]
        losing_trades = [pnl for pnl in self.pnl_records if pnl.net_pnl < 0]
        
        print(f"Total Trades: {len(self.pnl_records)}")
        print(f"Winning Trades: {len(winning_trades)}")
        print(f"Losing Trades: {len(losing_trades)}")
        print(f"Win Rate: {len(winning_trades)/len(self.pnl_records)*100:.1f}%")
        print()
        print(f"Gross P&L: ${total_gross:,.2f}")
        print(f"Total Costs: ${total_costs:,.2f}")
        print(f"Net P&L: ${total_net:,.2f}")
        print()
        
        if winning_trades:
            avg_win = sum(pnl.net_pnl for pnl in winning_trades) / len(winning_trades)
            max_win = max(pnl.net_pnl for pnl in winning_trades)
            print(f"Average Win: ${avg_win:,.2f}")
            print(f"Maximum Win: ${max_win:,.2f}")
        
        if losing_trades:
            avg_loss = sum(pnl.net_pnl for pnl in losing_trades) / len(losing_trades)
            max_loss = min(pnl.net_pnl for pnl in losing_trades)
            print(f"Average Loss: ${avg_loss:,.2f}")
            print(f"Maximum Loss: ${max_loss:,.2f}")
        
        print()
    
    def _print_execution_analysis(self):
        """Print order execution analysis"""
        print("ORDER EXECUTION ANALYSIS")
        print("-" * 40)
        
        if not self.trades:
            print("No order executions found.")
            return
        
        # Slippage analysis
        slippages = [trade.slippage_bps for trade in self.trades]
        avg_slippage = sum(slippages) / len(slippages)
        max_slippage = max(slippages)
        
        # Delay analysis
        delays = [trade.delay_ms for trade in self.trades]
        avg_delay = sum(delays) / len(delays)
        max_delay = max(delays)
        
        # Order breakdown
        buy_orders = [t for t in self.trades if t.action == "BUY"]
        sell_orders = [t for t in self.trades if t.action == "SELL"]
        
        print(f"Total Orders: {len(self.trades)}")
        print(f"Buy Orders: {len(buy_orders)}")
        print(f"Sell Orders: {len(sell_orders)}")
        print()
        print(f"Average Slippage: {avg_slippage:.1f} bps")
        print(f"Maximum Slippage: {max_slippage:.1f} bps")
        print(f"Average Execution Delay: {avg_delay:.0f} ms")
        print(f"Maximum Execution Delay: {max_delay:.0f} ms")
        print()
    
    def _print_recent_trades(self):
        """Print recent completed trades"""
        print("RECENT COMPLETED TRADES")
        print("-" * 40)
        
        if not self.pnl_records:
            print("No completed trades found.")
            return
        
        # Show last 10 trades
        recent_trades = sorted(self.pnl_records, key=lambda x: x.timestamp, reverse=True)[:10]
        
        for trade in recent_trades:
            print(f"{trade.timestamp.strftime('%H:%M:%S')} | {trade.strategy} | "
                  f"Net: ${trade.net_pnl:7.2f} | Gross: ${trade.gross_pnl:7.2f} | "
                  f"Costs: ${trade.costs:6.2f}")
        print()
    
    def _print_performance_metrics(self):
        """Print detailed performance metrics"""
        print("PERFORMANCE METRICS")
        print("-" * 40)
        
        if not self.pnl_records:
            print("Insufficient data for performance metrics.")
            return
        
        # Calculate daily PnL
        daily_pnl = defaultdict(float)
        for pnl in self.pnl_records:
            date = pnl.timestamp.date()
            daily_pnl[date] += pnl.net_pnl
        
        print("Daily P&L Breakdown:")
        for date, pnl in sorted(daily_pnl.items()):
            print(f"  {date}: ${pnl:,.2f}")
        
        print()
        
        # Strategy performance
        strategy_pnl = defaultdict(list)
        for pnl in self.pnl_records:
            strategy_pnl[pnl.strategy].append(pnl.net_pnl)
        
        print("Strategy Performance:")
        for strategy, pnls in strategy_pnl.items():
            total = sum(pnls)
            trades = len(pnls)
            wins = len([p for p in pnls if p > 0])
            win_rate = wins / trades * 100 if trades > 0 else 0
            
            print(f"  {strategy}: ${total:,.2f} | {trades} trades | {win_rate:.1f}% win rate")
        
        print()
    
    def export_to_csv(self, filename="paper_trading_report.csv"):
        """Export trading data to CSV"""
        try:
            # Create DataFrames
            trades_df = pd.DataFrame([t._asdict() for t in self.trades])
            pnl_df = pd.DataFrame([p._asdict() for p in self.pnl_records])
            
            # Save to CSV
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                trades_df.to_excel(writer, sheet_name='Orders', index=False)
                pnl_df.to_excel(writer, sheet_name='P&L', index=False)
            
            print(f"Trading report exported to: {filename}")
        except Exception as e:
            print(f"Error exporting to CSV: {e}")

def main():
    """Main function to run the analyzer"""
    print("Paper Trading Analyzer")
    print("======================")
    
    # Initialize analyzer
    analyzer = PaperTradingAnalyzer()
    
    # Parse logs
    print("Parsing trading logs...")
    analyzer.parse_logs()
    
    # Generate report
    analyzer.generate_summary_report()
    
    # Export option
    export_choice = input("\nExport report to CSV? (y/n): ").lower()
    if export_choice == 'y':
        filename = f"paper_trading_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        analyzer.export_to_csv(filename)

if __name__ == "__main__":
    main()
