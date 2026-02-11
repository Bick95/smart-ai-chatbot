from src.chatbot.state import AgentState, AgentStateUpdate
from typing import Awaitable, Callable, TypeAlias, Union
from langchain_core.runnables import Runnable


NodeUpdate: TypeAlias = AgentStateUpdate
NodeReturn: TypeAlias = Union[NodeUpdate, Awaitable[NodeUpdate]]
NodeFn: TypeAlias = Callable[[AgentState], NodeReturn]

NodeLike: TypeAlias = Union[NodeFn, Runnable]  # widen to accept runnables
AgentNodes: TypeAlias = dict[str, NodeLike]
