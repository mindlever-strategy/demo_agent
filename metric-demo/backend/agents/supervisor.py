from langchain_core.messages import SystemMessage, HumanMessage
from providers import get_llm


ROUTING_PROMPT = """You are a supervisor agent that routes user queries to the appropriate specialist agent.

You must respond with EXACTLY one of these agent names:
- finance_agent
- research_agent
- reporting_agent
- code_agent
- creative_agent

Routing rules:
- finance_agent: revenue, cost, profit, budget, financial forecasts, pricing, margins, client profitability, accounting
- research_agent: data analysis, investigation, market research, competitor analysis, trends, deep dives, studies
- reporting_agent: executive summaries, reports, recommendations, status updates, presentations, dashboards
- code_agent: code generation, debugging, architecture, programming, algorithms, technical design, APIs, databases
- creative_agent: marketing copy, naming, brainstorming, creative writing, taglines, branding, content ideas

Respond with ONLY the agent name, nothing else."""


def route_query(
    query: str,
    provider: str = "openai",
    model: str = None,
    chat_history: list | None = None,
    metric_ai_api_key: str = None,
) -> str:
    llm = get_llm(
        provider=provider,
        model=model,
        temperature=0,
        max_tokens=20,
        metric_ai_api_key=metric_ai_api_key,
    )
    messages = [SystemMessage(content=ROUTING_PROMPT)]
    if chat_history:
        messages.extend(chat_history)
    messages.append(HumanMessage(content=query))
    response = llm.invoke(messages)
    agent_name = response.content.strip().lower()

    valid_agents = ["finance_agent", "research_agent", "reporting_agent", "code_agent", "creative_agent"]
    if agent_name not in valid_agents:
        agent_name = "research_agent"

    return agent_name
