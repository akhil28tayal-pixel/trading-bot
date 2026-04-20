#!/usr/bin/env python3
"""
Trading Bot Web Dashboard
Comprehensive web interface for paper and live trading monitoring
"""

import os
import sys
import json
import datetime
import subprocess
from flask import Flask, render_template, jsonify, request
from collections import defaultdict, namedtuple

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from auth import kite, TOKEN_FILE, _calculate_token_expiry

app = Flask(__name__)

# Data structures
Trade = namedtuple('Trade', ['timestamp', 'symbol', 'action', 'quantity', 'price', 'slippage_bps', 'delay_ms', 'type', 'mode'])
PnLRecord = namedtuple('PnLRecord', ['timestamp', 'strategy', 'symbol', 'gross_pnl', 'costs', 'net_pnl', 'entry_spread', 'exit_spread', 'mode'])

class TradingDataCollector:
    def __init__(self):
        self.trades = []
        self.pnl_records = []
        self.current_positions = {}
        
    def get_trading_logs(self):
        """Fetch trading logs from EC2"""
        try:
            cmd = ['ssh', '-i', '~/Downloads/trading-bot.pem', 
                   'trader@ec2-13-211-47-122.ap-southeast-2.compute.amazonaws.com',
                   'cd /home/trader/trading_bot && tail -500 logs/main.log']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.stdout.split('\n') if result.returncode == 0 else []
        except Exception as e:
            print(f"Error fetching logs: {e}")
            return []
    
    def parse_trading_data(self, log_lines):
        """Parse trading data from log lines"""
        trades = []
        pnl_records = []
        
        # Determine trading mode from config
        mode = "PAPER" if config.PAPER_TRADING else "LIVE"
        
        for line in log_lines:
            if "ORDER EXECUTED:" in line:
                trade = self._parse_order(line, mode)
                if trade:
                    trades.append(trade)
            elif "SPREAD EXIT" in line and "Net PnL:" in line:
                pnl = self._parse_pnl(line, mode)
                if pnl:
                    pnl_records.append(pnl)
        
        return trades, pnl_records
    
    def _parse_order(self, line, mode):
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
            
            # Extract timestamp
            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            timestamp = datetime.datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S') if timestamp_match else datetime.datetime.now()
            
            return Trade(
                timestamp=timestamp,
                symbol=symbol,
                action=action,
                quantity=int(quantity),
                price=float(price),
                slippage_bps=float(slippage_match.group(1)) if slippage_match else 0,
                delay_ms=int(delay_match.group(1)) if delay_match else 0,
                type="EXECUTION",
                mode=mode
            )
        except Exception as e:
            print(f"Error parsing order: {e}")
            return None
    
    def _parse_pnl(self, line, mode):
        """Parse P&L record"""
        try:
            # Extract strategy
            strategy_match = re.search(r'(\w+) SPREAD EXIT', line)
            strategy = strategy_match.group(1) if strategy_match else "UNKNOWN"
            
            # Extract P&L values
            gross_match = re.search(r'Gross PnL: \$?([\d.]+)', line)
            costs_match = re.search(r'Total Costs: \$?([\d.]+)', line)
            net_match = re.search(r'Net PnL: \$?([\d.]+)', line)
            entry_match = re.search(r'Entry spread: ([\d.]+)', line)
            exit_match = re.search(r'Exit spread: ([\d.]+)', line)
            
            if not all([gross_match, costs_match, net_match]):
                return None
            
            # Extract timestamp
            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            timestamp = datetime.datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S') if timestamp_match else datetime.datetime.now()
            
            return PnLRecord(
                timestamp=timestamp,
                strategy=strategy,
                symbol=f"{strategy}_SPREAD",
                gross_pnl=float(gross_match.group(1)),
                costs=float(costs_match.group(1)),
                net_pnl=float(net_match.group(1)),
                entry_spread=float(entry_match.group(1)) if entry_match else 0,
                exit_spread=float(exit_match.group(1)) if exit_match else 0,
                mode=mode
            )
        except Exception as e:
            print(f"Error parsing P&L: {e}")
            return None
    
    def get_trading_summary(self, trades, pnl_records):
        """Generate trading summary statistics"""
        summary = {
            'total_trades': len(pnl_records),
            'total_orders': len(trades),
            'winning_trades': len([pnl for pnl in pnl_records if pnl.net_pnl > 0]),
            'losing_trades': len([pnl for pnl in pnl_records if pnl.net_pnl < 0]),
            'total_gross_pnl': sum(pnl.gross_pnl for pnl in pnl_records),
            'total_costs': sum(pnl.costs for pnl in pnl_records),
            'total_net_pnl': sum(pnl.net_pnl for pnl in pnl_records),
            'avg_slippage': sum(trade.slippage_bps for trade in trades) / len(trades) if trades else 0,
            'avg_delay': sum(trade.delay_ms for trade in trades) / len(trades) if trades else 0,
        }
        
        if summary['total_trades'] > 0:
            summary['win_rate'] = summary['winning_trades'] / summary['total_trades'] * 100
            summary['avg_pnl_per_trade'] = summary['total_net_pnl'] / summary['total_trades']
        else:
            summary['win_rate'] = 0
            summary['avg_pnl_per_trade'] = 0
        
        return summary

