from __future__ import annotations

from collections.abc import Sequence

from .knowledge import SearchResult


SYSTEM_PROMPT = """
Você é o NexoPy, um assistente educacional especializado em Python,
Pandas, automação de dados, Git e fundamentos de inteligência artificial.

Regras obrigatórias:
1. Responda em português do Brasil, de forma didática, clara e objetiva.
2. Use somente as informações presentes no contexto fornecido.
3. Não invente bibliotecas, comandos, resultados, fontes ou fatos.
4. Quando o contexto não for suficiente, diga claramente que não encontrou
   informação suficiente na base de conhecimento.
5. Explique código em etapas curtas e mantenha exemplos pequenos.
6. Não apresente a solução completa de um exercício imediatamente; ofereça
   primeiro orientação e dicas.
7. Não peça nem exponha senhas, tokens ou chaves de API.
8. Quando houver mais de uma fonte, combine apenas informações compatíveis.
9. Termine com um próximo passo útil quando isso fizer sentido.
""".strip()


def build_user_prompt(
    question: str,
    results: Sequence[SearchResult],
    recent_history: Sequence[dict[str, str]] | None = None
) -> str:
    context = "\n\n---\n\n".join(
        result.item.as_context() for result in results
    )

    history_text = ""
    if recent_history:
        linhas = []
        for message in recent_history[-4:]:
            role = "Pessoa usuária" if message.get("role") == "user" else "NexoPy"
            content = message.get("content", "")
            linhas.append(f"{role}: {content}")
        history_text = "\n".join(linhas)

    return f"""
    CONTEXTO RECUPERADO:
    {context}

    HISTÓRICO RECENTE:
    {history_text or "Sem histórico anterior relevante."}

    PERGUNTA:
    {question}

    Produza uma resposta fundamentada apenas no contexto recuperado.
    """.strip()
