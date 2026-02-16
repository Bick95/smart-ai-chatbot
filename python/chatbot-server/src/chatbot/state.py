import operator

from langchain.messages import AnyMessage
from typing_extensions import Annotated, TypedDict


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

class AgentStateUpdate(AgentState, total=False):
    pass
