"""Plain Python client for three pay-per-call APIs for AI agents (USDC on Base via x402):

- Trust Check: is this token safe to buy? is this address safe to send to?
- Easy Reader AI: read any web page or PDF as clean Markdown, or just its metadata.
- Agent Deals: the cheapest working paid API for a task; free pre-payment checks.

Every service has a small free daily allowance (sent automatically). With a wallet key, calls beyond the free
allowance are paid automatically, capped per call by ``max_price_usd``. Without a key, you get the free
allowance and a clear PaymentRequired error afterwards.
"""

from __future__ import annotations

import os
from typing import Any

import requests

TRUST_CHECK = "https://trust-check.gm-tools.workers.dev"
EASY_READER = "https://agent-reader.gm-tools.workers.dev"
AGENT_DEALS = "https://agent-deals.gm-tools.workers.dev"

KEY_ENV = "GM_X402_PRIVATE_KEY"


class ToolError(Exception):
    """The service answered with an error. You are not charged for errors."""


class PaymentRequired(ToolError):
    """The free allowance is used up and no wallet is configured (or the price is above your cap)."""

    def __init__(self, message: str, offer: dict[str, Any] | None = None):
        super().__init__(message)
        self.offer = offer or {}


def _paying_session(private_key: str, max_price_usd: float) -> requests.Session:
    # Imported lazily so the free tier works without the payment dependencies being importable.
    from eth_account import Account
    from x402 import x402ClientSync
    from x402.client_base import max_amount
    from x402.http.clients import x402_requests
    from x402.mechanisms.evm.exact.register import register_exact_evm_client

    account = Account.from_key(private_key)
    client = x402ClientSync()
    # USDC has 6 decimals: never authorize more than the cap for a single call.
    register_exact_evm_client(client, account, networks="eip155:8453", policies=[max_amount(int(max_price_usd * 1_000_000))])
    return x402_requests(client)


class GMTools:
    """Client for Trust Check, Easy Reader AI and Agent Deals.

    Args:
        private_key: Wallet key that pays in USDC on Base (defaults to the ``GM_X402_PRIVATE_KEY`` environment
            variable). Use a dedicated wallet holding only a small amount of USDC, never your main wallet.
            Leave unset to use only the free daily allowance.
        max_price_usd: Refuse any single call priced above this (default $0.01).
        use_free_tier: Ask for the free daily allowance first (default True).
        timeout: Seconds to wait for each call.
    """

    def __init__(
        self,
        private_key: str | None = None,
        *,
        max_price_usd: float = 0.01,
        use_free_tier: bool = True,
        timeout: float = 90,
    ):
        key = private_key or os.environ.get(KEY_ENV)
        self.paying = bool(key)
        self.session = _paying_session(key, max_price_usd) if key else requests.Session()
        self.session.headers["User-Agent"] = "gm-x402-tools (python)"
        if use_free_tier:
            self.session.headers["X-Free-Tier"] = "1"
        self.timeout = timeout

    def _get(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        params = {k: v for k, v in params.items() if v is not None}
        res = self.session.get(url, params=params, timeout=self.timeout)
        try:
            body = res.json()
        except ValueError:
            body = {"error": res.text[:300]}
        if res.status_code == 402:
            hint = body.get("tryFree") or body.get("price") or ""
            how = "Set GM_X402_PRIVATE_KEY (a small USDC wallet on Base) to pay per call." if not self.paying else (
                "The price may be above your max_price_usd, or the wallet has no USDC on Base."
            )
            raise PaymentRequired(f"Payment required. {how} {hint}".strip(), body)
        if res.status_code >= 400:
            raise ToolError(f"HTTP {res.status_code}: {body.get('error', body)}")
        return body

    # Trust Check -----------------------------------------------------------------------------------------
    def check_token(self, address: str) -> dict[str, Any]:
        """Is this Base token safe to buy? Buy+sell simulation, taxes, owner powers, whales, liquidity, scam lists."""
        return self._get(f"{TRUST_CHECK}/v1/token", {"address": address})

    def check_address(self, address: str, from_address: str | None = None, known: list[str] | None = None) -> dict[str, Any]:
        """Is this Base address safe to send funds to? Scam lists, address poisoning, token contracts, burn addresses."""
        return self._get(
            f"{TRUST_CHECK}/v1/address",
            {"address": address, "from": from_address, "known": ",".join(known) if known else None},
        )

    # Easy Reader AI --------------------------------------------------------------------------------------
    def read_page(self, url: str, max_chars: int | None = None, selector: str | None = None) -> dict[str, Any]:
        """Read a public web page or PDF as clean Markdown, with title, author, date, JSON-LD and links."""
        return self._get(f"{EASY_READER}/v1/read", {"url": url, "maxChars": max_chars, "selector": selector})

    def page_metadata(self, url: str) -> dict[str, Any]:
        """Title, description, canonical URL, language, author, publish date, image and JSON-LD of a page."""
        return self._get(f"{EASY_READER}/v1/meta", {"url": url})

    # Agent Deals -----------------------------------------------------------------------------------------
    def cheapest_service(self, task: str, max_price_usd: float | None = None, limit: int | None = None) -> dict[str, Any]:
        """The cheapest WORKING paid (x402) APIs for a task, ranked by live price, uptime and speed."""
        return self._get(f"{AGENT_DEALS}/v1/best", {"task": task, "max_price_usd": max_price_usd, "limit": limit})

    def preflight_payment(
        self,
        url: str,
        price_usd: float | None = None,
        pay_to: str | None = None,
        method: str = "GET",
        max_price_usd: float | None = None,
    ) -> dict[str, Any]:
        """FREE Pay Safe check before paying any x402 API: GO / CAUTION / STOP. Is the service working, is the
        price fair (vs its listing, what it charged before, similar services), is the wallet safe and the one
        it normally uses?"""
        return self._get(
            f"{AGENT_DEALS}/v1/preflight",
            {"url": url, "price_usd": price_usd, "pay_to": pay_to, "method": method, "max_price_usd": max_price_usd},
        )

    def check_service(self, url: str, method: str = "GET") -> dict[str, Any]:
        """FREE: before paying an x402 API, check it is up, its price matches its listing, and cheaper options."""
        return self._get(f"{AGENT_DEALS}/v1/check", {"url": url, "method": method})
