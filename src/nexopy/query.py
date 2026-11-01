"""Expansão conservadora do vocabulário de perguntas sobre programação."""

from __future__ import annotations

import re
import unicodedata


def expand_query(question: str) -> str:
    normalized = "".join(
        char
        for char in unicodedata.normalize("NFKD", question.casefold())
        if not unicodedata.combining(char)
    )
    additions = []
    if re.search(r"\b(registrar|listar|salvar|anotar|documentar)\b", normalized) and re.search(
        r"\b(bibliotecas|dependencias|pacotes)\b", normalized
    ):
        additions.append("requirements.txt dependencias")
    if re.search(r"\b(celulas|campos|valores|dados)\b", normalized) and re.search(
        r"\b(vazi[oa]s?|faltantes?|ausentes?|em branco)\b", normalized
    ):
        additions.append("valores nulos ausentes")
    if (
        re.search(r"\b(total|soma|somar|media|contagem|contar)\b", normalized)
        and re.search(r"\bpor\b", normalized)
        and re.search(r"\b(vendas|pandas|tabela|dataframe|planilha|dados|registros)\b", normalized)
    ):
        additions.append("agrupar groupby")
    if re.search(r"\b(registros|linhas)\b", normalized) and re.search(
        r"\b(repetid[oa]s?|duplicad[oa]s?)\b", normalized
    ):
        additions.append("linhas duplicadas")
    if (
        re.search(r"\blista\b", normalized)
        and re.search(r"\b(acessar|obter|pegar|consultar)\b", normalized)
        and re.search(r"\b(posicao|indice|elemento|primeir[oa]|ultim[oa])\b", normalized)
        and not re.search(
            r"\b(erro|indexerror|inexistente|invalido|fora|falha)\b|out of range|nao consigo",
            normalized,
        )
    ):
        additions.append("listas indice elementos")
    return " ".join([question, *additions])
