from langchain_core.messages import SystemMessage


def with_system_prompt(system_prompt: str, chat_messages: list) -> list:
    return [SystemMessage(content=system_prompt)] + list(chat_messages)
