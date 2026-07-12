from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .config import Settings
from .knowledge import KnowledgeBase, SearchResult
from .llm import GeminiProvider, LLMUnavailableError
from .prompts import build_user_prompt


GREETING_PATTERN = re.compile(
    r"^(oi|olá|ola|bom dia|boa tarde|boa noite|e aí|eai|hello)[!,. ]*$",
    re.IGNORECASE
)


@dataclass(frozen=True)
class AssistantResponse:
    text: str
    sources: list[dict[str, Any]]
    confidence: float
    mode: str
    warning: str | None = None


class NexoPyAssistant:
    def __init__(
        self,
        settings: Settings | None = None,
        enable_llm: bool | None = None
    ) -> None:
        self.settings = settings or Settings()
        self.knowledge = KnowledgeBase(self.settings.knowledge_path)

        use_llm = (
            self.settings.gemini_enabled
            if enable_llm is None
            else enable_llm
        )

        self.llm = None
        self.llm_initialization_error: str | None = None

        if use_llm:
            try:
                self.llm = GeminiProvider(
                    api_key=self.settings.gemini_api_key,
                    model=self.settings.gemini_model
                )
            except (ValueError, LLMUnavailableError) as exc:
                self.llm_initialization_error = str(exc)

    @property
    def mode_name(self) -> str:
        return "Gemini + base local" if self.llm else "Base local"

    def answer(
        self,
        question: str,
        history: list[dict[str, str]] | None = None
    ) -> AssistantResponse:
        question = question.strip()

        if not question:
            return AssistantResponse(
                text="Digite uma pergunta para que eu possa ajudar.",
                sources=[],
                confidence=0.0,
                mode=self.mode_name
            )

        if GREETING_PATTERN.match(question):
            return AssistantResponse(
                text=(
                    "Olá! Eu sou o **NexoPy**. Posso ajudar com Python, "
                    "Pandas, automação, erros comuns, Git e fundamentos de IA. "
                    "Qual assunto você está estudando?"
                ),
                sources=[],
                confidence=1.0,
                mode=self.mode_name
            )

        results = self.knowledge.search(
            question,
            top_k=self.settings.top_k
        )

        relevant = [
            result for result in results
            if result.score >= self.settings.min_similarity
        ]

        if not relevant:
            return AssistantResponse(
                text=(
                    "Não encontrei informação suficiente na minha base de "
                    "conhecimento para responder com segurança. Atualmente, "
                    "posso ajudar com Python, Pandas, automação, ambientes "
                    "virtuais, Git e fundamentos de inteligência artificial."
                ),
                sources=[],
                confidence=results[0].score if results else 0.0,
                mode=self.mode_name
            )

        warning = None

        if self.llm:
            prompt = build_user_prompt(
                question=question,
                results=relevant,
                recent_history=history
            )
            try:
                response_text = self.llm.generate(prompt)
            except LLMUnavailableError as exc:
                warning = (
                    "A IA generativa ficou indisponível. A resposta abaixo "
                    "foi montada diretamente da base local."
                )
                response_text = self._build_local_answer(relevant)
        else:
            response_text = self._build_local_answer(relevant)

        return AssistantResponse(
            text=response_text,
            sources=[
                {
                    "id": result.item.id,
                    "titulo": result.item.titulo,
                    "categoria": result.item.categoria,
                    "score": round(result.score, 4)
                }
                for result in relevant
            ],
            confidence=relevant[0].score,
            mode=self.mode_name,
            warning=warning or self.llm_initialization_error
        )

    @staticmethod
    def _build_local_answer(results: list[SearchResult]) -> str:
        principal = results[0].item

        partes = [principal.resposta]

        if principal.exemplo:
            partes.append(f"**Exemplo:**\n```python\n{principal.exemplo}\n```")

        if principal.proximo_passo:
            partes.append(f"**Próximo passo:** {principal.proximo_passo}")

        return "\n\n".join(partes)
