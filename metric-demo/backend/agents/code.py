from providers import get_llm
from agents.messages import with_system_prompt


CODE_PROMPT = """You are a Code Agent working inside an enterprise AI system.

Your responsibilities:
- Code generation and architecture guidance
- Debugging and error analysis
- Technical design review
- Algorithm explanations
- Best practices and patterns

You provide clean, well-structured code examples and technical explanations.
Always specify the language and keep code concise but complete.
Keep responses under 250 words."""


def execute(chat_messages: list, user_id: str, provider: str = "openai", model: str = None, metric_ai_api_key: str = None) -> str:
    llm = get_llm(provider=provider, model=model, temperature=0.2, max_tokens=600, metric_ai_api_key=metric_ai_api_key)
    messages = with_system_prompt(CODE_PROMPT, chat_messages)
    response = llm.invoke(messages)
    return response.content


def stream_execute(chat_messages: list, user_id: str, provider: str = "openai", model: str = None, metric_ai_api_key: str = None):
    llm = get_llm(provider=provider, model=model, temperature=0.2, max_tokens=600, streaming=True, metric_ai_api_key=metric_ai_api_key)
    messages = with_system_prompt(CODE_PROMPT, chat_messages)
    for chunk in llm.stream(messages):
        if chunk.content:
            yield chunk.content
