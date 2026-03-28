"""
client.py — Binance Futures Testnet REST client.

Handles authentication (HMAC-SHA256), request signing, and raw HTTP
communication.  Credentials are pulled from config.settings — never
hardcoded or passed on the command line.
"""

import hashlib
import hmac
import logging
import time
from decimal import Decimal
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from bot.config import settings  # ← single source of credentials

logger = logging.getLogger("trading_bot.client")

RECV_WINDOW = 60000  # milliseconds — generous window to handle PC clock skew


class BinanceAPIError(Exception):
    """Raised when Binance returns an error payload."""

    def __init__(self, code: int, message: str, status_code: int = 0):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(f"Binance API error {code}: {message} (HTTP {status_code})")


class NetworkError(Exception):
    """Raised on connection / timeout failures."""


class BinanceFuturesClient:
    """
    Thin wrapper around the Binance Futures Testnet REST API.

    Credentials are loaded automatically from config.settings.
    You never need to pass api_key / api_secret directly.
    """

    def __init__(self):
        # Validate credentials before making any network call
        settings.validate()

        self.api_key = settings.api_key
        self.api_secret = settings.api_secret
        self.base_url = settings.base_url.rstrip("/")

        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self.api_key,   # ← API key in every header
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.info("BinanceFuturesClient ready (base_url=%s)", self.base_url)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _sign(self, query_string: str) -> str:
        """HMAC-SHA256 signature using the API secret."""
        return hmac.new(
            self.api_secret.encode("utf-8"),    # ← API secret used here
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _signed_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        params["timestamp"] = self._timestamp()
        params["recvWindow"] = RECV_WINDOW
        query_string = urlencode(params)
        params["signature"] = self._sign(query_string)
        return params

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Dict[str, Any]:
        params = params or {}
        if signed:
            params = self._signed_params(params)

        url = self.base_url + endpoint

        logger.debug(
            "REQUEST  method=%s url=%s params=%s",
            method.upper(), url,
            {k: v for k, v in params.items() if k != "signature"},
        )

        try:
            if method.upper() in ("GET", "DELETE"):
                response = self._session.request(method, url, params=params, timeout=10)
            else:
                response = self._session.request(method, url, data=params, timeout=10)
        except requests.exceptions.Timeout as exc:
            logger.error("NETWORK TIMEOUT: %s", exc)
            raise NetworkError(f"Request timed out: {exc}") from exc
        except requests.exceptions.ConnectionError as exc:
            logger.error("CONNECTION ERROR: %s", exc)
            raise NetworkError(f"Connection failed: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            logger.error("REQUEST EXCEPTION: %s", exc)
            raise NetworkError(f"Request failed: {exc}") from exc

        logger.debug("RESPONSE status=%s body=%s", response.status_code, response.text[:500])

        try:
            data = response.json()
        except ValueError:
            raise BinanceAPIError(
                -1,
                f"Non-JSON response (HTTP {response.status_code}): {response.text[:200]}",
                response.status_code,
            )

        if not response.ok or (isinstance(data, dict) and "code" in data and data["code"] != 200):
            code = data.get("code", response.status_code)
            msg = data.get("msg", "Unknown error")
            logger.error("API ERROR code=%s msg=%s", code, msg)
            raise BinanceAPIError(code, msg, response.status_code)

        return data

    # ── Public API methods ────────────────────────────────────────────────────

    def get_account_info(self) -> Dict[str, Any]:
        return self._request("GET", "/fapi/v2/account", signed=True)

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
        }

        if order_type == "LIMIT":
            params["price"] = str(price)
            params["timeInForce"] = time_in_force

        if order_type == "STOP_MARKET":
            # NOTE: The Binance Futures testnet does not support STOP_MARKET
            # (or any stop order type) on /fapi/v1/order — it returns -4120.
            # The algo endpoint (/fapi/v1/order/algo) also does not exist on
            # testnet (-5000). This is a testnet environment limitation only;
            # the production Futures API supports STOP_MARKET on /fapi/v1/order.
            params["stopPrice"] = str(stop_price)

        logger.info(
            "Placing %s %s | symbol=%s qty=%s price=%s stopPrice=%s",
            side, order_type, symbol, quantity, price, stop_price,
        )

        response = self._request("POST", "/fapi/v1/order", params=params, signed=True)

        logger.info(
            "Order placed | orderId=%s status=%s executedQty=%s avgPrice=%s",
            response.get("orderId"), response.get("status"),
            response.get("executedQty"), response.get("avgPrice"),
        )

        return response

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        return self._request("DELETE", "/fapi/v1/order",
                             params={"symbol": symbol, "orderId": order_id}, signed=True)

    def get_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        return self._request("GET", "/fapi/v1/order",
                             params={"symbol": symbol, "orderId": order_id}, signed=True)