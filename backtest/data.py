"""
Advanced Data Handling and Tick Simulation
Converts OHLC data into realistic tick streams and fetches historical data.
"""

import datetime as dt
import random
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from kiteconnect import KiteConnect

import config
from logger import log


class TickSimulator:
    """
    Converts OHLC bars into realistic tick sequences
    Simulates intrabar price movement
    """

    def __init__(self):
        self.random_seed = 42
        random.seed(self.random_seed)
        np.random.seed(self.random_seed)

    def generate_ticks_from_ohlc(
        self,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        num_ticks: int = 10,
    ) -> List[float]:
        if num_ticks < 4:
            num_ticks = 4

        ticks = [open_price]

        if random.random() > 0.5:
            path_points = [open_price, high_price, low_price, close_price]
        else:
            path_points = [open_price, low_price, high_price, close_price]

        ticks_per_segment = (num_ticks - 1) // 3
        remaining_ticks = (num_ticks - 1) % 3

        for i in range(3):
            start_price = path_points[i]
            end_price = path_points[i + 1]

            segment_ticks = ticks_per_segment
            if i < remaining_ticks:
                segment_ticks += 1

            if segment_ticks > 0:
                segment_prices = self._generate_segment_ticks(start_price, end_price, segment_ticks)
                ticks.extend(segment_prices)

        if ticks[-1] != close_price:
            ticks.append(close_price)

        return ticks[:num_ticks]

    def _generate_segment_ticks(self, start_price: float, end_price: float, num_ticks: int) -> List[float]:
        if num_ticks == 0:
            return []
        if num_ticks == 1:
            return [end_price]

        base_prices = np.linspace(start_price, end_price, num_ticks + 1)[1:]
        price_range = abs(end_price - start_price)
        noise_factor = min(price_range * 0.1, abs(start_price) * 0.001)

        noisy_prices = []
        for price in base_prices:
            noise = np.random.normal(0, noise_factor)
            noisy_price = price + noise

            min_bound = min(start_price, end_price) - noise_factor
            max_bound = max(start_price, end_price) + noise_factor
            noisy_price = np.clip(noisy_price, min_bound, max_bound)
            noisy_prices.append(noisy_price)

        return noisy_prices

    def generate_option_ticks(
        self,
        underlying_ticks: List[float],
        strike: float,
        option_type: str,
        dte: int,
        iv: float = 0.2,
    ) -> List[float]:
        option_ticks = []
        for underlying_price in underlying_ticks:
            option_price = self._calculate_option_price(underlying_price, strike, dte, iv, option_type)
            option_ticks.append(option_price)
        return option_ticks

    def _calculate_option_price(self, spot: float, strike: float, dte: int, iv: float, option_type: str) -> float:
        time_to_expiry = max(dte / 365.0, 0.001)

        if option_type.upper() == "CE":
            intrinsic = max(spot - strike, 0)
        else:
            intrinsic = max(strike - spot, 0)

        moneyness = spot / strike
        time_value = spot * iv * np.sqrt(time_to_expiry) * 0.4

        if option_type.upper() == "CE":
            if moneyness > 1:
                time_value *= 0.7
            elif moneyness < 0.95:
                time_value *= 0.3
        else:
            if moneyness < 1:
                time_value *= 0.7
            elif moneyness > 1.05:
                time_value *= 0.3

        option_price = intrinsic + time_value
        return max(option_price, 0.05)


