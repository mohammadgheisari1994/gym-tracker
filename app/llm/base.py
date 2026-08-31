"""LLM provider interface.

Providers are thin wrappers over a chat-completion endpoint. The application
only ever calls ``complete``; prompts are built by the service layer, never by
the user.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


class LLMUnavailable(RuntimeError):
    """Raised when a completion is attempted with no usable provider."""


@dataclass(frozen=True)
class LLMResult:
    text: str
    provider: str
    model: str


class LLMProvider(ABC):
    name: str = "base"

    @property
    @abstractmethod
    def available(self) -> bool:
        """Whether this provider is configured well enough to be called."""

    @abstractmethod
    def complete(self, *, system: str, prompt: str, max_tokens: int = 700) -> LLMResult:
        """Return a completion, or raise ``LLMUnavailable`` / a transport error."""
