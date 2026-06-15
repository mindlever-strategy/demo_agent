import time
import uuid
import json
from typing import Dict
from pathlib import Path
from datetime import datetime, timezone

from langgraph.graph import StateGraph, END

from state import AgentState
from agents.supervisor import route_query
from agents.finance import execute as finance_execute, stream_execute as finance_stream
from agents.research import execute as research_execute, stream_execute as research_stream
from agents.reporting import execute as reporting_execute, stream_execute as reporting_stream
from agents.code import execute as code_execute, stream_execute as code_stream
from agents.creative import execute as creative_execute, stream_execute as creative_stream
from metric_ai_wrapper import track_agent_execution, track_workflow
from storage import load_json, save_json

AGENT_DISPLAY_NAMES = {
    "finance_agent": "Finance Agent",
    "research_agent": "Research Agent",
    "reporting_agent": "Reporting Agent",
    "code_agent": "Code Agent",
    "creative_agent": "Creative Agent",
}

AGENT_IDS = {
    "finance_agent": "agt_finance",
    "research_agent": "agt_research",
    "reporting_agent": "agt_reporting",
    "code_agent": "agt_code",
    "creative_agent": "agt_creative",
}


def save_trace(trace: dict):
    traces = load_json("traces.json")
    traces.append(trace)
    save_json("traces.json", traces)


def supervisor_node(state: AgentState) -> Dict:
    query = state["query"]
    provider = state.get("provider", "openai")
    model = state.get("model", None)
    selected_agent = route_query(query, provider=provider, model=model)
    return {
        "current_agent": selected_agent,
    }


def _execute_agent(agent_key: str, execute_fn, state: AgentState) -> Dict:
    from providers import PROVIDERS
    start = time.time()
    provider = state.get("provider", "openai")
    model = state.get("model", None)
    if not model:
        provider_config = PROVIDERS.get(provider, PROVIDERS["openai"])
        model = provider_config["default_model"]
    response = execute_fn(state["query"], state["user_id"], provider=provider, model=model)
    execution_time = time.time() - start

    used_model = model
    trace_id = state.get("trace_id", f"trc_{uuid.uuid4().hex[:8]}")

    trace = {
        "trace_id": trace_id,
        "user_id": state["user_id"],
        "session_id": state["session_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": state["query"],
        "provider": provider,
        "model": used_model,
        "supervisor_decision": agent_key,
        "agent_id": AGENT_IDS[agent_key],
        "agent_name": AGENT_DISPLAY_NAMES[agent_key],
        "execution_time_ms": round(execution_time * 1000),
        "response": response[:200],
        "metricai_logged": True,
    }
    save_trace(trace)

    track_agent_execution(
        user_id=state["user_id"],
        session_id=state["session_id"],
        agent_name=AGENT_DISPLAY_NAMES[agent_key],
        agent_id=AGENT_IDS[agent_key],
        query=state["query"],
        response=response,
        execution_time=execution_time,
        provider=provider,
        model=used_model,
        metric_ai_api_key=state.get("metric_ai_api_key"),
    )
    return {"response": response}


def finance_node(state: AgentState) -> Dict:
    return _execute_agent("finance_agent", finance_execute, state)


def research_node(state: AgentState) -> Dict:
    return _execute_agent("research_agent", research_execute, state)


def reporting_node(state: AgentState) -> Dict:
    return _execute_agent("reporting_agent", reporting_execute, state)


def code_node(state: AgentState) -> Dict:
    return _execute_agent("code_agent", code_execute, state)


def creative_node(state: AgentState) -> Dict:
    return _execute_agent("creative_agent", creative_execute, state)


def route_to_agent(state: AgentState) -> str:
    return state["current_agent"]


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("finance_agent", finance_node)
    workflow.add_node("research_agent", research_node)
    workflow.add_node("reporting_agent", reporting_node)
    workflow.add_node("code_agent", code_node)
    workflow.add_node("creative_agent", creative_node)

    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "finance_agent": "finance_agent",
            "research_agent": "research_agent",
            "reporting_agent": "reporting_agent",
            "code_agent": "code_agent",
            "creative_agent": "creative_agent",
        },
    )

    workflow.add_edge("finance_agent", END)
    workflow.add_edge("research_agent", END)
    workflow.add_edge("reporting_agent", END)
    workflow.add_edge("code_agent", END)
    workflow.add_edge("creative_agent", END)

    return workflow.compile()