# Global data collector
data_collector = TradingDataCollector()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/trading-data')
def get_trading_data():
    """API endpoint for trading data"""
    try:
        # Get fresh data
        log_lines = data_collector.get_trading_logs()
        trades, pnl_records = data_collector.parse_trading_data(log_lines)
        
        # Separate by mode
        paper_trades = [t for t in trades if t.mode == "PAPER"]
        live_trades = [t for t in trades if t.mode == "LIVE"]
        paper_pnl = [p for p in pnl_records if p.mode == "PAPER"]
        live_pnl = [p for p in pnl_records if p.mode == "LIVE"]
        
        # Generate summaries
        paper_summary = data_collector.get_trading_summary(paper_trades, paper_pnl)
        live_summary = data_collector.get_trading_summary(live_trades, live_pnl)
        
        return jsonify({
            'paper_trading': {
                'trades': [t._asdict() for t in paper_trades[-20:]],  # Last 20 trades
                'pnl_records': [p._asdict() for p in paper_pnl[-10:]],  # Last 10 P&L records
                'summary': paper_summary
            },
            'live_trading': {
                'trades': [t._asdict() for t in live_trades[-20:]],
                'pnl_records': [p._asdict() for p in live_pnl[-10:]],
                'summary': live_summary
            },
            'last_updated': datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategy-performance')
def strategy_performance():
    """API endpoint for strategy performance data"""
    try:
        log_lines = data_collector.get_trading_logs()
        trades, pnl_records = data_collector.parse_trading_data(log_lines)
        
        # Group by strategy
        strategy_data = defaultdict(lambda: {'trades': [], 'pnl': []})
        
        for pnl in pnl_records:
            strategy_data[pnl.strategy]['pnl'].append(pnl.net_pnl)
        
        # Calculate performance metrics
        performance = {}
        for strategy, data in strategy_data.items():
            pnls = data['pnl']
            performance[strategy] = {
                'total_trades': len(pnls),
                'total_pnl': sum(pnls),
                'avg_pnl': sum(pnls) / len(pnls) if pnls else 0,
                'win_rate': len([p for p in pnls if p > 0]) / len(pnls) * 100 if pnls else 0,
                'max_win': max(pnls) if pnls else 0,
                'max_loss': min(pnls) if pnls else 0
            }
        
        return jsonify(performance)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system-status')
def system_status():
    """API endpoint for system status"""
    try:
        # Check trading mode
        mode = "PAPER" if config.PAPER_TRADING else "LIVE"
        
        # Check token validity
        token_valid = False
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, 'r') as f:
                    data = json.load(f)
                token_valid = True
            except:
                pass
        
        # Get current positions (simplified)
        positions = []
        
        return jsonify({
            'trading_mode': mode,
            'token_valid': token_valid,
            'api_key': config.API_KEY[:10] + "..." if config.API_KEY else None,
            'current_positions': positions,
            'last_updated': datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def create_templates():
    """Create HTML templates"""
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    # Main dashboard template
    dashboard_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Bot Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .status-bar {
            display: flex;
            gap: 20px;
            margin-top: 20px;
        }
        
        .status-item {
            background: #f8f9fa;
            padding: 15px 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        
        .status-item.live {
            border-left-color: #28a745;
        }
        
        .status-item.paper {
            border-left-color: #ffc107;
        }
        
        .trading-sections {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .trading-section {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .section-title {
            font-size: 1.8em;
            font-weight: 600;
        }
        
        .mode-badge {
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .mode-badge.paper {
            background: #fff3cd;
            color: #856404;
        }
        
        .mode-badge.live {
            background: #d4edda;
            color: #155724;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
        }
        
        .orders-table, .pnl-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        .orders-table th, .pnl-table th {
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        
        .orders-table td, .pnl-table td {
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .orders-table tr:hover, .pnl-table tr:hover {
            background: #f8f9fa;
        }
        
        .profit {
            color: #28a745;
            font-weight: 600;
        }
        
        .loss {
            color: #dc3545;
            font-weight: 600;
        }
        
        .chart-container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.3s;
        }
        
        .refresh-btn:hover {
            background: #5a6fd8;
        }
        
        .last-updated {
            color: #666;
            font-size: 0.9em;
            margin-top: 10px;
        }
        
        @media (max-width: 768px) {
            .trading-sections {
                grid-template-columns: 1fr;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Trading Bot Dashboard</h1>
            <div class="status-bar" id="statusBar">
                <div class="status-item">
                    <strong>Mode:</strong> <span id="tradingMode">Loading...</span>
                </div>
                <div class="status-item">
                    <strong>API Status:</strong> <span id="apiStatus">Loading...</span>
                </div>
                <div class="status-item">
                    <strong>Last Updated:</strong> <span id="lastUpdated">Loading...</span>
                </div>
            </div>
        </div>
        
        <div class="trading-sections">
            <!-- Paper Trading Section -->
            <div class="trading-section">
                <div class="section-header">
                    <h2 class="section-title">Paper Trading</h2>
                    <span class="mode-badge paper">Paper</span>
                </div>
                
                <div class="stats-grid" id="paperStats">
                    <div class="stat-card">
                        <div class="stat-value">-</div>
                        <div class="stat-label">Total Trades</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">-</div>
                        <div class="stat-label">Win Rate</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">-</div>
                        <div class="stat-label">Net P&L</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">-</div>
                        <div class="stat-label">Avg Slippage</div>
                    </div>
                </div>
                
                <h3>Recent Orders</h3>
                <table class="orders-table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Action</th>
                            <th>Symbol</th>
                            <th>Price</th>
                            <th>Slippage</th>
                        </tr>
                    </thead>
                    <tbody id="paperOrders">
                        <tr><td colspan="5">Loading...</td></tr>
                    </tbody>
                </table>
                
                <h3>Completed Trades</h3>
                <table class="pnl-table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Strategy</th>
                            <th>Gross</th>
                            <th>Costs</th>
                            <th>Net</th>
                        </tr>
                    </thead>
                    <tbody id="paperPnL">
                        <tr><td colspan="5">Loading...</td></tr>
                    </tbody>
                </table>
            </div>
            
            <!-- Live Trading Section -->
            <div class="trading-section">
                <div class="section-header">
                    <h2 class="section-title">Live Trading</h2>
                    <span class="mode-badge live">Live</span>
                </div>
                
                <div class="stats-grid" id="liveStats">
                    <div class="stat-card">
                        <div class="stat-value">-</div>
                        <div class="stat-label">Total Trades</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">-</div>
                        <div class="stat-label">Win Rate</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">-</div>
                        <div class="stat-label">Net P&L</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">-</div>
                        <div class="stat-label">Avg Slippage</div>
                    </div>
                </div>
                
                <h3>Recent Orders</h3>
                <table class="orders-table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Action</th>
                            <th>Symbol</th>
                            <th>Price</th>
                            <th>Slippage</th>
                        </tr>
                    </thead>
                    <tbody id="liveOrders">
                        <tr><td colspan="5">No live trades yet</td></tr>
                    </tbody>
                </table>
                
                <h3>Completed Trades</h3>
                <table class="pnl-table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Strategy</th>
                            <th>Gross</th>
                            <th>Costs</th>
                            <th>Net</th>
                        </tr>
                    </thead>
                    <tbody id="livePnL">
                        <tr><td colspan="5">No live trades yet</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>Strategy Performance</h2>
            <canvas id="performanceChart" width="400" height="200"></canvas>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <button class="refresh-btn" onclick="refreshData()">Refresh Data</button>
            <div class="last-updated" id="dataTimestamp">Loading...</div>
        </div>
    </div>
    
    <script>
        let performanceChart = null;
        
        function formatCurrency(amount) {
            return 'Rs ' + amount.toLocaleString('en-IN', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }
        
        function formatTime(timestamp) {
            return new Date(timestamp).toLocaleTimeString('en-IN', {
                hour: '2-digit',
                minute: '2-digit'
            });
        }
        
        function updateStats(stats, elementId) {
            const container = document.getElementById(elementId);
            const html = `
                <div class="stat-card">
                    <div class="stat-value">${stats.total_trades || 0}</div>
                    <div class="stat-label">Total Trades</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${(stats.win_rate || 0).toFixed(1)}%</div>
                    <div class="stat-label">Win Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value ${stats.total_net_pnl >= 0 ? 'profit' : 'loss'}">
                        ${formatCurrency(stats.total_net_pnl || 0)}
                    </div>
                    <div class="stat-label">Net P&L</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${(stats.avg_slippage || 0).toFixed(1)}</div>
                    <div class="stat-label">Avg Slippage (bps)</div>
                </div>
            `;
            container.innerHTML = html;
        }
        
        function updateOrders(orders, elementId) {
            const tbody = document.getElementById(elementId);
            if (orders.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5">No orders</td></tr>';
                return;
            }
            
            const html = orders.map(order => `
                <tr>
                    <td>${formatTime(order.timestamp)}</td>
                    <td>${order.action}</td>
                    <td>${order.symbol}</td>
                    <td>${formatCurrency(order.price)}</td>
                    <td>${order.slippage_bps.toFixed(1)}bps</td>
                </tr>
            `).join('');
            tbody.innerHTML = html;
        }
        
        function updatePnL(pnlRecords, elementId) {
            const tbody = document.getElementById(elementId);
            if (pnlRecords.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5">No completed trades</td></tr>';
                return;
            }
            
            const html = pnlRecords.map(pnl => `
                <tr>
                    <td>${formatTime(pnl.timestamp)}</td>
                    <td>${pnl.strategy}</td>
                    <td>${formatCurrency(pnl.gross_pnl)}</td>
                    <td>${formatCurrency(pnl.costs)}</td>
                    <td class="${pnl.net_pnl >= 0 ? 'profit' : 'loss'}">
                        ${formatCurrency(pnl.net_pnl)}
                    </td>
                </tr>
            `).join('');
            tbody.innerHTML = html;
        }
        
        function updatePerformanceChart(data) {
            const ctx = document.getElementById('performanceChart').getContext('2d');
            
            const strategies = Object.keys(data);
            const pnlData = strategies.map(s => data[s].total_pnl);
            const winRates = strategies.map(s => data[s].win_rate);
            
            if (performanceChart) {
                performanceChart.destroy();
            }
            
            performanceChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: strategies,
                    datasets: [{
                        label: 'Total P&L (Rs)',
                        data: pnlData,
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return 'Rs ' + value.toLocaleString('en-IN');
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const strategy = strategies[context.dataIndex];
                                    const data = strategyData[strategy];
                                    return [
                                        `P&L: ${formatCurrency(data.total_pnl)}`,
                                        `Win Rate: ${data.win_rate.toFixed(1)}%`,
                                        `Trades: ${data.total_trades}`
                                    ];
                                }
                            }
                        }
                    }
                }
            });
        }
        
        async function refreshData() {
            try {
                // Update system status
                const statusResponse = await fetch('/api/system-status');
                const statusData = await statusResponse.json();
                document.getElementById('tradingMode').textContent = statusData.trading_mode;
                document.getElementById('apiStatus').textContent = statusData.token_valid ? 'Connected' : 'Disconnected';
                document.getElementById('lastUpdated').textContent = new Date().toLocaleTimeString();
                
                // Update trading data
                const response = await fetch('/api/trading-data');
                const data = await response.json();
                
                // Update paper trading
                updateStats(data.paper_trading.summary, 'paperStats');
                updateOrders(data.paper_trading.trades, 'paperOrders');
                updatePnL(data.paper_trading.pnl_records, 'paperPnL');
                
                // Update live trading
                updateStats(data.live_trading.summary, 'liveStats');
                updateOrders(data.live_trading.trades, 'liveOrders');
                updatePnL(data.live_trading.pnl_records, 'livePnL');
                
                // Update timestamp
                document.getElementById('dataTimestamp').textContent = 
                    'Last updated: ' + new Date(data.last_updated).toLocaleString();
                
                // Update performance chart
                const perfResponse = await fetch('/api/strategy-performance');
                const perfData = await perfResponse.json();
                updatePerformanceChart(perfData);
                
            } catch (error) {
                console.error('Error refreshing data:', error);
            }
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
        
        // Initial load
        document.addEventListener('DOMContentLoaded', refreshData);
    </script>
</body>
</html>'''
    
    with open(os.path.join(templates_dir, 'dashboard.html'), 'w') as f:
        f.write(dashboard_html)

if __name__ == '__main__':
    # Create templates
    create_templates()
    
    # Start the server
    print("Starting Trading Bot Dashboard...")
    print("Dashboard will be available at: http://127.0.0.1:5002")
    print("Press Ctrl+C to stop")
    
    app.run(host='127.0.0.1', port=5002, debug=False, use_reloader=False)
