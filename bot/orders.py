"""
Order placement logic for the trading bot.

This module acts as the business-logic layer between the CLI and the
raw Binance client.  It formats requests, dispatches them via the
client, and returns structured result objects.
"""

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, Optional

from bot.client import BinanceFuturesClient, BinanceAPIError, NetworkError
from bot.validators import validate_inputs

logger = logging.getLogger("trading_bot.orders")


@dataclass
class OrderResult:
    """
    Structured representation of an order outcome.

    Attributes:
        success:      True if the order was accepted by the exchange.
        order_id:     Exchange-assigned order identifier.
        symbol:       Trading pair symbol.
        side:         BUY or SELL.
        order_type:   MARKET, LIMIT, or STOP_MARKET.
        status:       Exchange order status (e.g. FILLED, NEW).
        orig_qty:     Original requested quantity.
        executed_qty: Quantity actually executed so far.
        avg_price:    Average fill price (0 if unfilled LIMIT/STOP).
        raw_response: Full raw response from Binance.
        error:        Human-readable error message (only on failure).
    """

    success: bool
    order_id: Optional[int] = None
    symbol: str = ""
    side: str = ""
    order_type: str = ""
    status: str = ""
    orig_qty: str = ""
    executed_qty: str = ""
    avg_price: str = ""
    raw_response: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


def place_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    stop_price: Optional[str] = None,
) -> OrderResult:
    """
    Validate inputs and place an order via the Binance client.

    Args:
        client:     Authenticated BinanceFuturesClient instance.
        symbol:     Trading pair (e.g. BTCUSDT).
        side:       BUY or SELL.
        order_type: MARKET, LIMIT, or STOP_MARKET.
        quantity:   Order quantity (string; will be parsed to Decimal).
        price:      Limit price string (required for LIMIT).
        stop_price: Stop trigger price string (required for STOP_MARKET).

    Returns:
        OrderResult dataclass with success/failure details.
    """
    # --- Validation ---
    try:
        validated = validate_inputs(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
    except ValueError as exc:
        logger.warning("Input validation failed: %s", exc)
        return OrderResult(success=False, error=str(exc))

    # --- Dispatch ---
    try:
        response = client.place_order(
            symbol=validated["symbol"],
            side=validated["side"],
            order_type=validated["order_type"],
            quantity=validated["quantity"],
            price=validated["price"],
            stop_price=validated["stop_price"],
        )
    except BinanceAPIError as exc:
        logger.error("BinanceAPIError while placing order: %s", exc)
        return OrderResult(
            success=False,
            error=f"API error {exc.code}: {exc.message}",
        )
    except NetworkError as exc:
        logger.error("NetworkError while placing order: %s", exc)
        return OrderResult(success=False, error=f"Network error: {exc}")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error while placing order")
        return OrderResult(success=False, error=f"Unexpected error: {exc}")

    # --- Parse response ---
    return OrderResult(
        success=True,
        order_id=response.get("orderId"),
        symbol=response.get("symbol", ""),
        side=response.get("side", ""),
        order_type=response.get("type", ""),
        status=response.get("status", ""),
        orig_qty=response.get("origQty", ""),
        executed_qty=response.get("executedQty", ""),
        avg_price=response.get("avgPrice", "0"),
        raw_response=response,
    )
