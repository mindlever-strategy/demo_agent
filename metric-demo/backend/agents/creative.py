from langchain_core.messages import SystemMessage, HumanMessage
from providers import get_llm


CREATIVE_PROMPT = """You are a Creative Agent working inside an enterprise AI system.

Your responsibilities:
- Marketing copy and taglines
- Product naming and branding
- Brainstorming and ideation
- Content strategy
- Creative writing and storytelling

You produce engaging, original content with a focus on clarity and impact.
Offer multiple options when appropriate.
Keep responses under 200 words."""


def execute(query: str, user_id: str, provider: str = "openai", model: str = None) -> str:
    llm = get_llm(provider=provider, model=model, temperature=0.8, max_tokens=500)
    messages = [
        SystemMessage(content=CREATIVE_PROMPT),
        HumanMessage(content=f"User ({user_id}) asks: {query}"),
    ]
    response = llm.invoke(messages)
    return response.content


def stream_execute(query: str, user_id: str, provider: str = "openai", model: str = None):
    llm = get_llm(provider=provider, model=model, temperature=0.8, max_tokens=500, streaming=True)
    messages = [
        SystemMessage(content=CREATIVE_PROMPT),
        HumanMessage(content=f"User ({user_id}) asks: {query}"),
    ]
    for chunk in llm.stream(messages):
        if chunk.content:
            yield chunk.content
