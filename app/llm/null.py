"""The fallback provider used when no LLM is configured."""

from app.llm.base import LLMProvider, LLMResult, LLMUnavailable


class NullProvider(LLMProvider):
    name = "none"

    @property
    def available(self) -> bool:
        return False

    def complete(self, *, system: str, prompt: str, max_tokens: int = 700) -> LLMResult:
        raise LLMUnavailable("No LLM provider is configured.")
