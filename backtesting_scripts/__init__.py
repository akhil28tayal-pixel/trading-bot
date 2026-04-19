"""
Backtesting Scripts Package
Contains all backtesting examples, tests, and demonstrations
"""

# Import main backtesting functions for easy access
from .run_backtest_v2 import run_comprehensive_backtest, run_simple_backtest
from .WORKING_BACKTEST_DEMO import run_guaranteed_working_backtest
from .test_backtest_system import run_all_tests

__all__ = [
    'run_comprehensive_backtest',
    'run_simple_backtest', 
    'run_guaranteed_working_backtest',
    'run_all_tests'
]
