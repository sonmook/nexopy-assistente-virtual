from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from time import monotonic

from .prompts import SYSTEM_PROMPT


class LLMUnavailableError(RuntimeError):
    """Erro usado quando o provedor generativo não pode responder."""


@dataclass
class GeminiProvider:
    api_key: str
    model: str
    max_prompt_chars: int = 20000
    max_output_tokens: int = 1024
    requests_per_minute: int = 10
    requests_per_day: int = 100
    _requests: deque = field(default_factory=deque, init=False, repr=False)
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def _reserve_request(self) -> None:
        # Reserva antes da chamada; erros também consomem a cota. Janela móvel.
        with self._lock:
            now = monotonic()
            while self._requests and now - self._requests[0] >= 86400:
                self._requests.popleft()
            minute_count = sum(now - stamp < 60 for stamp in self._requests)
            if (len(self._requests) >= self.requests_per_day
                    or minute_count >= self.requests_per_minute):
                raise LLMUnavailableError("Limite de uso generativo atingido.")
            self._requests.append(now)

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError("A chave da API Gemini não foi informada.")

        try:
            from google import genai
        except ImportError as exc:
            raise LLMUnavailableError(
                "Instale a dependência google-genai para usar o modo generativo."
            ) from exc

        self._client = genai.Client(api_key=self.api_key)

    def generate(self, prompt: str) -> str:
        if len(prompt) > self.max_prompt_chars:
            raise LLMUnavailableError("O contexto excedeu o limite generativo.")
        self._reserve_request()
        try:
            interaction = self._client.interactions.create(
                model=self.model,
                timeout=45,
                system_instruction=SYSTEM_PROMPT,
                input=prompt,
                store=False,
                generation_config={
                    "temperature": 0.2,
                    "thinking_level": "low",
                    "max_output_tokens": self.max_output_tokens
                }
            )
        except Exception as exc:
            raise LLMUnavailableError(
                "O provedor generativo não respondeu."
            ) from exc

        if interaction.status != "completed":
            raise LLMUnavailableError("O provedor não concluiu a resposta.")

        # SDK 2.x expõe o texto final calculado a partir dos steps.
        output = interaction.output_text
        if not output or not output.strip():
            raise LLMUnavailableError("O provedor retornou uma resposta vazia.")

        return output.strip()
