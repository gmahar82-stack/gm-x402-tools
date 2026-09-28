import json

import pytest
import requests

from gm_x402_tools import GMTools, PaymentRequired
from gm_x402_tools.specs import as_text, specs


class FakeResponse:
    def __init__(self, status, body):
        self.status_code = status
        self._body = body
        self.text = json.dumps(body)

    def json(self):
        return self._body


def make(monkeypatch, status, body):
    client = GMTools()
    calls = []

    def fake_get(url, params=None, timeout=None):
        calls.append((url, params))
        return FakeResponse(status, body)

    monkeypatch.setattr(client.session, "get", fake_get)
    return client, calls


def test_free_tier_header_and_no_key(monkeypatch):
    monkeypatch.delenv("GM_X402_PRIVATE_KEY", raising=False)
    client = GMTools()
    assert client.paying is False
    assert client.session.headers["X-Free-Tier"] == "1"
    assert isinstance(client.session, requests.Session)


def test_success_drops_none_params(monkeypatch):
    client, calls = make(monkeypatch, 200, {"verdict": "low_risk"})
    assert client.check_address("0xabc", None)["verdict"] == "low_risk"
    assert calls[0][1] == {"address": "0xabc"}


def test_402_without_key_explains_how_to_pay(monkeypatch):
    client, _ = make(monkeypatch, 402, {"tryFree": "Send the header X-Free-Tier: 1 for 5 free checks per day."})
    with pytest.raises(PaymentRequired) as e:
        client.check_token("0xabc")
    assert "GM_X402_PRIVATE_KEY" in str(e.value)
    assert e.value.offer["tryFree"]


def test_errors_become_text_for_the_llm(monkeypatch):
    client, _ = make(monkeypatch, 502, {"error": "Blockchain data temporarily unavailable"})
    spec = next(s for s in specs(client) if s.name == "check_token_safety")
    out = as_text(spec.run, address="0xabc")
    assert out.startswith("Error (not charged)")


def test_seven_tools_with_schemas(monkeypatch):
    client, _ = make(monkeypatch, 200, {})
    names = [s.name for s in specs(client)]
    assert names == [
        "check_token_safety", "check_address_safety", "read_web_page", "get_page_metadata",
        "find_cheapest_api", "check_payment_safety", "check_paid_api",
    ]


def test_langchain_tools(monkeypatch):
    pytest.importorskip("langchain_core")
    from gm_x402_tools.langchain import get_tools

    client, calls = make(monkeypatch, 200, {"title": "Example Domain"})
    tools = get_tools(client)
    meta = next(t for t in tools if t.name == "get_page_metadata")
    assert "Example Domain" in meta.invoke({"url": "https://example.com"})
    assert calls[-1][1] == {"url": "https://example.com"}


def test_preflight_payment_calls_pay_safe(monkeypatch):
    client, calls = make(monkeypatch, 200, {"verdict": "stop", "summary": "Don't pay."})
    spec = next(s for s in specs(client) if s.name == "check_payment_safety")
    out = json.loads(as_text(spec.run, url="https://api.example.com/x", price_usd=0.01, pay_to="0xdead"))
    assert out["verdict"] == "stop"
    assert calls[0][0].endswith("/v1/preflight")
    assert calls[0][1] == {"url": "https://api.example.com/x", "price_usd": 0.01, "pay_to": "0xdead", "method": "GET"}
