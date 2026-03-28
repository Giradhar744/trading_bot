"""
config.py — Central configuration module.

Loads environment variables from the .env file (via python-dotenv) and
exposes them as typed constants.  Every other module imports from here
instead of calling os.environ directly.

Usage:
    from bot.config import settings
    print(settings.api_key)
    print(settings.base_url)
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# ── Load .env from the project root ──────────────────────────────────────────
# Path: trading_bot_v2/.env  (two levels up from this file)
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


# ── Settings dataclass ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Settings:
    """
    Immutable settings object populated from environment variables.

    Attributes:
        api_key:    Binance API key (X-MBX-APIKEY header).
        api_secret: Binance API secret (used for HMAC-SHA256 signing).
        base_url:   Binance Futures base URL.
    """
    api_key: str
    api_secret: str
    base_url: str

    def validate(self) -> None:
        """
        Raise EnvironmentError if any required credential is missing
        or still holds the placeholder value.
        """
        if not self.api_key or self.api_key == "your_testnet_api_key_here":
            raise EnvironmentError(
                "BINANCE_API_KEY is not set.\n"
                "  → Open .env and paste your Binance Futures Testnet API key."
            )
        if not self.api_secret or self.api_secret == "your_testnet_api_secret_here":
            raise EnvironmentError(
                "BINANCE_API_SECRET is not set.\n"
                "  → Open .env and paste your Binance Futures Testnet API secret."
            )


def _load_settings() -> Settings:
    """Read env vars and return a Settings instance."""
    return Settings(
        api_key=os.environ.get("BINANCE_API_KEY", ""),
        api_secret=os.environ.get("BINANCE_API_SECRET", ""),
        base_url=os.environ.get("BINANCE_BASE_URL", "https://testnet.binancefuture.com"),
    )


# ── Singleton — import this everywhere ───────────────────────────────────────
settings: Settings = _load_settings()
