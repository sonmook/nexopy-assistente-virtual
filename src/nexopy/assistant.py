from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Literal

from .config import Settings
from .knowledge import KnowledgeBase, SearchResult
from .llm import GeminiProvider, LLMUnavailableError
from .prompts import build_user_prompt


GREETING_PATTERN = re.compile(
    r"^(oi|olá|ola|bom dia|boa tarde|boa noite|e aí|eai|hello)[!,. ]*$", re.IGNORECASE
)


# Heurísticas de intenção: operações sobre dados não são pedidos de previsão
# ou diagnóstico. Pedidos externos explícitos e desvios têm precedência.
EXTERNAL_TOPIC = re.compile(
    r"\b(previsao do tempo|clima|loteria|eleicao|horoscopo|diagnostico|investir|calorias|nutricao|dieta)\b"
)
EXTERNAL_REQUEST = re.compile(
    r"\b(?:qual sera|como estara).{0,30}\b(?:clima|tempo)\b"
    r"|\b(?:preveja|prever|vai chover)\b|\b(?:qual|diga|informe).{0,20}\bprevisao\b"
    r"|\b(?:quem).{0,30}\b(?:vencera|ganhara)\b"
    r"|\b(?:quais|preveja).{0,30}\b(?:numeros|resultado).{0,30}loteria\b"
    r"|\b(?:qual|diga|forneca).{0,25}\bdiagnostico\b|\bdiagnostique\b"
    r"|\bcomo investir\b|\bficar rico\b"
    r"|\bqual (?:o|a) (?:total|quantidade)\b.{0,25}\bcalorias\b"
    r"|\bquantas calorias\b|\b(?:recomende|prescreva)\b.{0,30}\b(?:calorias|dieta)\b"
)
PROGRAMMING_OPERATION = re.compile(
    r"\b(?:ler|carregar|abrir|salvar|filtrar|agrupar|ordenar|contar|criar|validar|analisar|somar|calcular)\b"
    r".{0,60}\b(?:csv|json|arquivo|dataframe|coluna|linhas|tabela|funcao|variavel)\b"
)
OVERRIDE_INTENT = re.compile(
    r"\b(?:ignore|desconsidere|esqueca)\b.{0,80}\b(?:instruc|base|contexto|regra)"
    r"|\b(?:revele|mostre|exiba|imprima|exponha)\b.{0,60}"
    r"\b(?:chave de api|token secreto|senha|sua chave|seu token)\b"
    r"|\b(?:invente|inventa)\b.{0,30}\bfontes\b"
)
FOLLOW_UP = re.compile(
    r"(?:(?:pode|voce pode|poderia) )?(?:dar|mostrar|mostre|de|me de) "
    r"(?:um |outro |mais um )?exemplo"
    r"|(?:(?:pode|voce pode|poderia) )?(?:explicar|explique) (?:melhor|de novo)"
    r"|(?:e )?(?:como (?:faco|fazer) )?isso (?:no|na|em) (?:linux|windows|macos)"
    r"|e agora|nao deu certo"
)
AMBIGUOUS = re.compile(r"(?:como |pode )?(?:instalar|usar|fazer|corrigir) (?:isso|isto)")


def normalize(text: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", text.casefold())
        if not unicodedata.combining(char)
    ).strip(" ?!.\n")


@dataclass(frozen=True)
class AssistantResponse:
    text: str
    sources: list[dict[str, Any]]
    confidence: float
    mode: str
    warning: str | None = None
    action: Literal["answer", "refuse", "clarify"] = "answer"


