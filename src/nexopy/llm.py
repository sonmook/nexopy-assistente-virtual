from __future__ import annotations

from dataclasses import dataclass

from .prompts import SYSTEM_PROMPT


class LLMUnavailableError(RuntimeError):
    """Erro usado quando o provedor generativo não pode responder."""


@dataclass
class GeminiProvider:
    api_key: str
    model: str

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
        try:
            interaction = self._client.interactions.create(
                model=self.model,
                system_instruction=SYSTEM_PROMPT,
                input=prompt,
                generation_config={
                    "temperature": 0.2,
                    "thinking_level": "low"
                }
            )
        except Exception as exc:
            raise LLMUnavailableError(
                "O provedor generativo não respondeu."
            ) from exc

        output = "\n\n".join(
            block.text.strip()
            for block in (interaction.outputs or [])
            if block.type == "text" and block.text.strip()
        )
        if not output or not output.strip():
            raise LLMUnavailableError("O provedor retornou uma resposta vazia.")

        return output.strip()
