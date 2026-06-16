from providers import get_llm
from agents.messages import with_system_prompt


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


def execute(chat_messages: list, user_id: str, provider: str = "openai", model: str = None, metric_ai_api_key: str = None) -> str:
    llm = get_llm(provider=provider, model=model, temperature=0.3, max_tokens=500, metric_ai_api_key=metric_ai_api_key)
    messages = with_system_prompt(FINANCE_PROMPT, chat_messages)
    response = llm.invoke(messages)
    return response.content


def stream_execute(chat_messages: list, user_id: str, provider: str = "openai", model: str = None, metric_ai_api_key: str = None):
    llm = get_llm(provider=provider, model=model, temperature=0.3, max_tokens=500, streaming=True, metric_ai_api_key=metric_ai_api_key)
    messages = with_system_prompt(FINANCE_PROMPT, chat_messages)
    for chunk in llm.stream(messages):
        if chunk.content:
            yield chunk.content
