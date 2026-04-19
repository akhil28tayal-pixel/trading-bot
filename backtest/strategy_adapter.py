"""
Strategy Adapter for Backtesting
Allows existing live trading strategies to work seamlessly in backtesting
"""

import datetime as dt
from typing import Dict, List, Any, Callable
from .execution import BacktestBrokerInterface
from .data import DataProvider
from logger import log
import config
import strategies.breakout_ws as breakout_strategy
import strategies.credit_spread_ws as credit_spread_strategy


class BacktestStrategyAdapter:
    """
    Adapter that makes existing strategies work in backtesting
    Replaces live components with backtest equivalents
    """
    
    def __init__(self, backtest_engine):
        self.backtest_engine = backtest_engine
        self.broker_interface = BacktestBrokerInterface(backtest_engine)
        
        # Store original functions to restore later
        self.original_functions = {}
        
        # Strategy state (shared with live strategies)
        self.strategy_states = {}
        
    def setup_backtest_environment(self):
        """
        Replace live trading functions with backtest equivalents
        This allows existing strategy code to work unchanged
        """
        # Replace broker functions
        import broker
        
        # Store originals
        self.original_functions['place_order'] = getattr(broker, 'place_order', None)
        self.original_functions['place_order_realistic'] = getattr(broker, 'place_order_realistic', None)
        self.original_functions['get_ltp'] = getattr(broker, 'get_ltp', None)
        
        # Replace with backtest versions
        broker.place_order = self._backtest_place_order
        broker.place_order_realistic = self._backtest_place_order_realistic
        broker.get_ltp = self._backtest_get_ltp

        # Patch strategy-level direct imports so backtests hit the OMS instead of the live broker shim.
        self.original_functions["breakout_place_order"] = getattr(breakout_strategy, "place_order", None)
        self.original_functions["breakout_place_order_realistic"] = getattr(breakout_strategy, "place_order_realistic", None)
        self.original_functions["credit_place_order"] = getattr(credit_spread_strategy, "place_order", None)
        self.original_functions["credit_place_order_realistic"] = getattr(credit_spread_strategy, "place_order_realistic", None)

        breakout_strategy.place_order = self._backtest_place_order
        breakout_strategy.place_order_realistic = self._backtest_place_order_realistic
        credit_spread_strategy.place_order = self._backtest_place_order
        credit_spread_strategy.place_order_realistic = self._backtest_place_order_realistic
        
        # Replace config values for backtesting if needed
        self.original_functions['PAPER_TRADING'] = config.PAPER_TRADING
        config.PAPER_TRADING = True  # Always paper trading in backtest
        
        log("Backtest environment setup complete - strategies will use simulated execution")
    
    def restore_live_environment(self):
        """Restore original live trading functions"""
        import broker
        
        # Restore broker functions
        if self.original_functions.get('place_order'):
            broker.place_order = self.original_functions['place_order']
        if self.original_functions.get('place_order_realistic'):
            broker.place_order_realistic = self.original_functions['place_order_realistic']
        if self.original_functions.get('get_ltp'):
            broker.get_ltp = self.original_functions['get_ltp']

        if self.original_functions.get("breakout_place_order"):
            breakout_strategy.place_order = self.original_functions["breakout_place_order"]
        if self.original_functions.get("breakout_place_order_realistic"):
            breakout_strategy.place_order_realistic = self.original_functions["breakout_place_order_realistic"]
        if self.original_functions.get("credit_place_order"):
            credit_spread_strategy.place_order = self.original_functions["credit_place_order"]
        if self.original_functions.get("credit_place_order_realistic"):
            credit_spread_strategy.place_order_realistic = self.original_functions["credit_place_order_realistic"]
        
        # Restore config
        config.PAPER_TRADING = self.original_functions.get('PAPER_TRADING', True)
        
        log("Live environment restored")
    
    def _backtest_place_order(self, symbol: str, transaction_type: str, quantity: int, 
                             market_price: float = None) -> Dict[str, Any]:
        """Backtest version of place_order"""
        if market_price is None:
            market_price = self.broker_interface.get_ltp(symbol)
        
        return self.broker_interface.place_order(symbol, transaction_type, quantity, market_price)
    
    def _backtest_place_order_realistic(self, symbol: str, transaction_type: str, quantity: int,
                                       market_price: float, volatility_data=None) -> Dict[str, Any]:
        """Backtest version of place_order_realistic"""
        return self.broker_interface.place_order_realistic(
            symbol, transaction_type, quantity, market_price, volatility_data
        )
    
    def _backtest_get_ltp(self, symbol: str) -> float:
        """Backtest version of get_ltp"""
        return self.broker_interface.get_ltp(symbol)
    
    def get_strategy_data_for_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Get strategy-specific data for a symbol
        This would be populated with option tokens, strikes, etc.
        """
        # This is a simplified version - in production you'd have proper option chain data
        if symbol == "NIFTY":
            return {
                "ce_symbol": "NIFTY2642124350CE",
                "pe_symbol": "NIFTY2642124350PE", 
                "ce_token": 256265,  # Simplified - would be actual option token
                "pe_token": 256265,
                "strike": 24350
            }
        elif symbol == "BANKNIFTY":
            return {
                "ce_symbol": "BANKNIFTY2642156600CE",
                "pe_symbol": "BANKNIFTY2642156600PE",
                "ce_token": 260105,  # Simplified - would be actual option token
                "pe_token": 260105,
                "strike": 56600
            }
        
        return {}

    def reset_strategy_state(self, strategy_module, symbol: str):
        """Reset module-level strategy state between runs to avoid cross-run contamination."""
        if strategy_module is breakout_strategy:
            if hasattr(strategy_module, "state"):
                strategy_module.state[symbol] = {"active": False}
            if hasattr(strategy_module, "orb_data"):
                strategy_module.orb_data[symbol] = {"high": None, "low": None, "prices": []}
            if hasattr(strategy_module, "ema_data"):
                strategy_module.ema_data[symbol] = []
        elif strategy_module is credit_spread_strategy:
            if hasattr(strategy_module, "state"):
                strategy_module.state[symbol] = {"active": False}
    
    def create_strategy_wrapper(self, strategy_function: Callable, symbol: str) -> Callable:
        """
        Create a wrapper for strategy functions that provides necessary data
        
        Args:
            strategy_function: The strategy's process_ticks function
            symbol: Symbol this strategy trades
            
        Returns:
            Wrapped function that can be called with just ticks
        """
        def wrapped_strategy(ticks: List[Dict]):
            # Call the original strategy function with the same signature as live trading
            try:
                strategy_data = self.data_provider.get_strategy_data(symbol)
                if strategy_function.__module__ == breakout_strategy.__name__:
                    payload = strategy_data["breakout"]
                else:
                    payload = strategy_data
                strategy_function(ticks, symbol, payload)
            except Exception as e:
                log(f"Error in strategy {strategy_function.__name__} for {symbol}: {e}")
        
        return wrapped_strategy


class BacktestDataProvider:
    """
    Provides market data to strategies in the same format as live trading
    """
    
    def __init__(self, backtest_engine):
        self.backtest_engine = backtest_engine
        self.current_prices = {}
        self.data_provider = DataProvider()
        self.strategy_cache: Dict[tuple, Dict[str, Any]] = {}
    
    def update_current_prices(self, ticks: List[Dict]):
        """Update current price cache from ticks"""
        for tick in ticks:
            self.current_prices[tick['instrument_token']] = tick['last_price']

    def get_option_tokens(self, symbol: str) -> Dict[str, Any]:
        return self.get_strategy_data(symbol)["breakout"]

    def get_credit_spread(self, symbol: str, direction: str = "CALL") -> Dict[str, Any]:
        strategy_data = self.get_strategy_data(symbol)
        return strategy_data["spread_call"] if direction.upper() == "CALL" else strategy_data["spread_put"]

    def get_strategy_data(self, symbol: str) -> Dict[str, Any]:
        cache_key = (symbol, self.backtest_engine.config.start_date.date(), self.backtest_engine.config.end_date.date())
        if cache_key in self.strategy_cache:
            return self.strategy_cache[cache_key]

        underlying_token = 256265 if symbol == "NIFTY" else 260105
        strike_step = 50 if symbol == "NIFTY" else 100

        underlying_data = self.backtest_engine.market_data.get(symbol)
        if underlying_data is None or underlying_data.empty:
            underlying_data = self.data_provider.get_data(
                underlying_token,
                self.backtest_engine.config.start_date,
                self.backtest_engine.config.end_date,
                "1minute",
            )
            self.backtest_engine.add_market_data(symbol, underlying_data, underlying_token)

        spot_price = float(underlying_data.iloc[0]["close"])
        atm_strike = int(round(spot_price / strike_step) * strike_step)
        expiry = self.data_provider.get_nearest_expiry(symbol, self.backtest_engine.config.start_date)

        ce_contract = self.data_provider.find_option_contract(symbol, atm_strike, "CE", expiry)
        pe_contract = self.data_provider.find_option_contract(symbol, atm_strike, "PE", expiry)

        breakout = {
            "underlying": symbol,
            "expiry": expiry,
            "spot_price": spot_price,
            "strike": atm_strike,
            "ce_symbol": ce_contract["tradingsymbol"],
            "pe_symbol": pe_contract["tradingsymbol"],
            "ce_token": int(ce_contract["instrument_token"]),
            "pe_token": int(pe_contract["instrument_token"]),
        }
        self._ensure_market_data_loaded(breakout["ce_symbol"], breakout["ce_token"])
        self._ensure_market_data_loaded(breakout["pe_symbol"], breakout["pe_token"])

        strategy_data = {
            "breakout": breakout,
            "spread_call": self._build_spread(symbol, expiry, atm_strike, "CALL", strike_step),
            "spread_put": self._build_spread(symbol, expiry, atm_strike, "PUT", strike_step),
        }
        self.strategy_cache[cache_key] = strategy_data
        return strategy_data

    def _build_spread(self, symbol: str, expiry, atm_strike: int, direction: str, strike_step: int) -> Dict[str, Any]:
        if direction == "CALL":
            sell_strike = atm_strike + strike_step
            buy_strike = sell_strike + strike_step
            option_type = "CE"
        else:
            sell_strike = atm_strike - strike_step
            buy_strike = sell_strike - strike_step
            option_type = "PE"

        sell_contract = self.data_provider.find_option_contract(symbol, sell_strike, option_type, expiry)
        buy_contract = self.data_provider.find_option_contract(symbol, buy_strike, option_type, expiry)

        spread = {
            "underlying": symbol,
            "expiry": expiry,
            "direction": direction,
            "sell_symbol": sell_contract["tradingsymbol"],
            "buy_symbol": buy_contract["tradingsymbol"],
            "sell_token": int(sell_contract["instrument_token"]),
            "buy_token": int(buy_contract["instrument_token"]),
            "sell_strike": sell_strike,
            "buy_strike": buy_strike,
        }
        self._ensure_market_data_loaded(spread["sell_symbol"], spread["sell_token"])
        self._ensure_market_data_loaded(spread["buy_symbol"], spread["buy_token"])
        return spread

    def _ensure_market_data_loaded(self, symbol: str, token: int):
        if symbol in self.backtest_engine.market_data:
            return

        data = self.data_provider.get_data(
            token,
            self.backtest_engine.config.start_date,
            self.backtest_engine.config.end_date,
            "1minute",
        )
        self.backtest_engine.add_market_data(symbol, data, token)


class BacktestContext:
    """
    Context manager for backtesting that handles setup and cleanup
    """
    
    def __init__(self, backtest_engine):
        self.backtest_engine = backtest_engine
        self.adapter = BacktestStrategyAdapter(backtest_engine)
        self.data_provider = BacktestDataProvider(backtest_engine)
        self.adapter.data_provider = self.data_provider
        
    def __enter__(self):
        """Setup backtest environment"""
        self.adapter.setup_backtest_environment()
        
        # Make data provider functions available globally
        import utils.instruments as instruments
        
        # Store originals
        self.original_get_option_tokens = getattr(instruments, 'get_option_tokens', None)
        self.original_get_credit_spread = getattr(instruments, 'get_credit_spread', None)
        
        # Replace with backtest versions
        instruments.get_option_tokens = self.data_provider.get_option_tokens
        instruments.get_credit_spread = self.data_provider.get_credit_spread
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup backtest environment"""
        self.adapter.restore_live_environment()
        
        # Restore instrument functions
        import utils.instruments as instruments
        
        if self.original_get_option_tokens:
            instruments.get_option_tokens = self.original_get_option_tokens
        if self.original_get_credit_spread:
            instruments.get_credit_spread = self.original_get_credit_spread
    
    def add_strategy(self, strategy_module, symbol: str):
        """
        Add a strategy to the backtest
        
        Args:
            strategy_module: The strategy module (e.g., breakout_ws, credit_spread_ws)
            symbol: Symbol to trade
        """
        # Get the process_ticks function from the strategy
        if hasattr(strategy_module, 'process_ticks'):
            self.adapter.reset_strategy_state(strategy_module, symbol)
            strategy_function = strategy_module.process_ticks
            
            # Create wrapper that provides the right data format
            wrapped_strategy = self.adapter.create_strategy_wrapper(strategy_function, symbol)
            
            # Add to backtest engine
            self.backtest_engine.add_strategy_callback(wrapped_strategy)
            
            log(f"Added strategy {strategy_module.__name__} for {symbol}")
        else:
            log(f"Warning: Strategy module {strategy_module.__name__} has no process_ticks function")


def create_backtest_with_strategies(config, strategies: List[tuple]) -> 'BacktestEngine':
    """
    Create a backtest engine with strategies configured
    
    Args:
        config: BacktestConfig object
        strategies: List of (strategy_module, symbol) tuples
        
    Returns:
        Configured BacktestEngine
    """
    from .engine_v2 import BacktestEngine
    
    # Create engine
    engine = BacktestEngine(config)
    
    # Setup context
    context = BacktestContext(engine)
    
    # Add strategies
    with context:
        for strategy_module, symbol in strategies:
            context.add_strategy(strategy_module, symbol)
    
    return engine, context
