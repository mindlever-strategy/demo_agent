from typing import TypedDict, Optional


class AgentState(TypedDict):
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
