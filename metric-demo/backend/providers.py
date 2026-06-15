import os
from typing import Optional

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
        "models": ["claude-sonnet-4-20250514"],
        "default_model": "claude-sonnet-4-20250514",
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


def get_llm(
    provider: str = "openai",
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 500,
    streaming: bool = False,
):
    provider_config = PROVIDERS.get(provider, PROVIDERS["openai"])
    if not model:
        model = provider_config["default_model"]

    if provider == "anthropic":
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=streaming,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
    elif provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            max_output_tokens=max_tokens,
            streaming=streaming,
            google_api_key=os.getenv("GEMINI_API_KEY"),
        )
    elif provider == "grok":
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=streaming,
            api_key=os.getenv("GROK_API_KEY"),
            base_url="https://api.x.ai/v1",
        )
    else:
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=streaming,
        )
