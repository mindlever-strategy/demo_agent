from typing import Annotated, Optional, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: str
    session_id: str
    conversation_id: str
    current_agent: str
    query: str
    response: str
    provider: str
    model: str
    trace_id: str
    metric_ai_api_key: Optional[str]
