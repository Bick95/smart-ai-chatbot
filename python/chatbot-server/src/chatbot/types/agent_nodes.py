from typing import Awaitable, Callable, TypeAlias, Union

from langchain_core.runnables import Runnable

from src.chatbot.state import AgentState, AgentStateUpdate

NodeUpdate: TypeAlias = AgentStateUpdate
NodeReturn: TypeAlias = Union[NodeUpdate, Awaitable[NodeUpdate]]
NodeFn: TypeAlias = Callable[[AgentState], NodeReturn]

NodeLike: TypeAlias = Union[NodeFn, Runnable]
AgentNodes: TypeAlias = dict[str, NodeLike]
