import os
import uuid
import threading
import logging
from typing import Optional

import httpx

_LOG = logging.getLogger(__name__)

METRICAI_BASE_URL = "https://proxy.metricai.co.in"
METRICAI_EVENTS_PATH = "/v1/sdk/events"

_http_client: Optional[httpx.Client] = None
_lock = threading.Lock()


def _get_http_client() -> httpx.Client:
    global _http_client
    if _http_client is None:
        with _lock:
            if _http_client is None:
                _http_client = httpx.Client(timeout=5.0)
    return _http_client


def _send_event(payload: dict):
    api_key = os.getenv("METRIC_AI_API_KEY", "")
    if not api_key:
        return
    idempotency_key = str(uuid.uuid4())
    headers = {
        "X-MetricAI-API-Key": api_key,
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key,
    }
    url = f"{METRICAI_BASE_URL}{METRICAI_EVENTS_PATH}"
    try:
        client = _get_http_client()
        resp = client.post(url, json=payload, headers=headers)
        if resp.status_code >= 400:
            _LOG.warning("MetricAI track failed: %s %s", resp.status_code, resp.text[:200])
    except Exception as e:
        _LOG.debug("MetricAI track error: %s", e)


def _track_async(payload: dict):
    t = threading.Thread(target=_send_event, args=(payload,), daemon=True)
    t.start()


def register_user(user_id: str, name: str, role: str):
    pass


def register_session(session_id: str, user_id: str):
    pass


def track_agent_execution(
    user_id: str,
    session_id: str,
    agent_name: str,
    agent_id: str,
    query: str,
    response: str,
    execution_time: float,
    provider: str = "openai",
    model: str = "gpt-4o-mini",
):
    payload = {
        "event_type": "turn",
        "provider": provider,
        "model": model,
        "agent_id": agent_id,
        "user_id": user_id,
        "session_id": session_id,
        "latency_ms": int(execution_time * 1000),
        "input_tokens": len(query.split()) * 2,
        "output_tokens": len(response.split()) * 2,
        "agent_name": agent_name,
        "query": query[:200],
    }
    _track_async(payload)


AGENT_ID_MAP = {
    "finance_agent": "agt_finance",
    "research_agent": "agt_research",
    "reporting_agent": "agt_reporting",
    "code_agent": "agt_code",
    "creative_agent": "agt_creative",
}

def track_workflow(
    user_id: str,
    session_id: str,
    query: str,
    routed_agent: str,
    total_execution_time: float,
    provider: str = "openai",
    model: str = "gpt-4o-mini",
):
    agent_id = AGENT_ID_MAP.get(routed_agent, routed_agent)
    payload = {
        "event_type": "turn",
        "provider": provider,
        "model": model,
        "input_tokens": len(query.split()) * 2,
        "output_tokens": 5,
        "agent_id": agent_id,
        "user_id": user_id,
        "session_id": session_id,
        "latency_ms": int(total_execution_time * 1000),
        "workflow": "routing",
        "selected_agent": routed_agent,
    }
    _track_async(payload)
