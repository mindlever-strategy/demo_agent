from langchain_core.messages import SystemMessage, HumanMessage
from providers import get_llm


RESEARCH_PROMPT = """You are a Research Agent working inside an enterprise AI system.

Your responsibilities:
- Data retrieval and analysis
- Market investigation
- Competitor research
- Trend analysis
- Deep-dive investigations

You have access to internal research databases. Provide thorough, evidence-based insights.
Always cite your reasoning and present findings clearly.
Keep responses under 200 words."""


def execute(query: str, user_id: str, provider: str = "openai", model: str = None) -> str:
    llm = get_llm(provider=provider, model=model, temperature=0.3, max_tokens=500)
    messages = [
        SystemMessage(content=RESEARCH_PROMPT),
        HumanMessage(content=f"User ({user_id}) asks: {query}"),
    ]
    response = llm.invoke(messages)
    return response.content


def stream_execute(query: str, user_id: str, provider: str = "openai", model: str = None):
    llm = get_llm(provider=provider, model=model, temperature=0.3, max_tokens=500, streaming=True)
    messages = [
        SystemMessage(content=RESEARCH_PROMPT),
        HumanMessage(content=f"User ({user_id}) asks: {query}"),
    ]
    for chunk in llm.stream(messages):
        if chunk.content:
            yield chunk.content
