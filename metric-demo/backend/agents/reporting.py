from langchain_core.messages import SystemMessage, HumanMessage
from providers import get_llm


REPORTING_PROMPT = """You are a Reporting Agent working inside an enterprise AI system.

Your responsibilities:
- Executive summaries
- Status reports
- Strategic recommendations
- Presentation content
- Action item generation

You produce clear, structured outputs suitable for leadership review.
Use bullet points and clear headers where appropriate.
Keep responses under 200 words."""


def execute(query: str, user_id: str, provider: str = "openai", model: str = None) -> str:
    llm = get_llm(provider=provider, model=model, temperature=0.3, max_tokens=500)
    messages = [
        SystemMessage(content=REPORTING_PROMPT),
        HumanMessage(content=f"User ({user_id}) asks: {query}"),
    ]
    response = llm.invoke(messages)
    return response.content


def stream_execute(query: str, user_id: str, provider: str = "openai", model: str = None):
    llm = get_llm(provider=provider, model=model, temperature=0.3, max_tokens=500, streaming=True)
    messages = [
        SystemMessage(content=REPORTING_PROMPT),
        HumanMessage(content=f"User ({user_id}) asks: {query}"),
    ]
    for chunk in llm.stream(messages):
        if chunk.content:
            yield chunk.content
