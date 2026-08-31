"""LLM provider wiring.

The application never lets a user type a prompt; the service layer builds every
prompt and calls ``get_provider().complete(...)``.
"""

from functools import lru_cache

from app.config import get_settings
from app.llm.base import LLMProvider, LLMResult, LLMUnavailable
from app.llm.http_provider import HttpChatProvider
from app.llm.null import NullProvider

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
_DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
_DEFAULT_OLLAMA_MODEL = "llama3.1"

__all__ = ["LLMProvider", "LLMResult", "LLMUnavailable", "get_provider"]


@lru_cache
def get_provider() -> LLMProvider:
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider == "groq":
        return HttpChatProvider(
            name="groq",
            base_url=_GROQ_BASE_URL,
            model=settings.llm_model or _DEFAULT_GROQ_MODEL,
            api_key=settings.llm_api_key,
            requires_key=True,
        )

    if provider == "ollama":
        return HttpChatProvider(
            name="ollama",
            base_url=f"{settings.llm_base_url.rstrip('/')}/v1",
            model=settings.llm_model or _DEFAULT_OLLAMA_MODEL,
        )

    return NullProvider()
