from langchain_core.messages import SystemMessage, HumanMessage
from providers import get_llm


FINANCE_PROMPT = """You are a Finance Agent working inside an enterprise AI system.

Your responsibilities:
- Revenue analysis
- Cost analysis
- Profitability analysis
- Financial forecasting
- Budget planning

You have access to internal financial data. Provide concise, data-driven insights.
Always respond professionally and include specific numbers when possible.
Keep responses under 200 words."""


def execute(query: str, user_id: str, provider: str = "openai", model: str = None) -> str:
    llm = get_llm(provider=provider, model=model, temperature=0.3, max_tokens=500)
    messages = [
        SystemMessage(content=FINANCE_PROMPT),
        HumanMessage(content=f"User ({user_id}) asks: {query}"),
    ]
    response = llm.invoke(messages)
    return response.content


def stream_execute(query: str, user_id: str, provider: str = "openai", model: str = None):
    llm = get_llm(provider=provider, model=model, temperature=0.3, max_tokens=500, streaming=True)
    messages = [
        SystemMessage(content=FINANCE_PROMPT),
        HumanMessage(content=f"User ({user_id}) asks: {query}"),
    ]
    for chunk in llm.stream(messages):
        if chunk.content:
            yield chunk.content
