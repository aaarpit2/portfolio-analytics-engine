"""
LLM client, provider-switchable via LLM_PROVIDER in .env ("anthropic" or "openai").

Both providers get the same SYSTEM_PROMPT and grounded context — only the SDK call
and response parsing differ. Everything upstream (analytics, retriever, guardrails,
routes) is unaffected by which provider is active.
"""

from app.config import settings
from app.rag.prompt_templates import SYSTEM_PROMPT, build_user_prompt

_anthropic_client = None
_openai_client = None


def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        from anthropic import Anthropic

        _anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI

        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _generate_anthropic(context: str) -> str:
    client = _get_anthropic_client()
    message = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_prompt(context)}],
    )
    return "".join(block.text for block in message.content if block.type == "text")


def _generate_openai(context: str) -> str:
    client = _get_openai_client()
    response = client.chat.completions.create(
        model=settings.openai_model,
        max_completion_tokens=600,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(context)},
        ],
    )
    return response.choices[0].message.content or ""


def generate_summary(context: str) -> str:
    provider = settings.llm_provider.lower()

    if provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError(
                "LLM_PROVIDER is 'openai' but OPENAI_API_KEY is not set in .env"
            )
        return _generate_openai(context)

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError(
                "LLM_PROVIDER is 'anthropic' but ANTHROPIC_API_KEY is not set in .env"
            )
        return _generate_anthropic(context)

    raise ValueError(
        f"Unknown LLM_PROVIDER '{provider}' — expected 'anthropic' or 'openai'"
    )