class NexoPyAssistant:
    def __init__(self, settings: Settings | None = None, enable_llm: bool | None = None) -> None:
        self.settings = settings or Settings()
        self.knowledge = KnowledgeBase(self.settings.knowledge_path)

        use_llm = self.settings.gemini_enabled if enable_llm is None else enable_llm

        self.llm = None
        self.llm_initialization_error: str | None = None

        if use_llm:
            try:
                self.llm = GeminiProvider(
                    api_key=self.settings.gemini_api_key, model=self.settings.gemini_model,
                    max_prompt_chars=self.settings.max_prompt_chars,
                    max_output_tokens=self.settings.gemini_max_output_tokens,
                    requests_per_minute=self.settings.gemini_requests_per_minute,
                    requests_per_day=self.settings.gemini_requests_per_day,
                )
            except (ValueError, LLMUnavailableError) as exc:
                self.llm_initialization_error = str(exc)

    @property
    def mode_name(self) -> str:
        return "Gemini + base local" if self.llm else "Base local"

    def answer(
        self, question: str, history: list[dict[str, str]] | None = None
    ) -> AssistantResponse:
        if len(question) > self.settings.max_question_chars:
            return AssistantResponse(
                text=f"Envie uma pergunta de até {self.settings.max_question_chars} caracteres.",
                sources=[], confidence=0.0, mode="Base local", action="clarify",
            )
        question = question.strip()

        if not question:
            return AssistantResponse(
                text="Digite uma pergunta para que eu possa ajudar.",
                sources=[],
                confidence=0.0,
                mode="Base local",
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
                mode="Base local",
            )

        normalized = normalize(question)
        if self._blocked(normalized):
            return self._refusal()

        search_question = question
        if FOLLOW_UP.fullmatch(normalized):
            # O histórico da IA nunca define o assunto da recuperação.
            previous = next(
                (
                    message.get("content", "")
                    for message in reversed(history or [])
                    if message.get("role") == "user"
                    and not FOLLOW_UP.fullmatch(normalize(message.get("content", "")))
                ),
                "",
            )
            if (not previous or len(previous) > self.settings.max_question_chars
                    or self._blocked(normalize(previous))):
                return self._clarification()
            # O histórico é usado somente na recuperação local, nunca no prompt remoto.
            search_question = previous
        if AMBIGUOUS.fullmatch(normalize(search_question)):
            return self._clarification()

        results = self.knowledge.search(search_question, top_k=self.settings.top_k)

        relevant = [
            result
            for result in results
            if math.isfinite(result.score)
            and result.score > 0
            and result.score >= self.settings.min_similarity
        ]

        if not relevant:
            if FOLLOW_UP.fullmatch(normalized) or "diferenca entre" in normalized:
                return self._clarification()
            return self._refusal(results[0].score if results else 0.0)

        # Conceitos pedidos explicitamente precisam estar cobertos pela fonte principal.
        # Evita responder apenas a metade conhecida de comparações e pedidos compostos.
        requested = set(re.findall(r"\b(?:tuplas?|dicionarios?|conjuntos?)\b", normalize(search_question)))
        coverage = normalize(relevant[0].item.resposta + " " + relevant[0].item.exemplo)
        if any(term not in coverage for term in requested):
            return self._clarification()

        warning = None
        response_mode = "Base local"

        if self.llm:
            provider_question = question
            if FOLLOW_UP.fullmatch(normalized):
                # Referência confiável da base em vez de copiar a mensagem anterior.
                provider_question = f"Assunto: {relevant[0].item.titulo}. {question}"
            prompt = build_user_prompt(question=provider_question, results=relevant)
            try:
                response_text = self.llm.generate(prompt)
                response_mode = "Gemini + base local"
            except LLMUnavailableError:
                warning = (
                    "A IA generativa ficou indisponível. A resposta abaixo "
                    "foi montada diretamente da base local."
                )
                response_text = self._build_local_answer(relevant, question)
        else:
            response_text = self._build_local_answer(relevant, question)

        return AssistantResponse(
            text=response_text,
            sources=[
                {
                    "id": result.item.id,
                    "titulo": result.item.titulo,
                    "categoria": result.item.categoria,
                    "score": round(result.score, 4),
                }
                for result in relevant
            ],
            confidence=relevant[0].score,
            mode=response_mode,
            warning=warning or self.llm_initialization_error,
        )

    @staticmethod
    def _blocked(question: str) -> bool:
        if OVERRIDE_INTENT.search(question):
            return True
        operation = PROGRAMMING_OPERATION.search(question)
        if EXTERNAL_REQUEST.search(question):
            return True
        return bool(EXTERNAL_TOPIC.search(question) and not operation)

    @staticmethod
    def _clarification() -> AssistantResponse:
        return AssistantResponse(
            text="Qual assunto, biblioteca ou erro você quer explorar? "
            "Diga, por exemplo, se está falando de Pandas, Git ou ambientes virtuais.",
            sources=[],
            confidence=0.0,
            mode="Base local",
            action="clarify",
        )

    @staticmethod
    def _refusal(confidence: float = 0.0) -> AssistantResponse:
        if not math.isfinite(confidence) or not 0 <= confidence <= 1:
            confidence = 0.0
        return AssistantResponse(
            text="Não encontrei informação suficiente na minha base de conhecimento "
            "para responder com segurança. Posso ajudar com Python, Pandas, "
            "automação, ambientes virtuais, Git e fundamentos de IA.",
            sources=[],
            confidence=confidence,
            mode="Base local",
            action="refuse",
        )

    @staticmethod
    def _build_local_answer(results: list[SearchResult], question: str = "") -> str:
        principal = results[0].item

        partes = [principal.resposta]

        example = principal.exemplo
        language = "python"
        if principal.exemplos_por_plataforma:
            platforms = re.findall(r"\b(linux|macos|windows)\b", normalize(question))
            platform = platforms[-1] if platforms else None
            examples = principal.exemplos_por_plataforma
            if platform in examples:
                example = examples[platform]
            else:
                example = "\n\n".join(f"# {name}\n{code}" for name, code in examples.items())
            language = "bash" if platform in {"linux", "macos"} else "powershell"
            if platform is None:
                language = "text"
        if example:
            partes.append(f"**Exemplo:**\n```{language}\n{example}\n```")

        if principal.proximo_passo:
            partes.append(f"**Próximo passo:** {principal.proximo_passo}")

        return "\n\n".join(partes)
