"""CrewAI tools. Usage:

    from gm_x402_tools.crewai import get_tools
    agent = Agent(role="Trader", goal="...", tools=get_tools())
"""

from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool

from .client import GMTools
from .specs import Spec, as_text, specs


def _tool(spec: Spec) -> BaseTool:
    class _GMTool(BaseTool):
        name: str = spec.name
        description: str = spec.description
        args_schema: type = spec.args

        def _run(self, **kwargs: Any) -> str:
            return as_text(spec.run, **kwargs)

    _GMTool.__name__ = "".join(p.title() for p in spec.name.split("_")) + "Tool"
    return _GMTool()


def get_tools(client: GMTools | None = None, **client_kwargs) -> list[BaseTool]:
    """All six tools (token and address safety, web reader, metadata, cheapest API, API check)."""
    client = client or GMTools(**client_kwargs)
    return [_tool(s) for s in specs(client)]
