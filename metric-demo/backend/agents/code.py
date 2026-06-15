from langchain_core.messages import SystemMessage, HumanMessage
from providers import get_llm


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


def execute(query: str, user_id: str, provider: str = "openai", model: str = None) -> str:
    llm = get_llm(provider=provider, model=model, temperature=0.2, max_tokens=600)
    messages = [
        SystemMessage(content=CODE_PROMPT),
        HumanMessage(content=f"User ({user_id}) asks: {query}"),
    ]
    response = llm.invoke(messages)
    return response.content


def stream_execute(query: str, user_id: str, provider: str = "openai", model: str = None):
    llm = get_llm(provider=provider, model=model, temperature=0.2, max_tokens=600, streaming=True)
    messages = [
        SystemMessage(content=CODE_PROMPT),
        HumanMessage(content=f"User ({user_id}) asks: {query}"),
    ]
    for chunk in llm.stream(messages):
        if chunk.content:
            yield chunk.content
