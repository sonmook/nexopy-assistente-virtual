import json
from pathlib import Path

import pytest

from nexopy.assistant import NexoPyAssistant
from nexopy.query import expand_query


@pytest.mark.parametrize(
    "question,source",
    [
        ("Quero registrar as bibliotecas que meu projeto precisa.", "pip-requirements"),
        ("Como contar as células vazias antes de decidir se devo apagá-las?", "pandas-nulos"),
        ("Como obter o total de vendas por loja?", "pandas-groupby"),
        ("Como documentar os pacotes usados no projeto?", "pip-requirements"),
        ("Quero remover valores ausentes da tabela.", "pandas-nulos"),
        ("Como somar os dados por categoria?", "pandas-groupby"),
    ],
)
def test_paraphrases_retrieve_expected_source(question, source):
    response = NexoPyAssistant(enable_llm=False).answer(question)
    assert response.action == "answer"
    assert response.sources[0]["id"] == source
    assert response.confidence >= 0.16


@pytest.mark.parametrize(
    "question",
    [
        "Qual o total de calorias por refeição?",
        "Quero registrar uma reclamação.",
        "Quero salvar um arquivo de texto.",
        "Como preencher uma lista vazia?",
        "Qual o total de vendas?",  # Sem agrupamento explícito, não inferir groupby.
    ],
)
def test_unrelated_or_insufficient_intents_do_not_gain_search_terms(question):
    assert expand_query(question) == question


def test_known_diagnostic_cases_now_meet_all_expected_outcomes():
    from nexopy.evaluation import evaluate_cases

    path = Path(__file__).resolve().parent / "casos_independentes_v1.json"
    metrics, details = evaluate_cases(NexoPyAssistant(enable_llm=False), path)
    assert metrics.total == 18
    assert details["resposta_segura"].all()


def test_new_diagnostic_is_distinct_and_preserved():
    root = Path(__file__).resolve().parent
    v2 = json.loads((root / "casos_independentes_v2.json").read_text())
    used = [
        *json.loads((root / "casos_avaliacao.json").read_text()),
        *json.loads((root / "casos_independentes_v1.json").read_text()),
    ]
    assert len(v2) == 12
    # Perguntas já existentes só são permitidas com histórico diferente.
    signatures = {
        (case["pergunta"], json.dumps(case.get("historico", []), sort_keys=True)) for case in used
    }
    assert not any(
        (case["pergunta"], json.dumps(case.get("historico", []), sort_keys=True)) in signatures
        for case in v2
    )
