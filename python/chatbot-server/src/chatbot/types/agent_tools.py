from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence, TypeAlias

from langchain_core.tools import BaseTool


Tool: TypeAlias = BaseTool
ToolName: TypeAlias = str
Tools: TypeAlias = Sequence[Tool]
ToolsByName: TypeAlias = Mapping[ToolName, Tool]

@dataclass(frozen=True, slots=True)
class AgentTools:
    tools: Tools
    tools_by_name: ToolsByName
