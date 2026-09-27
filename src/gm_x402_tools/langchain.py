"""LangChain tools. Usage:

    from gm_x402_tools.langchain import get_tools
    tools = get_tools()                      # free daily allowance only
    tools = get_tools(private_key="0x...")   # or set GM_X402_PRIVATE_KEY to pay beyond it
"""

from __future__ import annotations

from functools import partial

from langchain_core.tools import BaseTool, StructuredTool

from .client import GMTools
from .specs import as_text, specs


def get_tools(client: GMTools | None = None, **client_kwargs) -> list[BaseTool]:
    """All six tools (token and address safety, web reader, metadata, cheapest API, API check)."""
    client = client or GMTools(**client_kwargs)
    return [
        StructuredTool.from_function(func=partial(as_text, s.run), name=s.name, description=s.description, args_schema=s.args)
        for s in specs(client)
    ]
