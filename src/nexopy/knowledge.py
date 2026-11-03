from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .query import expand_query


STOP_WORDS_PT = {
    "a", "ao", "aos", "aquela", "aquele", "aquilo", "as", "ate", "com",
    "como", "da", "das", "de", "dela", "dele", "do", "dos", "e", "ela",
    "ele", "em", "entre", "era", "essa", "esse", "esta", "este", "eu",
    "foi", "ha", "isso", "isto", "ja", "mais", "mas", "me", "meu", "na",
    "nas", "nao", "no", "nos", "o", "os", "ou", "para", "pela", "pelo",
    "por", "qual", "que", "quem", "se", "sem", "ser", "seu", "sua", "tem",
    "ter", "um", "uma", "voce"
}


@dataclass(frozen=True)
class KnowledgeItem:
    id: str
    categoria: str
    titulo: str
    perguntas: list[str]
    palavras_chave: list[str]
    resposta: str
    exemplo: str
    proximo_passo: str
    exemplos_por_plataforma: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnowledgeItem":
        return cls(
            id=data["id"],
            categoria=data["categoria"],
            titulo=data["titulo"],
            perguntas=list(data.get("perguntas", [])),
            palavras_chave=list(data.get("palavras_chave", [])),
            resposta=data["resposta"],
            exemplo=data.get("exemplo", ""),
            proximo_passo=data.get("proximo_passo", ""),
            exemplos_por_plataforma=dict(data.get("exemplos_por_plataforma", {}))
        )

    def searchable_text(self) -> str:
        partes = [
            self.titulo,
            self.categoria,
            " ".join(self.perguntas),
            " ".join(self.palavras_chave),
            self.resposta,
            self.exemplo
        ]
        return " ".join(parte for parte in partes if parte)

    def as_context(self) -> str:
        return (
            f"Fonte: {self.titulo}\n"
            f"Categoria: {self.categoria}\n"
            f"Explicação: {self.resposta}\n"
            f"Exemplo: {self.exemplo}\n"
            f"Exemplos por plataforma: {json.dumps(self.exemplos_por_plataforma, ensure_ascii=False)}\n"
            f"Próximo passo: {self.proximo_passo}"
        )


@dataclass(frozen=True)
class SearchResult:
    item: KnowledgeItem
    score: float


class KnowledgeBase:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.items = self._load_items(path)
        if not self.items:
            raise ValueError("A base de conhecimento está vazia.")

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words=sorted(STOP_WORDS_PT)
        )
        self.matrix = self.vectorizer.fit_transform(
            item.searchable_text() for item in self.items
        )

    @staticmethod
    def _load_items(path: Path) -> list[KnowledgeItem]:
        if not path.exists():
            raise FileNotFoundError(f"Base de conhecimento não encontrada: {path}")

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("A base deve ser uma lista de objetos JSON.")

        return [KnowledgeItem.from_dict(item) for item in data]

    def search(self, question: str, top_k: int = 3) -> list[SearchResult]:
        question = question.strip()
        if not question:
            return []

        # O limiar e os scores continuam os do TF-IDF; apenas o vocabulário muda.
        query_vector = self.vectorizer.transform([expand_query(question)])
        scores = cosine_similarity(query_vector, self.matrix).flatten()
        indexes = scores.argsort()[::-1][:max(1, top_k)]

        return [
            SearchResult(item=self.items[index], score=float(scores[index]))
            for index in indexes
        ]

    def categories(self) -> list[str]:
        return sorted({item.categoria for item in self.items})
