from providers import get_llm
from agents.messages import with_system_prompt


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


def execute(chat_messages: list, user_id: str, provider: str = "openai", model: str = None, metric_ai_api_key: str = None) -> str:
    llm = get_llm(provider=provider, model=model, temperature=0.3, max_tokens=500, metric_ai_api_key=metric_ai_api_key)
    messages = with_system_prompt(RESEARCH_PROMPT, chat_messages)
    response = llm.invoke(messages)
    return response.content


def stream_execute(chat_messages: list, user_id: str, provider: str = "openai", model: str = None, metric_ai_api_key: str = None):
    llm = get_llm(provider=provider, model=model, temperature=0.3, max_tokens=500, streaming=True, metric_ai_api_key=metric_ai_api_key)
    messages = with_system_prompt(RESEARCH_PROMPT, chat_messages)
    for chunk in llm.stream(messages):
        if chunk.content:
            yield chunk.content
