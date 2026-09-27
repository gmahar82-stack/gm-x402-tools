"""Tool definitions shared by the LangChain and CrewAI adapters."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel, Field

from .client import GMTools, ToolError


class TokenArgs(BaseModel):
    address: str = Field(description="Token contract address on Base (0x followed by 40 hex characters)")


class AddressArgs(BaseModel):
    address: str = Field(description="Destination address on Base that funds would be sent to")
    from_address: str | None = Field(default=None, description="Optional: the sending wallet, to detect look-alike (poisoning) addresses")


class ReadArgs(BaseModel):
    url: str = Field(description="Public http(s) URL of a web page or PDF")
    max_chars: int | None = Field(default=None, description="Optional: maximum Markdown characters to return (default 50000)")


class MetaArgs(BaseModel):
    url: str = Field(description="Public http(s) URL")


class DealArgs(BaseModel):
    task: str = Field(description="What you need done, in plain words, e.g. 'current weather for a city'")
    max_price_usd: float | None = Field(default=None, description="Optional: ignore services above this price per call")


class CheckServiceArgs(BaseModel):
    url: str = Field(description="URL of the paid (x402) API you are about to pay")
    method: str = Field(default="GET", description="HTTP method the API uses")


@dataclass
class Spec:
    name: str
    description: str
    args: type[BaseModel]
    run: Callable[..., dict[str, Any]]


def specs(client: GMTools) -> list[Spec]:
    return [
        Spec(
            "check_token_safety",
            "Before buying a token on Base: simulates a real buy and sell (honeypot and hidden-tax test), checks owner powers, "
            "whale concentration, liquidity and scam lists. Returns verdict scam/high_risk/caution/low_risk with reasons.",
            TokenArgs,
            lambda address: client.check_token(address),
        ),
        Spec(
            "check_address_safety",
            "Before sending crypto on Base: checks scam lists, address poisoning (look-alikes of addresses the sender really uses), "
            "token contracts and burn addresses where funds are lost. Returns a verdict with reasons.",
            AddressArgs,
            lambda address, from_address=None: client.check_address(address, from_address),
        ),
        Spec(
            "read_web_page",
            "Read a public web page or PDF and return clean Markdown of the main content, plus title, author, date and links.",
            ReadArgs,
            lambda url, max_chars=None: client.read_page(url, max_chars),
        ),
        Spec(
            "get_page_metadata",
            "Get a web page's title, description, canonical URL, language, author, publish date, image and JSON-LD.",
            MetaArgs,
            lambda url: client.page_metadata(url),
        ),
        Spec(
            "find_cheapest_api",
            "Find the cheapest WORKING paid (x402) API for a task, ranked by live price, uptime and speed, with example inputs.",
            DealArgs,
            lambda task, max_price_usd=None: client.cheapest_service(task, max_price_usd),
        ),
        Spec(
            "check_paid_api",
            "FREE. Before paying an x402 API: is it up, does its real price match its listing, and is there a cheaper alternative?",
            CheckServiceArgs,
            lambda url, method="GET": client.check_service(url, method),
        ),
    ]


def as_text(run: Callable[..., dict[str, Any]], **kwargs: Any) -> str:
    """Run a tool and return JSON text for the LLM; errors become readable messages instead of exceptions."""
    try:
        return json.dumps(run(**kwargs), indent=1)[:60_000]
    except ToolError as e:
        return f"Error (not charged): {e}"
