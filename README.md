# Binance Futures Testnet Trading Bot

A lightweight Python CLI trading bot for placing orders on the [Binance Futures Testnet (USDT-M)](https://testnet.binancefuture.com). Built with direct REST calls (no third-party Binance SDK), HMAC-SHA256 signing, and a clean layered architecture.

---

## Features

| Feature | Details |
|---|---|
| Order types | MARKET, LIMIT, STOP_MARKET (bonus) |
| Sides | BUY, SELL |
| CLI | `argparse`-based with colour-coded terminal output |
| Logging | Structured rotating log file (DEBUG) + console (INFO) |
| Validation | All inputs validated before any API call is made |
| Error handling | API errors, network failures, and bad inputs all caught and reported |
| Auth | Credentials loaded automatically from `.env` — never passed on the CLI |

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package metadata
│   ├── client.py            # Binance REST client (HMAC signing, HTTP)
│   ├── orders.py            # Order placement business logic + OrderResult dataclass
│   ├── validators.py        # Input validation (symbol, side, type, quantity, price)
│   ├── logging_config.py    # Rotating file + console logging setup
│   └── cli.py               # argparse CLI entry point
├── logs/
│   └── trading_bot.log      # Auto-created on first run
├── .env                     # API credentials (git-ignored)
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Setup

### 1. Create a Binance Futures Testnet account

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Sign in with your GitHub account
3. Navigate to the **API Key** tab → generate a new key pair
4. Copy your **API Key** and **Secret Key**

### 2. Clone / download this project

```bash
git clone <repo-url>
cd trading_bot
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Dependencies: `requests`, `python-dotenv`. No third-party Binance SDK is used.

### 4. Configure credentials

Create a `.env` file in the project root:

```
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
# Optional — defaults to testnet if omitted
BINANCE_BASE_URL=https://testnet.binancefuture.com
```

> **Note:** Credentials are loaded automatically by `bot/config.py` via `python-dotenv`. You never need to pass them as CLI flags.

---

## How to Run

Run commands from the **project root** (`trading_bot/`). Since `cli.py` lives at the root alongside the `bot/` package, use either of these equivalent forms:

```bash
# Recommended (module form)
python -m cli <command> [options]

# Direct script form
python cli.py <command> [options]
```

> **Note:** `python -m bot.cli` only works if your files are inside a `bot/` sub-package with a proper `__init__.py` and you're running from the parent directory. If `cli.py` is at the root, use `python -m cli` or `python cli.py`.

---

### Place a MARKET order

```bash
# BUY 0.002 BTC at market price
python -m cli place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.002

# SELL 0.02 ETH at market price
python -m cli place --symbol ETHUSDT --side SELL --type MARKET --quantity 0.02
```

### Place a LIMIT order

```bash
# BUY 0.002 BTC with a limit at $55,000
python -m cli place --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.002 --price 55000

# SELL 0.002 BTC with a limit at $65,000
python -m cli place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.002 --price 65000
```

> **Note:** `--price` is required for LIMIT orders. Time-in-force defaults to `GTC`.

### Place a STOP_MARKET order (bonus order type)

```bash
# BUY when price rises above $62,000 (breakout entry)
python -m cli place --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.002 --stop-price 62000

# SELL when price drops below $50,000 (stop-loss)
python -m cli place --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.002 --stop-price 50000
```

> **Note:** `--stop-price` is required for STOP_MARKET orders.

### View account balances

```bash
python -m cli account
```

Displays all assets with a non-zero wallet balance, including unrealised PNL.

### Get raw JSON response

Append `--json` to any `place` command to print the full Binance API response:

```bash
python -m cli place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.002 --json
```

---

## Example Output

### Successful MARKET order

```
────────────────────────────────────────────────────────────
  ORDER REQUEST SUMMARY
────────────────────────────────────────────────────────────
  Symbol             BTCUSDT
  Side               BUY
  Type               MARKET
  Quantity           0.002
────────────────────────────────────────────────────────────

────────────────────────────────────────────────────────────
  ✔  ORDER PLACED SUCCESSFULLY
────────────────────────────────────────────────────────────
  Order ID           13001480283
  Symbol             BTCUSDT
  Side               BUY
  Type               MARKET
  Status             NEW
  Orig Qty           0.002
  Executed Qty       0.000
  Avg Price          N/A (unfilled)
────────────────────────────────────────────────────────────
```

### Account balances

```
────────────────────────────────────────────────────────────
  ACCOUNT BALANCES
────────────────────────────────────────────────────────────
  Asset        Wallet Balance         Unrealised PNL
  ──────────────────────────────────────────────────
  BTC          0.01000000             0.00000000
  USDT         4999.87771112          0.11238598
  USDC         5000.00000000          0.00000000
────────────────────────────────────────────────────────────
```

Colour coding is applied automatically when running in a TTY (green for BUY/FILLED, red for SELL/FAILED, yellow for pending statuses).

---

## Log Files

Logs are written to `logs/trading_bot.log` (directory auto-created on first run).

| Handler | Level | Purpose |
|---|---|---|
| File | DEBUG | Full API request params, response bodies, errors |
| Console | INFO | Clean summary — order placed, errors only |

Log files rotate at **5 MB**, keeping **3 backups**.

Sample log lines:

```
2026-03-28T12:35:22 | INFO     | trading_bot.client | BinanceFuturesClient ready (base_url=https://testnet.binancefuture.com)
2026-03-28T12:35:22 | INFO     | trading_bot.cli    | CLI place | symbol=BTCUSDT side=BUY type=MARKET qty=0.002 price=None stop_price=None
2026-03-28T12:35:22 | INFO     | trading_bot.client | Placing BUY MARKET | symbol=BTCUSDT qty=0.002 price=None stopPrice=None
2026-03-28T12:35:24 | INFO     | trading_bot.client | Order placed | orderId=13001480283 status=NEW executedQty=0.000 avgPrice=0.00
```

---

## Architecture

The codebase follows a strict layered separation:

```
CLI (cli.py)
  └── Business logic (orders.py)
        └── Validation (validators.py)
        └── HTTP client (client.py)
              └── Config / credentials (config.py)
```

- **`config.py`** — loads `.env` via `python-dotenv` and exposes a frozen `Settings` dataclass; validates credentials before any network call.
- **`client.py`** — handles HMAC-SHA256 signing, timestamp injection, `requests.Session` management, and HTTP error parsing. Raises typed `BinanceAPIError` and `NetworkError` exceptions.
- **`validators.py`** — pure functions that parse and validate each field (symbol, side, type, quantity, price, stop price) and raise `ValueError` with descriptive messages.
- **`orders.py`** — orchestrates validation → dispatch → response parsing; always returns a typed `OrderResult` dataclass (never raises to the CLI).
- **`cli.py`** — parses CLI arguments, calls `place_order`, and renders colour-coded output.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Missing `--price` for a LIMIT order | Validation error before any API call; exit code 1 |
| Missing `--stop-price` for STOP_MARKET | Validation error before any API call; exit code 1 |
| Invalid symbol or negative quantity | Clear error message; exit code 1 |
| Binance API error (e.g. `-1121 Invalid symbol`) | `BinanceAPIError` caught; code and message printed |
| Network timeout / connection failure | `NetworkError` caught; user-friendly message |
| Unexpected exception | Logged with full stack trace; user-friendly message |
| Missing or placeholder credentials | `EnvironmentError` on startup with remediation hint |

---

## Assumptions & Known Testnet Behaviour

1. **Testnet only** — `BINANCE_BASE_URL` defaults to `https://testnet.binancefuture.com`. Override via `.env` for production (change at your own risk).

2. **USDT-M perpetual futures** — all symbols must be USDT-margined (e.g. `BTCUSDT`, `ETHUSDT`).

3. **Minimum notional value** — Binance enforces a minimum order notional of **$100** (error `-4164`). For BTCUSDT at ~$85,000, the minimum viable quantity is approximately `0.002`. A quantity of `0.001` (~$85) will be rejected by the exchange. Always ensure `quantity × price ≥ 100`.

4. **STOP_MARKET on testnet** — the testnet `/fapi/v1/order` endpoint returns error `-4120` (`Order type not supported for this endpoint`) for STOP_MARKET orders. The testnet routes these to a separate Algo Order API. This is a **testnet environment limitation**, not a code bug; the implementation is correct for the production Futures API.

5. **Market order status** — MARKET orders on the testnet frequently return status `NEW` rather than `FILLED` immediately, as the testnet matching engine is asynchronous. The order is accepted; check the account balances or order status after a short delay to confirm execution.

6. **Quantity precision** — you are responsible for supplying a quantity that satisfies the symbol's `LOT_SIZE` filter. The minimum step for BTCUSDT is `0.001`, but the minimum notional constraint effectively requires at least `0.002` at current prices.

7. **Time-in-force** — LIMIT orders default to `GTC` (Good Till Cancelled). Change `time_in_force` in `client.py → place_order()` if needed.

8. **Python version** — requires Python 3.8+.

9. **Signature** — the `_sign` method uses `hmac.new` (standard library). Timestamp skew beyond `recvWindow` (5000 ms) will be rejected by Binance.

---

## Dependencies

```
requests>=2.31.0
python-dotenv>=1.0.0
```

Full pinned versions are in `requirements.txt`. No third-party Binance SDK is used — all API calls are made directly via `requests` with HMAC-SHA256 signing.
