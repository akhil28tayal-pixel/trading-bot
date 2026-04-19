"""
Performance Metrics and Analysis for Backtesting
Comprehensive trading performance evaluation
"""

import pandas as pd
import numpy as np
import datetime as dt
from typing import Dict, List, Any, Optional, Tuple
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from dataclasses import dataclass
from logger import log


@dataclass
class PerformanceMetrics:
    """Container for all performance metrics"""
    # Returns
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    
    # Risk metrics
    max_drawdown: float
    max_drawdown_duration: int
    var_95: float  # Value at Risk
    cvar_95: float  # Conditional Value at Risk
    
    # Trade metrics
    total_trades: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    
    # Consistency metrics
    calmar_ratio: float
    recovery_factor: float
    expectancy: float
    
    # Cost analysis
    total_costs: float
    cost_impact_percent: float
    avg_slippage_bps: float


class PerformanceAnalyzer:
    """
    Comprehensive performance analysis for backtesting results
    """
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.equity_points = []
        self.daily_returns = []
        self.drawdown_series = []
        
    def add_equity_point(self, equity_point: Dict):
        """Add equity point for analysis"""
        self.equity_points.append(equity_point)
        
        # Calculate daily return
        if len(self.equity_points) > 1:
            prev_equity = self.equity_points[-2]['equity']
            current_equity = equity_point['equity']
            daily_return = (current_equity - prev_equity) / prev_equity
            self.daily_returns.append(daily_return)
    
    def calculate_metrics(self) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        if len(self.equity_points) < 2:
            return self._empty_metrics()
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(self.equity_points)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Basic return calculations
        final_equity = df['equity'].iloc[-1]
        total_return = (final_equity - self.initial_capital) / self.initial_capital
        
        # Time-based calculations
        start_date = df.index[0]
        end_date = df.index[-1]
        days = (end_date - start_date).days
        years = days / 365.25
        
        annualized_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
        
        # Volatility calculations
        returns = df['equity'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # Annualized
        
        # Risk-adjusted returns
        risk_free_rate = 0.06  # Assume 6% risk-free rate
        excess_returns = returns - risk_free_rate/252
        sharpe_ratio = excess_returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        
        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252)
        sortino_ratio = (annualized_return - risk_free_rate) / downside_std if downside_std > 0 else 0
        
        # Drawdown analysis
        running_max = df['equity'].expanding().max()
        drawdown = (df['equity'] - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Max drawdown duration
        drawdown_duration = self._calculate_max_drawdown_duration(drawdown)
        
        # Value at Risk
        var_95 = np.percentile(returns, 5)
        cvar_95 = returns[returns <= var_95].mean()
        
        # Trade-based metrics (these would come from trade history)
        trade_metrics = self._calculate_trade_metrics()
        
        # Additional risk metrics
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        recovery_factor = total_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_duration=drawdown_duration,
            var_95=var_95,
            cvar_95=cvar_95,
            total_trades=trade_metrics['total_trades'],
            win_rate=trade_metrics['win_rate'],
            profit_factor=trade_metrics['profit_factor'],
            avg_win=trade_metrics['avg_win'],
            avg_loss=trade_metrics['avg_loss'],
            largest_win=trade_metrics['largest_win'],
            largest_loss=trade_metrics['largest_loss'],
            calmar_ratio=calmar_ratio,
            recovery_factor=recovery_factor,
            expectancy=trade_metrics['expectancy'],
            total_costs=trade_metrics['total_costs'],
            cost_impact_percent=trade_metrics['cost_impact_percent'],
            avg_slippage_bps=trade_metrics['avg_slippage_bps']
        )
    
    def _calculate_max_drawdown_duration(self, drawdown_series: pd.Series) -> int:
        """Calculate maximum drawdown duration in days"""
        in_drawdown = drawdown_series < 0
        drawdown_periods = []
        current_period = 0
        
        for is_dd in in_drawdown:
            if is_dd:
                current_period += 1
            else:
                if current_period > 0:
                    drawdown_periods.append(current_period)
                current_period = 0
        
        # Add final period if still in drawdown
        if current_period > 0:
            drawdown_periods.append(current_period)
        
        return max(drawdown_periods) if drawdown_periods else 0
    
    def _calculate_trade_metrics(self) -> Dict[str, float]:
        """Calculate trade-based metrics (placeholder - would use actual trade data)"""
        # This would be populated from actual trade history
        return {
            'total_trades': 0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
            'expectancy': 0.0,
            'total_costs': 0.0,
            'cost_impact_percent': 0.0,
            'avg_slippage_bps': 0.0
        }
    
    def _empty_metrics(self) -> PerformanceMetrics:
        """Return empty metrics for insufficient data"""
        return PerformanceMetrics(
            total_return=0.0, annualized_return=0.0, volatility=0.0,
            sharpe_ratio=0.0, sortino_ratio=0.0, max_drawdown=0.0,
            max_drawdown_duration=0, var_95=0.0, cvar_95=0.0,
            total_trades=0, win_rate=0.0, profit_factor=0.0,
            avg_win=0.0, avg_loss=0.0, largest_win=0.0, largest_loss=0.0,
            calmar_ratio=0.0, recovery_factor=0.0, expectancy=0.0,
            total_costs=0.0, cost_impact_percent=0.0, avg_slippage_bps=0.0
        )
    
    def generate_equity_curve_plot(self, save_path: Optional[str] = None) -> plt.Figure:
        """Generate equity curve visualization"""
        if len(self.equity_points) < 2:
            log("Insufficient data for equity curve plot")
            return None
        
        df = pd.DataFrame(self.equity_points)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Equity curve
        ax1.plot(df['timestamp'], df['equity'], linewidth=2, color='blue', label='Portfolio Value')
        ax1.axhline(y=self.initial_capital, color='red', linestyle='--', alpha=0.7, label='Initial Capital')
        ax1.set_title('Portfolio Equity Curve', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Portfolio Value (₹)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Format x-axis
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # Drawdown
        running_max = df['equity'].expanding().max()
        drawdown = (df['equity'] - running_max) / running_max * 100
        
        ax2.fill_between(df['timestamp'], drawdown, 0, alpha=0.3, color='red')
        ax2.plot(df['timestamp'], drawdown, color='red', linewidth=1)
        ax2.set_title('Drawdown (%)', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Drawdown (%)')
        ax2.set_xlabel('Date')
        ax2.grid(True, alpha=0.3)
        
        # Format x-axis
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax2.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            log(f"Equity curve saved to {save_path}")
        
        return fig
    
    def generate_monthly_returns_heatmap(self, save_path: Optional[str] = None) -> plt.Figure:
        """Generate monthly returns heatmap"""
        if len(self.equity_points) < 30:  # Need at least a month of data
            log("Insufficient data for monthly returns heatmap")
            return None
        
        df = pd.DataFrame(self.equity_points)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Calculate daily returns
        df['returns'] = df['equity'].pct_change()
        
        # Resample to monthly returns
        monthly_returns = df['returns'].resample('M').apply(lambda x: (1 + x).prod() - 1)
        
        # Create pivot table for heatmap
        monthly_returns.index = pd.to_datetime(monthly_returns.index)
        monthly_returns_df = pd.DataFrame({
            'Year': monthly_returns.index.year,
            'Month': monthly_returns.index.month,
            'Returns': monthly_returns.values * 100  # Convert to percentage
        })
        
        pivot_table = monthly_returns_df.pivot(index='Year', columns='Month', values='Returns')
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Use a diverging colormap
        im = ax.imshow(pivot_table.values, cmap='RdYlGn', aspect='auto')
        
        # Set ticks and labels
        ax.set_xticks(range(len(pivot_table.columns)))
        ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
        ax.set_yticks(range(len(pivot_table.index)))
        ax.set_yticklabels(pivot_table.index)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Monthly Returns (%)', rotation=270, labelpad=20)
        
        # Add text annotations
        for i in range(len(pivot_table.index)):
            for j in range(len(pivot_table.columns)):
                value = pivot_table.iloc[i, j]
                if not np.isnan(value):
                    text = ax.text(j, i, f'{value:.1f}%', ha='center', va='center',
                                 color='white' if abs(value) > 5 else 'black', fontweight='bold')
        
        ax.set_title('Monthly Returns Heatmap', fontsize=14, fontweight='bold')
        ax.set_xlabel('Month')
        ax.set_ylabel('Year')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            log(f"Monthly returns heatmap saved to {save_path}")
        
        return fig


class BacktestReporter:
    """
    Comprehensive backtest reporting
    """
    
    def __init__(self, backtest_results: Dict[str, Any]):
        self.results = backtest_results
        self.metrics = backtest_results.get('performance_metrics')
        self.trades = backtest_results.get('trades', [])
        self.equity_curve = backtest_results.get('equity_curve', [])
    
    def generate_summary_report(self) -> str:
        """Generate a comprehensive text summary report"""
        summary = backtest_results.get('summary', {})
        
        report = f"""
{'='*60}
BACKTESTING RESULTS SUMMARY
{'='*60}

PORTFOLIO PERFORMANCE:
  Initial Capital:     ₹{summary.get('initial_capital', 0):,.2f}
  Final Capital:       ₹{summary.get('final_capital', 0):,.2f}
  Total Return:        {summary.get('total_return', 0):.2%}
  Total P&L:           ₹{summary.get('total_pnl', 0):,.2f}

RISK METRICS:
  Max Drawdown:        {self.metrics.max_drawdown:.2%} if self.metrics else 'N/A'
  Volatility:          {self.metrics.volatility:.2%} if self.metrics else 'N/A'
  Sharpe Ratio:        {self.metrics.sharpe_ratio:.2f} if self.metrics else 'N/A'
  Sortino Ratio:       {self.metrics.sortino_ratio:.2f} if self.metrics else 'N/A'

TRADING STATISTICS:
  Total Trades:        {summary.get('total_trades', 0)}
  Win Rate:            {self.metrics.win_rate:.2%} if self.metrics else 'N/A'
  Profit Factor:       {self.metrics.profit_factor:.2f} if self.metrics else 'N/A'
  Average Win:         ₹{self.metrics.avg_win:.2f} if self.metrics else 'N/A'
  Average Loss:        ₹{self.metrics.avg_loss:.2f} if self.metrics else 'N/A'

EXECUTION ANALYSIS:
  Total Costs:         ₹{self.metrics.total_costs:.2f} if self.metrics else 'N/A'
  Cost Impact:         {self.metrics.cost_impact_percent:.2%} if self.metrics else 'N/A'
  Avg Slippage:        {self.metrics.avg_slippage_bps:.1f}bps if self.metrics else 'N/A'

BACKTEST SETTINGS:
  Start Date:          {self.results.get('config', {}).start_date}
  End Date:            {self.results.get('config', {}).end_date}
  Execution Time:      {summary.get('execution_time', 0):.2f} seconds

{'='*60}
        """
        
        return report
    
    def save_detailed_report(self, filepath: str):
        """Save detailed report to file"""
        with open(filepath, 'w') as f:
            f.write(self.generate_summary_report())
            
            # Add trade details if available
            if self.trades:
                f.write("\n\nDETAILED TRADE HISTORY:\n")
                f.write("-" * 80 + "\n")
                
                for i, trade in enumerate(self.trades[:50], 1):  # Limit to first 50 trades
                    f.write(f"Trade {i}: {trade.side.value} {trade.quantity} {trade.symbol}\n")
                    f.write(f"  Entry: ₹{trade.entry_price:.2f} @ {trade.entry_timestamp}\n")
                    f.write(f"  Exit:  ₹{trade.exit_price:.2f} @ {trade.exit_timestamp}\n")
                    f.write(f"  P&L:   ₹{trade.net_pnl:.2f} (Gross: ₹{trade.gross_pnl:.2f}, Costs: ₹{trade.costs:.2f})\n")
                    f.write("-" * 40 + "\n")
        
        log(f"Detailed report saved to {filepath}")
    
    def export_trades_to_csv(self, filepath: str):
        """Export trade history to CSV"""
        if not self.trades:
            log("No trades to export")
            return
        
        trade_data = []
        for trade in self.trades:
            trade_data.append({
                'trade_id': trade.trade_id,
                'symbol': trade.symbol,
                'side': trade.side.value,
                'quantity': trade.quantity,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'entry_timestamp': trade.entry_timestamp,
                'exit_timestamp': trade.exit_timestamp,
                'gross_pnl': trade.gross_pnl,
                'costs': trade.costs,
                'net_pnl': trade.net_pnl,
                'slippage_bps': trade.slippage_bps
            })
        
        df = pd.DataFrame(trade_data)
        df.to_csv(filepath, index=False)
        log(f"Trade history exported to {filepath}")
    
    def export_equity_curve_to_csv(self, filepath: str):
        """Export equity curve to CSV"""
        if not self.equity_curve:
            log("No equity curve data to export")
            return
        
        df = pd.DataFrame(self.equity_curve)
        df.to_csv(filepath, index=False)
        log(f"Equity curve exported to {filepath}")
