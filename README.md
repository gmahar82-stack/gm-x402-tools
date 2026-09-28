# gm-x402-tools

Seven ready-made tools for AI agents, for **LangChain**, **CrewAI** or plain Python:

| Tool | What it does | Price |
|---|---|---|
| `check_token_safety` | Before buying a token on Base: simulates a real buy and sell (honeypot and hidden-tax test), owner powers, whales, liquidity, scam lists | $0.003 |
| `check_address_safety` | Before sending crypto on Base: scam lists, **address poisoning** look-alikes, token contracts and burn addresses | $0.002 |
| `read_web_page` | Any public web page or PDF as clean Markdown, with title, author, date and links | $0.003 |
| `get_page_metadata` | A page's title, description, author, date, image and JSON-LD | $0.002 |
| `find_cheapest_api` | The cheapest **working** paid API for a task, ranked by live price, uptime and speed | $0.002 |
| `check_payment_safety` | **Pay Safe**: before paying any x402 API, GO / CAUTION / STOP. Is it working, is the price fair, is the wallet safe and the one it normally uses? | **Free** |
| `check_paid_api` | Before paying an API: is it up, is the price right, is there a cheaper one? | **Free** |

- **Free to start:** every service includes a free daily allowance (3–20 calls a day), requested automatically.
- **No signup, no API key:** beyond the free allowance, calls are paid per use in USDC on Base with [x402](https://www.x402.org).
- **Only charged on success:** errors are never billed.
- **Spending cap:** no single call can cost more than `max_price_usd` (default $0.01).

## Install

```bash
pip install "gm-x402-tools[langchain]"   # or [crewai], or plain: pip install gm-x402-tools
```

## LangChain

```python
from gm_x402_tools.langchain import get_tools

tools = get_tools()  # free daily allowance
# agent = create_agent(model, tools)
```

## CrewAI

```python
from crewai import Agent
from gm_x402_tools.crewai import get_tools

analyst = Agent(role="Crypto analyst", goal="Only buy safe tokens", backstory="...", tools=get_tools())
```

## Plain Python

```python
from gm_x402_tools import GMTools

gm = GMTools()
print(gm.check_token("0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed")["verdict"])
print(gm.check_address("0x...destination", from_address="0x...your wallet")["summary"])
print(gm.read_page("https://example.com")["markdown"])
print(gm.preflight_payment("https://api.example.com/data", price_usd=0.01, pay_to="0x...")["verdict"])  # go / caution / stop
```

## Paying beyond the free allowance

Set `GM_X402_PRIVATE_KEY` to the key of a **dedicated wallet holding a small amount of USDC on Base** (a few dollars
covers thousands of calls). Never use your main wallet. The key stays on your machine; it only signs each payment,
and never above `max_price_usd`.

```python
tools = get_tools(max_price_usd=0.005)   # key read from GM_X402_PRIVATE_KEY
```

## Also available as

- MCP servers: `https://trust-check.gm-tools.workers.dev/mcp` and `https://agent-deals.gm-tools.workers.dev/mcp`
- Plain HTTP APIs, documented at `/llms.txt` and `/openapi.json` on each service.

Safety checks are automated on-chain analysis, not financial advice.

MIT licensed.