agent_graph = build_graph()


def run_workflow(user_id: str, session_id: str, query: str, provider: str = "openai", model: str = None, metric_ai_api_key: str = None) -> Dict:
    from providers import PROVIDERS
    start = time.time()
    trace_id = f"trc_{uuid.uuid4().hex[:8]}"
    provider_config = PROVIDERS.get(provider, PROVIDERS["openai"])
    used_model = model or provider_config["default_model"]

    initial_state: AgentState = {
        "user_id": user_id,
        "session_id": session_id,
        "conversation_id": "",
        "current_agent": "",
        "query": query,
        "response": "",
        "provider": provider,
        "model": used_model,
        "trace_id": trace_id,
        "metric_ai_api_key": metric_ai_api_key,
    }

    result = agent_graph.invoke(initial_state)
    total_time = time.time() - start

    track_workflow(
        user_id=user_id,
        session_id=session_id,
        query=query,
        routed_agent=result["current_agent"],
        total_execution_time=total_time,
        provider=provider,
        model=used_model,
        metric_ai_api_key=metric_ai_api_key,
    )

    return {
        "agent": AGENT_DISPLAY_NAMES.get(result["current_agent"], result["current_agent"]),
        "agent_id": AGENT_IDS.get(result["current_agent"], "unknown"),
        "response": result["response"],
        "execution_time": round(total_time, 2),
        "trace_id": trace_id,
        "provider": provider,
        "model": used_model,
        "execution_time_ms": round(total_time * 1000),
    }


AGENT_STREAM_FNS = {
    "finance_agent": finance_stream,
    "research_agent": research_stream,
    "reporting_agent": reporting_stream,
    "code_agent": code_stream,
    "creative_agent": creative_stream,
}


def stream_workflow(user_id: str, session_id: str, query: str, provider: str = "openai", model: str = None, metric_ai_api_key: str = None):
    """Route the query then return (agent_name, agent_id, token_generator)."""
    from providers import PROVIDERS
    provider_config = PROVIDERS.get(provider, PROVIDERS["openai"])
    used_model = model or provider_config["default_model"]
    selected_agent = route_query(query, provider=provider, model=used_model)

    agent_name = AGENT_DISPLAY_NAMES.get(selected_agent, selected_agent)
    agent_id = AGENT_IDS.get(selected_agent, "unknown")
    stream_fn = AGENT_STREAM_FNS[selected_agent]

    def token_generator():
        full_response = []
        start = time.time()
        for token in stream_fn(query, user_id, provider=provider, model=used_model):
            full_response.append(token)
            yield token

        execution_time = time.time() - start
        response_text = "".join(full_response)

        trace_id = f"trc_{uuid.uuid4().hex[:8]}"
        trace = {
            "trace_id": trace_id,
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "provider": provider,
            "model": used_model,
            "supervisor_decision": selected_agent,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "execution_time_ms": round(execution_time * 1000),
            "response": response_text[:200],
            "metricai_logged": True,
        }
        save_trace(trace)

        track_agent_execution(
            user_id=user_id,
            session_id=session_id,
            agent_name=agent_name,
            agent_id=agent_id,
            query=query,
            response=response_text,
            execution_time=execution_time,
            provider=provider,
            model=used_model,
            metric_ai_api_key=metric_ai_api_key,
        )

        track_workflow(
            user_id=user_id,
            session_id=session_id,
            query=query,
            routed_agent=selected_agent,
            total_execution_time=execution_time,
            provider=provider,
            model=used_model,
            metric_ai_api_key=metric_ai_api_key,
        )

    return agent_name, agent_id, token_generator()
