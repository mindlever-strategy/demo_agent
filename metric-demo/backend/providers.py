import os
from typing import Any, Dict, Optional

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "models": ["gpt-4o", "gpt-4o-mini"],
        "default_model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "models": ["claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
        "default_model": "claude-sonnet-4-6",
        "env_key": "ANTHROPIC_API_KEY",
    },
    "gemini": {
        "name": "Google Gemini",
        "models": ["gemini-2.5-flash", "gemini-2.5-pro"],
        "default_model": "gemini-2.5-flash",
        "env_key": "GEMINI_API_KEY",
    },
    "grok": {
        "name": "xAI Grok",
        "models": ["grok-3-mini", "grok-3"],
        "default_model": "grok-3-mini",
        "env_key": "GROK_API_KEY",
    },
}

# llm_keys dict keys for BYOK header mapping.
_BYOK_KEY_NAME = {
    "openai": "openai",
    "anthropic": "anthropic",
    "gemini": "gemini",
    "grok": "grok",
}


def get_available_providers():
    available = {}
    for key, config in PROVIDERS.items():
        env_val = os.getenv(config["env_key"])
        available[key] = {
            "name": config["name"],
            "models": config["models"],
            "default_model": config["default_model"],
            "available": bool(env_val),
        }
    return available


def _get_metricai_client(metric_ai_api_key: Optional[str] = None):
    override = (metric_ai_api_key or "").strip()
    if override:
        from metricai import MetricAIClient

        return MetricAIClient(api_key=override)

    try:
        import metricai

        return metricai.get_metricai()
    except Exception:
        return None


def _byok_headers(provider: str) -> Dict[str, str]:
    from metricai.config import llm_keys_to_proxy_headers

    env_key = PROVIDERS.get(provider, PROVIDERS["openai"])["env_key"]
    secret = os.getenv(env_key, "").strip()
    if not secret:
        return {}
    return llm_keys_to_proxy_headers({_BYOK_KEY_NAME[provider]: secret})


def _proxy_headers(provider: str, metric_ai_api_key: Optional[str] = None) -> Optional[Dict[str, str]]:
    client = _get_metricai_client(metric_ai_api_key)
    if client is None:
        return None

    from metricai.context import get_attribution

    attr = get_attribution()
    headers = client.headers(
        agent_id=attr.agent_id,
        user_id=attr.user_id,
        session_id=attr.session_id,
    )
    headers.update(_byok_headers(provider))
    return headers


def _metricai_llm(
    provider: str,
    model: str,
    temperature: float,
    max_tokens: int,
    streaming: bool,
    metric_ai_api_key: Optional[str] = None,
):
    client = _get_metricai_client(metric_ai_api_key)
    if client is None:
        return None

    headers = _proxy_headers(provider, metric_ai_api_key)
    if headers is None:
        return None

    if provider == "anthropic":
        from metricai.integrations.langchain_chat import ChatMetricAI

        llm = ChatMetricAI(
            model=model,
            metricai_api_key=client._api_key,
            provider="claude",
            extra_proxy_headers=headers,
        )
        return llm.bind(temperature=temperature, max_tokens=max_tokens)

    llm = ChatOpenAI(
        model=model,
        api_key=client._api_key,
        base_url=client.config.proxy_url_for(provider),
        default_headers=headers,
        streaming=streaming,
    )
    return llm.bind(temperature=temperature, max_tokens=max_tokens)


def _direct_llm(
    provider: str,
    model: str,
    temperature: float,
    max_tokens: int,
    streaming: bool,
):
    if provider == "anthropic":
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=streaming,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
    if provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            max_output_tokens=max_tokens,
            streaming=streaming,
            google_api_key=os.getenv("GEMINI_API_KEY"),
        )
    if provider == "grok":
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=streaming,
            api_key=os.getenv("GROK_API_KEY"),
            base_url="https://api.x.ai/v1",
        )
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=streaming,
    )


def get_llm(
    provider: str = "openai",
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 500,
    streaming: bool = False,
    metric_ai_api_key: Optional[str] = None,
) -> Any:
    provider_config = PROVIDERS.get(provider, PROVIDERS["openai"])
    if not model:
        model = provider_config["default_model"]

    metricai_llm = _metricai_llm(
        provider, model, temperature, max_tokens, streaming, metric_ai_api_key
    )
    if metricai_llm is not None:
        return metricai_llm

    return _direct_llm(provider, model, temperature, max_tokens, streaming)
