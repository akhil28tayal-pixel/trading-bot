import os


def _load_dotenv(path=".env"):
    """Load simple KEY=VALUE pairs from a local .env file if present."""
    if not os.path.exists(path):
        return

    try:
        with open(path, "r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)
    except OSError:
        pass


_load_dotenv()


def _get_env(name, default=None, cast=str):
    value = os.getenv(name)
    if value is None or value == "":
        return default

    if cast is bool:
        return value.strip().lower() in {"1", "true", "yes", "on"}

    if cast is int:
        return int(value)

    if cast is float:
        return float(value)

    return value


API_KEY = _get_env("KITE_API_KEY", "")
API_SECRET = _get_env("KITE_API_SECRET", "")
ACCESS_TOKEN = _get_env("KITE_ACCESS_TOKEN", "")

CAPITAL = _get_env("TRADING_CAPITAL", 100000, int)
RISK_PER_TRADE = _get_env("RISK_PER_TRADE", 0.01, float)   # 1%
DAILY_LOSS_LIMIT = _get_env("DAILY_LOSS_LIMIT", 0.03, float)

MODE = _get_env("TRADING_MODE", "PAPER").upper()
# options: LIVE / PAPER / BACKTEST

PAPER_TRADING = _get_env("PAPER_TRADING", MODE != "LIVE", bool)

LOT_SIZE = {
    "NIFTY": 50,
    "BANKNIFTY": 15,
}

TELEGRAM_TOKEN = _get_env("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = _get_env("TELEGRAM_CHAT_ID", "")

# =========================
# EXECUTION REALISM SETTINGS
# =========================

# Slippage Configuration
ENABLE_SLIPPAGE = _get_env("ENABLE_SLIPPAGE", True, bool)
SLIPPAGE_PERCENT = _get_env("SLIPPAGE_PERCENT", 0.003, float)  # 0.3% base slippage

# Execution Delay Configuration
ENABLE_DELAY = _get_env("ENABLE_DELAY", True, bool)
EXECUTION_DELAY_MS = _get_env("EXECUTION_DELAY_MS", 200, int)  # 200ms base delay

# Advanced Execution Settings
ENABLE_VOLATILITY_ADJUSTMENT = _get_env("ENABLE_VOLATILITY_ADJUSTMENT", True, bool)
ENABLE_TIME_BASED_SLIPPAGE = _get_env("ENABLE_TIME_BASED_SLIPPAGE", True, bool)
ENABLE_PARTIAL_FILLS = _get_env("ENABLE_PARTIAL_FILLS", False, bool)
