"""
Input validation helpers for the trading bot CLI.
Raises ValueError with descriptive messages on invalid input.
"""

from decimal import Decimal, InvalidOperation
from typing import Optional


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


def validate_symbol(symbol: str) -> str:
    """
    Validate and normalise a trading symbol.

    Rules:
    - Must be a non-empty string containing only alphanumeric characters.
    - Converted to uppercase automatically.

    Args:
        symbol: Raw symbol string from user input.

    Returns:
        Uppercased, stripped symbol.

    Raises:
        ValueError: If the symbol is invalid.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol must not be empty.")
    if not symbol.isalnum():
        raise ValueError(
            f"Invalid symbol '{symbol}'. Use alphanumeric characters only (e.g. BTCUSDT)."
        )
    return symbol


def validate_side(side: str) -> str:
    """
    Validate order side (BUY or SELL).

    Args:
        side: Raw side string.

    Returns:
        Uppercased side string.

    Raises:
        ValueError: If not BUY or SELL.
    """
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    """
    Validate order type.

    Args:
        order_type: Raw order type string.

    Returns:
        Uppercased order type.

    Raises:
        ValueError: If not a supported order type.
    """
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: str) -> Decimal:
    """
    Validate and parse order quantity.

    Args:
        quantity: Raw quantity string.

    Returns:
        Positive Decimal quantity.

    Raises:
        ValueError: If quantity is not a positive number.
    """
    try:
        qty = Decimal(str(quantity).strip())
    except InvalidOperation:
        raise ValueError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be greater than zero, got {qty}.")
    return qty


def validate_price(price: Optional[str]) -> Optional[Decimal]:
    """
    Validate and parse order price (required for LIMIT / STOP_MARKET orders).

    Args:
        price: Raw price string, or None.

    Returns:
        Positive Decimal price, or None if not provided.

    Raises:
        ValueError: If price is provided but invalid or non-positive.
    """
    if price is None:
        return None
    try:
        p = Decimal(str(price).strip())
    except InvalidOperation:
        raise ValueError(f"Invalid price '{price}'. Must be a positive number.")
    if p <= 0:
        raise ValueError(f"Price must be greater than zero, got {p}.")
    return p


def validate_stop_price(stop_price: Optional[str]) -> Optional[Decimal]:
    """
    Validate and parse stop price (required for STOP_MARKET orders).

    Args:
        stop_price: Raw stop price string, or None.

    Returns:
        Positive Decimal stop price, or None if not provided.

    Raises:
        ValueError: If stop_price is provided but invalid or non-positive.
    """
    if stop_price is None:
        return None
    try:
        sp = Decimal(str(stop_price).strip())
    except InvalidOperation:
        raise ValueError(f"Invalid stop price '{stop_price}'. Must be a positive number.")
    if sp <= 0:
        raise ValueError(f"Stop price must be greater than zero, got {sp}.")
    return sp


def validate_inputs(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    stop_price: Optional[str] = None,
) -> dict:
    """
    Run all validations and return a cleaned parameter dict.

    Args:
        symbol:      Trading symbol (e.g. BTCUSDT).
        side:        BUY or SELL.
        order_type:  MARKET, LIMIT, or STOP_MARKET.
        quantity:    Order quantity.
        price:       Limit price (required for LIMIT).
        stop_price:  Stop trigger price (required for STOP_MARKET).

    Returns:
        Dict with validated & typed values.

    Raises:
        ValueError: On any validation failure.
    """
    clean_symbol = validate_symbol(symbol)
    clean_side = validate_side(side)
    clean_order_type = validate_order_type(order_type)
    clean_qty = validate_quantity(quantity)
    clean_price = validate_price(price)
    clean_stop = validate_stop_price(stop_price)

    # Cross-field checks
    if clean_order_type == "LIMIT" and clean_price is None:
        raise ValueError("A price is required for LIMIT orders.")
    if clean_order_type == "STOP_MARKET" and clean_stop is None:
        raise ValueError("A stop price (--stop-price) is required for STOP_MARKET orders.")

    return {
        "symbol": clean_symbol,
        "side": clean_side,
        "order_type": clean_order_type,
        "quantity": clean_qty,
        "price": clean_price,
        "stop_price": clean_stop,
    }
