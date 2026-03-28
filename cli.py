#!/usr/bin/env python3
"""
cli.py — CLI entry point for the Binance Futures Testnet trading bot.
Credentials are loaded automatically from the .env file in the project root.

Run from the project root (trading_bot/) as:
    python -m bot.cli place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
"""

import argparse
import json
import logging
import os
import sys

from bot.config import settings
from bot.client import BinanceFuturesClient, BinanceAPIError, NetworkError
from bot.logging_config import setup_logging
from bot.orders import place_order

setup_logging()
log = logging.getLogger("trading_bot.cli")

# ── ANSI colours ──────────────────────────────────────────────────────────────
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_GREEN  = "\033[92m"
_RED    = "\033[91m"
_CYAN   = "\033[96m"
_YELLOW = "\033[93m"

def _c(text, code):
    return f"{code}{text}{_RESET}" if sys.stdout.isatty() else text

def _sep():
    print("─" * 60)

# ── Print helpers ─────────────────────────────────────────────────────────────

def _print_request_summary(args):
    _sep()
    print(_c("  ORDER REQUEST SUMMARY", _BOLD + _CYAN))
    _sep()
    print(f"  {'Symbol':<18} {args.symbol.upper()}")
    print(f"  {'Side':<18} {_c(args.side.upper(), _GREEN if args.side.upper() == 'BUY' else _RED)}")
    print(f"  {'Type':<18} {args.type.upper()}")
    print(f"  {'Quantity':<18} {args.quantity}")
    if getattr(args, "price", None):
        print(f"  {'Limit Price':<18} {args.price}")
    if getattr(args, "stop_price", None):
        print(f"  {'Stop Price':<18} {args.stop_price}")
    _sep()
    print()


def _print_order_response(result):
    if result.success:
        print()
        _sep()
        print(_c("  ✔  ORDER PLACED SUCCESSFULLY", _BOLD + _GREEN))
        _sep()
        print(f"  {'Order ID':<18} {result.order_id}")
        print(f"  {'Symbol':<18} {result.symbol}")
        print(f"  {'Side':<18} {_c(result.side, _GREEN if result.side == 'BUY' else _RED)}")
        print(f"  {'Type':<18} {result.order_type}")
        print(f"  {'Status':<18} {_c(result.status, _GREEN if result.status == 'FILLED' else _YELLOW)}")
        print(f"  {'Orig Qty':<18} {result.orig_qty}")
        print(f"  {'Executed Qty':<18} {result.executed_qty}")
        avg = result.avg_price
        print(f"  {'Avg Price':<18} {avg if avg and avg != '0' else 'N/A (unfilled)'}")
        _sep()
        print()
    else:
        print()
        _sep()
        print(_c("  ✖  ORDER FAILED", _BOLD + _RED))
        _sep()
        print(f"  {'Error':<18} {result.error}")
        _sep()
        print()

# ── Client factory ────────────────────────────────────────────────────────────

def _build_client():
    try:
        return BinanceFuturesClient()
    except EnvironmentError as exc:
        print(_c(f"\n  Configuration error:\n  {exc}\n", _RED))
        sys.exit(1)

# ── Sub-commands ──────────────────────────────────────────────────────────────

def cmd_place(args):
    _print_request_summary(args)
    client = _build_client()

    log.info("CLI place | symbol=%s side=%s type=%s qty=%s price=%s stop_price=%s",
             args.symbol, args.side, args.type, args.quantity,
             getattr(args, "price", None), getattr(args, "stop_price", None))

    result = place_order(
        client     = client,
        symbol     = args.symbol,
        side       = args.side,
        order_type = args.type,
        quantity   = args.quantity,
        price      = getattr(args, "price", None),
        stop_price = getattr(args, "stop_price", None),
    )

    _print_order_response(result)

    if args.json:
        payload = result.raw_response if result.success else {"error": result.error}
        print(json.dumps(payload, indent=2))

    return 0 if result.success else 1


def cmd_account(args):
    client = _build_client()
    try:
        info = client.get_account_info()
    except (BinanceAPIError, NetworkError) as exc:
        print(_c(f"Failed to fetch account info: {exc}", _RED))
        return 1

    assets = [a for a in info.get("assets", []) if float(a.get("walletBalance", 0)) > 0]
    _sep()
    print(_c("  ACCOUNT BALANCES", _BOLD + _CYAN))
    _sep()
    if assets:
        print(f"  {'Asset':<12} {'Wallet Balance':<22} {'Unrealised PNL'}")
        print("  " + "─" * 50)
        for a in assets:
            print(f"  {a['asset']:<12} {float(a['walletBalance']):<22.8f} {float(a.get('unrealizedProfit', 0)):.8f}")
    else:
        print("  No non-zero balances found.")
    _sep()
    return 0

# ── Argument parser ───────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet trading bot",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # place
    p = sub.add_parser("place", help="Place a new order")
    p.add_argument("--symbol",     required=True,  help="e.g. BTCUSDT")
    p.add_argument("--side",       required=True,  choices=["BUY","SELL","buy","sell"])
    p.add_argument("--type",       required=True,  choices=["MARKET","LIMIT","STOP_MARKET","market","limit","stop_market"])
    p.add_argument("--quantity",   required=True,  help="Order quantity e.g. 0.001")
    p.add_argument("--price",                      help="Limit price (LIMIT orders only)")
    p.add_argument("--stop-price", dest="stop_price", help="Stop trigger price (STOP_MARKET only)")
    p.add_argument("--json",       action="store_true", help="Print raw JSON response")
    p.set_defaults(func=cmd_place)

    # account
    a = sub.add_parser("account", help="Show account balances")
    a.set_defaults(func=cmd_account)

    return parser

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = build_parser()
    args   = parser.parse_args()
    try:
        code = args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        code = 130
    sys.exit(code)


if __name__ == "__main__":
    main()