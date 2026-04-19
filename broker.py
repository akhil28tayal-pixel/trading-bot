from auth import get_kite
from logger import log
from risk.execution import execute_order_with_realism, update_price_history
import config


kite = None


def _get_kite_client():
    global kite
    if kite is None:
        kite = get_kite()
    return kite


def get_ltp(symbol):
    """Get Last Traded Price for a symbol."""
    try:
        quote = _get_kite_client().ltp(symbol)
        return quote[symbol]["last_price"]
    except Exception as e:
        log(f"Error getting LTP for {symbol}: {e}")
        return None


def place_order_realistic(symbol, transaction_type, quantity, market_price, volatility_data=None):
    """
    Place order with realistic execution (slippage + delay)
    """
    execution_details = execute_order_with_realism(
        price=market_price,
        side=transaction_type,
        quantity=quantity,
        symbol=symbol,
        volatility_data=volatility_data,
    )

    base_symbol = (
        symbol.split("2")[0]
        if "2" in symbol
        else symbol[:symbol.find("CE")]
        if "CE" in symbol
        else symbol[:symbol.find("PE")]
        if "PE" in symbol
        else symbol
    )
    if base_symbol in ["NIFTY", "BANKNIFTY"]:
        update_price_history(base_symbol, market_price)

    if config.PAPER_TRADING:
        log(f"PAPER REALISTIC: {transaction_type} {quantity} {symbol} @ ₹{execution_details['executed_price']:.2f}")
        execution_details["order_id"] = "PAPER_REALISTIC_ORDER"
        execution_details["status"] = "COMPLETE"
        return execution_details

    try:
        order = _get_kite_client().place_order(
            variety=_get_kite_client().VARIETY_REGULAR,
            exchange=_get_kite_client().EXCHANGE_NFO,
            tradingsymbol=symbol,
            transaction_type=transaction_type,
            quantity=quantity,
            product=_get_kite_client().PRODUCT_MIS,
            order_type=_get_kite_client().ORDER_TYPE_LIMIT,
            price=execution_details["executed_price"],
        )

        execution_details["order_id"] = order["order_id"]
        execution_details["status"] = "PLACED"

        log(
            f"REALISTIC Order placed: {transaction_type} {quantity} {symbol} "
            f"@ ₹{execution_details['executed_price']:.2f} | Order ID: {order['order_id']}"
        )
        return execution_details

    except Exception as e:
        log(f"Error placing realistic order: {e}")
        execution_details["error"] = str(e)
        execution_details["status"] = "FAILED"
        return execution_details


def place_order(symbol, transaction_type, quantity, market_price=None):
    """
    Legacy order placement function - now with optional realistic execution
    """
    if market_price and (config.ENABLE_SLIPPAGE or config.ENABLE_DELAY):
        return place_order_realistic(symbol, transaction_type, quantity, market_price)

    if config.PAPER_TRADING:
        log(f"PAPER: {transaction_type} {quantity} {symbol}")
        return {"order_id": "PAPER_ORDER", "status": "COMPLETE"}

    try:
        order = _get_kite_client().place_order(
            variety=_get_kite_client().VARIETY_REGULAR,
            exchange=_get_kite_client().EXCHANGE_NFO,
            tradingsymbol=symbol,
            transaction_type=transaction_type,
            quantity=quantity,
            product=_get_kite_client().PRODUCT_MIS,
            order_type=_get_kite_client().ORDER_TYPE_MARKET,
        )

        log(f"Order placed: {transaction_type} {quantity} {symbol} | Order ID: {order['order_id']}")
        return {"order_id": order["order_id"], "status": "PLACED"}

    except Exception as e:
        log(f"Error placing order: {e}")
        return {"error": str(e), "status": "FAILED"}