class DataProvider:
    """
    Provides historical market data for backtesting.
    Attempts to use real Kite historical candles first, then falls back to synthetic data.
    """

    CHUNK_DAYS = {
        "minute": 60,
        "3minute": 90,
        "5minute": 90,
        "10minute": 90,
        "15minute": 180,
        "30minute": 180,
        "60minute": 365,
        "day": 2000,
    }

    INTERVAL_ALIAS = {
        "1minute": "minute",
        "minute": "minute",
        "3minute": "3minute",
        "5minute": "5minute",
        "10minute": "10minute",
        "15minute": "15minute",
        "30minute": "30minute",
        "60minute": "60minute",
        "day": "day",
    }

    def __init__(self):
        self.data_cache = {}
        self.cache_dir = Path("data_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.instrument_cache: Optional[List[Dict]] = None

    def get_data(self, instrument_token: int, start: dt.datetime, end: dt.datetime, interval: str = "1minute") -> pd.DataFrame:
        cache_key = f"{instrument_token}_{start}_{end}_{interval}"
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]

        normalized_interval = self.INTERVAL_ALIAS.get(interval, interval)
        data = self._load_cached_real_data(instrument_token, start, end, normalized_interval)

        if data is None:
            data = self._fetch_real_data(instrument_token, start, end, normalized_interval)
            if data is not None and not data.empty:
                self._save_cached_real_data(instrument_token, start, end, normalized_interval, data)

        if data is None or data.empty:
            synthetic_interval = "1minute" if normalized_interval == "minute" else normalized_interval
            data = self._generate_synthetic_data(instrument_token, start, end, synthetic_interval)

        self.data_cache[cache_key] = data
        return data

    def _cache_path(self, instrument_token: int, start: dt.datetime, end: dt.datetime, interval: str) -> Path:
        safe_start = start.strftime("%Y%m%d")
        safe_end = end.strftime("%Y%m%d")
        return self.cache_dir / f"{instrument_token}_{interval}_{safe_start}_{safe_end}.csv"

    def _load_cached_real_data(self, instrument_token: int, start: dt.datetime, end: dt.datetime, interval: str):
        path = self._cache_path(instrument_token, start, end, interval)
        if not path.exists():
            return None

        try:
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            if getattr(df.index, "tz", None) is not None:
                df.index = df.index.tz_localize(None)
            if not df.empty:
                log(f"Loaded cached real data for token {instrument_token} from {path}")
                return df
        except Exception as exc:
            log(f"Failed to load cached data {path}: {exc}")

        return None

    def _save_cached_real_data(self, instrument_token: int, start: dt.datetime, end: dt.datetime, interval: str, df: pd.DataFrame):
        path = self._cache_path(instrument_token, start, end, interval)
        try:
            df.to_csv(path)
            log(f"Cached real data for token {instrument_token} at {path}")
        except Exception as exc:
            log(f"Failed to cache real data to {path}: {exc}")

    def _get_kite_client(self):
        if not config.API_KEY or not config.API_SECRET:
            return None

        access_token = getattr(config, "ACCESS_TOKEN", "") or None
        if not access_token:
            token_file = Path("token.json")
            if token_file.exists():
                try:
                    import json

                    token_data = json.loads(token_file.read_text())
                    if token_data.get("date") == str(dt.date.today()):
                        access_token = token_data.get("access_token")
                        config.ACCESS_TOKEN = access_token or ""
                except Exception as exc:
                    log(f"Failed to read token.json: {exc}")

        if not access_token:
            return None

        try:
            kite = KiteConnect(api_key=config.API_KEY)
            kite.set_access_token(access_token)
            return kite
        except Exception as exc:
            log(f"Failed to initialize Kite client for historical data: {exc}")
            return None

    def get_instruments(self, exchange: str = "NFO") -> List[Dict]:
        if self.instrument_cache is not None and exchange == "NFO":
            return self.instrument_cache

        kite = self._get_kite_client()
        if kite is None:
            raise ValueError("Kite credentials are required for real historical option data")

        instruments = kite.instruments(exchange)
        if exchange == "NFO":
            self.instrument_cache = instruments
        return instruments

    def get_nearest_expiry(self, underlying: str, reference_date: dt.datetime) -> dt.date:
        instruments = self.get_instruments("NFO")
        expiries = sorted(
            {
                instrument["expiry"]
                for instrument in instruments
                if instrument.get("name") == underlying and instrument.get("instrument_type") in {"CE", "PE"}
                and instrument["expiry"] >= reference_date.date()
            }
        )
        if not expiries:
            raise ValueError(f"No option expiry found for {underlying} on or after {reference_date.date()}")
        return expiries[0]

    def find_option_contract(
        self,
        underlying: str,
        strike: int,
        option_type: str,
        expiry: dt.date,
    ) -> Dict:
        instruments = self.get_instruments("NFO")
        for instrument in instruments:
            if (
                instrument.get("name") == underlying
                and instrument.get("instrument_type") == option_type
                and int(instrument.get("strike", 0)) == int(strike)
                and instrument.get("expiry") == expiry
            ):
                return instrument

        raise ValueError(f"No {underlying} {strike} {option_type} contract found for expiry {expiry}")

    def _fetch_real_data(self, instrument_token: int, start: dt.datetime, end: dt.datetime, interval: str) -> pd.DataFrame | None:
        kite = self._get_kite_client()
        if kite is None:
            log(f"Real data unavailable for token {instrument_token}: Kite credentials not ready")
            return None

        chunk_days = self.CHUNK_DAYS.get(interval, 60)
        current_start = start
        frames = []

        try:
            while current_start <= end:
                current_end = min(current_start + dt.timedelta(days=chunk_days - 1), end)
                candles = kite.historical_data(
                    instrument_token=instrument_token,
                    from_date=current_start,
                    to_date=current_end,
                    interval=interval,
                    continuous=False,
                    oi=False,
                )

                if candles:
                    frame = pd.DataFrame(candles)
                    frame["date"] = pd.to_datetime(frame["date"])
                    if getattr(frame["date"].dt, "tz", None) is not None:
                        frame["date"] = frame["date"].dt.tz_localize(None)
                    frame = frame.set_index("date")
                    frames.append(frame[["open", "high", "low", "close", "volume"]])

                current_start = current_end + dt.timedelta(days=1)

            if not frames:
                log(f"Kite returned no historical candles for token {instrument_token}")
                return None

            df = pd.concat(frames).sort_index()
            df = df[~df.index.duplicated(keep="last")]
            log(f"Fetched {len(df)} real bars from Kite for token {instrument_token}")
            return df
        except Exception as exc:
            log(f"Failed to fetch real historical data for token {instrument_token}: {exc}")
            return None

    def _generate_synthetic_data(self, instrument_token: int, start: dt.datetime, end: dt.datetime, interval: str) -> pd.DataFrame:
        if interval == "1minute":
            freq = "1min"
        elif interval == "5minute":
            freq = "5min"
        else:
            freq = "1min"

        dates = pd.date_range(start, end, freq=freq)

        market_dates = []
        for date in dates:
            if date.weekday() >= 5:
                continue
            if 9 <= date.hour < 15 or (date.hour == 15 and date.minute <= 30):
                if date.hour >= 9 and (date.hour > 9 or date.minute >= 15):
                    market_dates.append(date)

        if not market_dates:
            return pd.DataFrame()

        if instrument_token == 256265:
            base_price = 24000
            volatility = 0.015
        elif instrument_token == 260105:
            base_price = 56000
            volatility = 0.02
        else:
            base_price = 100
            volatility = 0.3

        returns = np.random.normal(0, volatility / np.sqrt(252 * 375), len(market_dates))
        trend = np.linspace(0, 0.05, len(market_dates))
        mean_reversion = -0.1 * np.cumsum(returns)
        adjusted_returns = returns + trend / len(market_dates) + mean_reversion / 1000
        prices = base_price * np.exp(np.cumsum(adjusted_returns))

        ohlc_data = []
        for i, price in enumerate(prices):
            intrabar_vol = volatility * 0.3
            high = price * (1 + abs(np.random.normal(0, intrabar_vol)))
            low = price * (1 - abs(np.random.normal(0, intrabar_vol)))
            open_price = prices[i - 1] if i > 0 else price
            close_price = price
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            volume = int(np.random.lognormal(10, 1))

            ohlc_data.append(
                {
                    "open": round(open_price, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "close": round(close_price, 2),
                    "volume": volume,
                }
            )

        df = pd.DataFrame(ohlc_data, index=market_dates)
        log(f"Generated {len(df)} bars of synthetic data for token {instrument_token}")
        return df

    def get_option_chain_data(self, underlying_token: int, expiry_date: dt.date, strikes: List[float]) -> Dict[str, pd.DataFrame]:
        return {}


def get_data(instrument_token: int, start: dt.datetime, end: dt.datetime) -> pd.DataFrame:
    provider = DataProvider()
    return provider.get_data(instrument_token, start, end)
