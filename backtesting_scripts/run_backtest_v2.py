#!/usr/bin/env python3
"""
Complete Backtesting Example
Demonstrates how to run backtests using existing strategies
"""

import datetime as dt
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.engine_v2 import BacktestEngine, BacktestConfig
from backtest.data import DataProvider
from backtest.strategy_adapter import BacktestContext, create_backtest_with_strategies
from backtest.metrics import BacktestReporter
from logger import log

# Import existing strategies
import strategies.breakout_ws as breakout_strategy
import strategies.credit_spread_ws as credit_spread_strategy


def run_comprehensive_backtest():
    """Run a comprehensive backtest with multiple strategies"""
    
    print("🚀 Starting Comprehensive Backtesting Engine")
    print("=" * 60)
    
    # Configure backtest
    backtest_config = BacktestConfig(
        start_date=dt.datetime(2026, 1, 1),
        end_date=dt.datetime(2026, 3, 31),
        initial_capital=100000,
        enable_slippage=True,
        enable_delay=True,
        enable_costs=True,
        tick_frequency="1min",
        max_daily_loss=0.03,
        verbose=True
    )
    
    print(f"📅 Backtest Period: {backtest_config.start_date.date()} to {backtest_config.end_date.date()}")
    print(f"💰 Initial Capital: ₹{backtest_config.initial_capital:,}")
    print(f"⚙️  Realism: Slippage={backtest_config.enable_slippage}, Costs={backtest_config.enable_costs}")
    print()
    
    # Create backtest engine
    engine = BacktestEngine(backtest_config)
    
    # Add market data
    print("📊 Loading Market Data...")
    data_provider = DataProvider()
    
    # Get NIFTY data
    nifty_data = data_provider.get_data(
        instrument_token=256265,
        start=backtest_config.start_date,
        end=backtest_config.end_date,
        interval="1minute"
    )
    engine.add_market_data("NIFTY", nifty_data, 256265)
    
    # Get BANKNIFTY data
    banknifty_data = data_provider.get_data(
        instrument_token=260105,
        start=backtest_config.start_date,
        end=backtest_config.end_date,
        interval="1minute"
    )
    engine.add_market_data("BANKNIFTY", banknifty_data, 260105)
    
    print(f"✅ Loaded {len(nifty_data)} NIFTY bars")
    print(f"✅ Loaded {len(banknifty_data)} BANKNIFTY bars")
    print()
    
    # Setup strategy context
    print("🎯 Setting up Strategies...")
    context = BacktestContext(engine)
    
    with context:
        # Add breakout strategies
        context.add_strategy(breakout_strategy, "NIFTY")
        context.add_strategy(breakout_strategy, "BANKNIFTY")
        
        # Add credit spread strategies
        context.add_strategy(credit_spread_strategy, "NIFTY")
        context.add_strategy(credit_spread_strategy, "BANKNIFTY")
        
        print("✅ Strategies configured")
        print()
        
        # Run backtest
        print("🔄 Running Backtest...")
        print("This may take a few minutes for realistic simulation...")
        print()
        
        results = engine.run()
    
    # Generate comprehensive report
    print("📈 Generating Results...")
    print()
    
    # Print summary
    summary = results['summary']
    print("BACKTEST RESULTS SUMMARY")
    print("=" * 40)
    print(f"Initial Capital:    ₹{summary['initial_capital']:,.2f}")
    print(f"Final Capital:      ₹{summary['final_capital']:,.2f}")
    print(f"Total Return:       {summary['total_return']:.2%}")
    print(f"Total P&L:          ₹{summary['total_pnl']:,.2f}")
    print(f"Total Trades:       {summary['total_trades']}")
    print(f"Execution Time:     {summary['execution_time']:.2f} seconds")
    print()
    
    # Detailed analysis
    if results.get('performance_metrics'):
        metrics = results['performance_metrics']
        print("PERFORMANCE METRICS")
        print("=" * 40)
        print(f"Sharpe Ratio:       {metrics.sharpe_ratio:.2f}")
        print(f"Max Drawdown:       {metrics.max_drawdown:.2%}")
        print(f"Win Rate:           {metrics.win_rate:.2%}")
        print(f"Profit Factor:      {metrics.profit_factor:.2f}")
        print()
    
    # Trade analysis
    if results.get('trades'):
        trades = results['trades']
        winning_trades = [t for t in trades if t.net_pnl > 0]
        losing_trades = [t for t in trades if t.net_pnl < 0]
        
        print("TRADE ANALYSIS")
        print("=" * 40)
        print(f"Winning Trades:     {len(winning_trades)}")
        print(f"Losing Trades:      {len(losing_trades)}")
        
        if winning_trades:
            avg_win = sum(t.net_pnl for t in winning_trades) / len(winning_trades)
            print(f"Average Win:        ₹{avg_win:.2f}")
        
        if losing_trades:
            avg_loss = sum(t.net_pnl for t in losing_trades) / len(losing_trades)
            print(f"Average Loss:       ₹{avg_loss:.2f}")
        
        print()
    
    # Cost analysis
    execution_stats = engine.execution_engine.get_execution_statistics()
    print("EXECUTION ANALYSIS")
    print("=" * 40)
    print(f"Total Executions:   {execution_stats['total_executions']}")
    print(f"Total Slippage:     ₹{execution_stats['total_slippage_cost']:.2f}")
    print(f"Total Costs:        ₹{execution_stats['total_transaction_costs']:.2f}")
    print(f"Avg Cost/Trade:     ₹{execution_stats['avg_transaction_cost_per_execution']:.2f}")
    print()
    
    # Generate detailed reports
    print("📄 Generating Detailed Reports...")
    
    reporter = BacktestReporter(results)
    
    # Save text report
    report_path = f"backtest_report_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    reporter.save_detailed_report(report_path)
    
    # Export trade data
    if results.get('trades'):
        trades_path = f"backtest_trades_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        reporter.export_trades_to_csv(trades_path)
        print(f"✅ Trade data exported to {trades_path}")
    
    # Export equity curve
    if results.get('equity_curve'):
        equity_path = f"backtest_equity_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        reporter.export_equity_curve_to_csv(equity_path)
        print(f"✅ Equity curve exported to {equity_path}")
    
    print(f"✅ Detailed report saved to {report_path}")
    print()
    
    # Generate visualizations
    try:
        import matplotlib.pyplot as plt
        
        analyzer = engine.performance_analyzer
        
        # Equity curve
        fig = analyzer.generate_equity_curve_plot(
            save_path=f"equity_curve_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        
        # Monthly returns heatmap
        heatmap_fig = analyzer.generate_monthly_returns_heatmap(
            save_path=f"monthly_returns_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        
        print("✅ Visualizations generated")
        
    except ImportError:
        print("⚠️  Matplotlib not available - skipping visualizations")
    except Exception as e:
        print(f"⚠️  Error generating visualizations: {e}")
    
    print()
    print("🎉 Backtest Complete!")
    print("=" * 60)
    
    return results


def run_simple_backtest():
    """Run a simple backtest example"""
    
    print("🚀 Running Simple Backtest Example")
    print("=" * 50)
    
    # Quick backtest configuration
    config = BacktestConfig(
        start_date=dt.datetime(2024, 1, 1),
        end_date=dt.datetime(2024, 1, 31),  # Just January
        initial_capital=50000,
        enable_slippage=True,
        enable_costs=True,
        verbose=False  # Less logging
    )
    
    # Create engine and add strategies
    engine, context = create_backtest_with_strategies(
        config=config,
        strategies=[
            (breakout_strategy, "NIFTY"),
            (credit_spread_strategy, "BANKNIFTY")
        ]
    )
    
    # Add market data
    data_provider = DataProvider()
    
    nifty_data = data_provider.get_data(256265, config.start_date, config.end_date)
    engine.add_market_data("NIFTY", nifty_data, 256265)
    
    banknifty_data = data_provider.get_data(260105, config.start_date, config.end_date)
    engine.add_market_data("BANKNIFTY", banknifty_data, 260105)
    
    # Run backtest
    with context:
        results = engine.run()
    
    # Print results
    summary = results['summary']
    print(f"Return: {summary['total_return']:.2%}")
    print(f"Trades: {summary['total_trades']}")
    print(f"Final Capital: ₹{summary['final_capital']:,.2f}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run backtesting examples")
    parser.add_argument("--simple", action="store_true", help="Run simple backtest")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive backtest")
    
    args = parser.parse_args()
    
    if args.simple:
        run_simple_backtest()
    elif args.comprehensive:
        run_comprehensive_backtest()
    else:
        # Default to comprehensive
        run_comprehensive_backtest()
