#!/usr/bin/env python3
"""
Demonstration of the complete backtesting engine
Shows all features working together
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datetime as dt
from backtest.engine_v2 import BacktestEngine, BacktestConfig
from backtest.data import DataProvider
from backtest.strategy_adapter import BacktestContext
from backtest.metrics import BacktestReporter


def demo_comprehensive_backtest():
    """Demonstrate comprehensive backtesting capabilities"""
    
    print("🚀 COMPREHENSIVE BACKTESTING ENGINE DEMONSTRATION")
    print("=" * 70)
    
    # Configure backtest
    config = BacktestConfig(
        start_date=dt.datetime(2026, 1, 1),
        end_date=dt.datetime(2026, 1, 15),  # 2 weeks for demo
        initial_capital=100000,
        enable_slippage=True,
        enable_delay=True,
        enable_costs=True,
        tick_frequency="1min",
        max_daily_loss=0.05,  # 5% daily loss limit
        verbose=True
    )
    
    print(f"📅 Period: {config.start_date.date()} to {config.end_date.date()}")
    print(f"💰 Capital: ₹{config.initial_capital:,}")
    print(f"⚙️  Features: Slippage ✅ | Costs ✅ | Delays ✅")
    print()
    
    # Create engine
    engine = BacktestEngine(config)
    
    # Add market data
    print("📊 Loading Market Data...")
    data_provider = DataProvider()
    
    nifty_data = data_provider.get_data(256265, config.start_date, config.end_date)
    engine.add_market_data("NIFTY", nifty_data, 256265)
    
    banknifty_data = data_provider.get_data(260105, config.start_date, config.end_date)
    engine.add_market_data("BANKNIFTY", banknifty_data, 260105)
    
    print(f"✅ NIFTY: {len(nifty_data)} bars")
    print(f"✅ BANKNIFTY: {len(banknifty_data)} bars")
    print()
    
    # Create demo trading strategy
    trade_signals = []
    
    def demo_momentum_strategy(ticks):
        """Demo momentum strategy with realistic trading logic"""
        if not ticks:
            return
            
        # Get current price
        current_price = ticks[0]['last_price']
        current_time = ticks[0].get('timestamp', dt.datetime.now())
        
        # Simple momentum logic
        if len(trade_signals) == 0:
            trade_signals.append(current_price)
            return
        
        # Calculate price change
        prev_price = trade_signals[-1]
        price_change = (current_price - prev_price) / prev_price
        
        # Trading logic
        if abs(price_change) > 0.002:  # 0.2% move
            
            if price_change > 0.002:  # Upward momentum - buy call
                print(f"📈 MOMENTUM BUY: Price moved {price_change:.2%}")
                
                try:
                    from broker import place_order_realistic
                    result = place_order_realistic(
                        symbol="NIFTY2642124350CE",
                        transaction_type="BUY",
                        quantity=50,
                        market_price=current_price * 0.05  # Simulate option price
                    )
                    print(f"   ✅ Call option bought @ ₹{result['executed_price']:.2f}")
                    
                except Exception as e:
                    print(f"   ❌ Order failed: {e}")
            
            elif price_change < -0.002:  # Downward momentum - buy put
                print(f"📉 MOMENTUM SELL: Price moved {price_change:.2%}")
                
                try:
                    from broker import place_order_realistic
                    result = place_order_realistic(
                        symbol="NIFTY2642124350PE", 
                        transaction_type="BUY",
                        quantity=50,
                        market_price=current_price * 0.04  # Simulate option price
                    )
                    print(f"   ✅ Put option bought @ ₹{result['executed_price']:.2f}")
                    
                except Exception as e:
                    print(f"   ❌ Order failed: {e}")
        
        # Update price history (keep last 10)
        trade_signals.append(current_price)
        if len(trade_signals) > 10:
            trade_signals.pop(0)
    
    # Setup and run backtest
    context = BacktestContext(engine)
    
    with context:
        # Add demo strategy
        engine.add_strategy_callback(demo_momentum_strategy)
        print("🎯 Demo momentum strategy loaded")
        print()
        
        # Run backtest
        print("🔄 Running Backtest...")
        print("   (This demonstrates realistic execution with slippage & costs)")
        print()
        
        results = engine.run()
    
    # Comprehensive results analysis
    print("\n" + "="*70)
    print("📈 BACKTEST RESULTS ANALYSIS")
    print("="*70)
    
    # Summary metrics
    summary = results['summary']
    print(f"\n💰 PORTFOLIO PERFORMANCE:")
    print(f"   Initial Capital:     ₹{summary['initial_capital']:,.2f}")
    print(f"   Final Capital:       ₹{summary['final_capital']:,.2f}")
    print(f"   Total Return:        {summary['total_return']:.2%}")
    print(f"   Absolute P&L:        ₹{summary['total_pnl']:,.2f}")
    
    # Execution analysis
    exec_stats = engine.execution_engine.get_execution_statistics()
    print(f"\n⚡ EXECUTION ANALYSIS:")
    print(f"   Total Orders:        {exec_stats['total_executions']}")
    print(f"   Slippage Cost:       ₹{exec_stats['total_slippage_cost']:.2f}")
    print(f"   Transaction Costs:   ₹{exec_stats['total_transaction_costs']:.2f}")
    print(f"   Avg Cost per Trade:  ₹{exec_stats['avg_transaction_cost_per_execution']:.2f}")
    
    # Trading statistics
    oms_stats = engine.oms.get_statistics()
    print(f"\n📊 TRADING STATISTICS:")
    print(f"   Completed Trades:    {oms_stats['total_trades']}")
    print(f"   Winning Trades:      {oms_stats.get('winning_trades', 0)}")
    print(f"   Losing Trades:       {oms_stats.get('losing_trades', 0)}")
    print(f"   Win Rate:            {oms_stats.get('win_rate', 0):.2%}")
    
    if oms_stats.get('total_trades', 0) > 0:
        print(f"   Average Win:         ₹{oms_stats.get('avg_win', 0):.2f}")
        print(f"   Average Loss:        ₹{oms_stats.get('avg_loss', 0):.2f}")
        print(f"   Profit Factor:       {oms_stats.get('profit_factor', 0):.2f}")
    
    # Performance metrics
    if results.get('performance_metrics'):
        metrics = results['performance_metrics']
        print(f"\n📈 RISK METRICS:")
        print(f"   Sharpe Ratio:        {metrics.sharpe_ratio:.2f}")
        print(f"   Max Drawdown:        {metrics.max_drawdown:.2%}")
        print(f"   Volatility:          {metrics.volatility:.2%}")
    
    # System performance
    print(f"\n🖥️  SYSTEM PERFORMANCE:")
    print(f"   Execution Time:      {summary['execution_time']:.2f} seconds")
    print(f"   Ticks Processed:     {len(nifty_data) + len(banknifty_data):,}")
    
    if summary['execution_time'] > 0:
        ticks_per_sec = (len(nifty_data) + len(banknifty_data)) / summary['execution_time']
        print(f"   Processing Speed:    {ticks_per_sec:,.0f} ticks/second")
    
    # Generate report
    print(f"\n📄 GENERATING REPORTS...")
    
    reporter = BacktestReporter(results)
    
    # Save summary report
    timestamp = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"demo_backtest_report_{timestamp}.txt"
    reporter.save_detailed_report(report_file)
    print(f"   ✅ Detailed report: {report_file}")
    
    # Export data if trades exist
    if results.get('trades'):
        trades_file = f"demo_trades_{timestamp}.csv"
        reporter.export_trades_to_csv(trades_file)
        print(f"   ✅ Trade data: {trades_file}")
    
    if results.get('equity_curve'):
        equity_file = f"demo_equity_{timestamp}.csv"
        reporter.export_equity_curve_to_csv(equity_file)
        print(f"   ✅ Equity curve: {equity_file}")
    
    print(f"\n🎉 DEMONSTRATION COMPLETE!")
    print("="*70)
    
    # Key takeaways
    print(f"\n🔑 KEY FEATURES DEMONSTRATED:")
    print(f"   ✅ Event-driven tick processing")
    print(f"   ✅ Realistic slippage simulation")
    print(f"   ✅ Comprehensive cost modeling")
    print(f"   ✅ Risk management integration")
    print(f"   ✅ Detailed performance analytics")
    print(f"   ✅ Professional reporting")
    
    return results


if __name__ == "__main__":
    demo_comprehensive_backtest()
