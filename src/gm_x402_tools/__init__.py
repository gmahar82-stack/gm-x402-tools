"""Pay-per-call tools for AI agents: crypto safety checks, a web/PDF reader and a cheapest-API finder.

Free daily allowance built in; pay beyond it in USDC on Base via x402. See README for details.
"""

from .client import GMTools, PaymentRequired, ToolError

__all__ = ["GMTools", "PaymentRequired", "ToolError"]
__version__ = "0.1.0"
