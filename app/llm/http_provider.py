"""Chat-completion provider for any OpenAI-compatible endpoint (Groq, Ollama)."""

import httpx

from app.llm.base import LLMProvider, LLMResult, LLMUnavailable

_TIMEOUT = httpx.Timeout(45.0)


class HttpChatProvider(LLMProvider):
    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        model: str,
        api_key: str = "",
        requires_key: bool = False,
    ) -> None:
        self.name = name
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._requires_key = requires_key

    @property
    def available(self) -> bool:
        if not self._base_url or not self._model:
            return False
        return bool(self._api_key) or not self._requires_key

    def complete(self, *, system: str, prompt: str, max_tokens: int = 700) -> LLMResult:
        if not self.available:
            raise LLMUnavailable(f"Provider '{self.name}' is not configured.")

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.4,
        }

        response = httpx.post(
            f"{self._base_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        message = response.json()["choices"][0]["message"]["content"]
        return LLMResult(text=message.strip(), provider=self.name, model=self._model)
