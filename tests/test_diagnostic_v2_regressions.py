from pathlib import Path
from unittest.mock import Mock

import pytest

from nexopy.assistant import NexoPyAssistant
from nexopy.evaluation import evaluate_cases


@pytest.mark.parametrize(
    "question",
    [
        "Como acessar a primeira posição de uma lista?",
        "Como obter o primeiro elemento da lista?",
        "Como consultar o índice de uma lista?",
    ],
)
def test_normal_index_access_uses_list_explanation(question):
    response = NexoPyAssistant(enable_llm=False).answer(question)
    assert response.sources[0]["id"] == "python-listas"
    assert "índice" in response.text


@pytest.mark.parametrize(
    "question",
    [
        "IndexError ao acessar uma posição inexistente da lista",
        "List index out of range",
        "Meu programa tenta acessar uma posição inexistente na lista.",
    ],
)
def test_index_errors_keep_error_guidance(question):
    response = NexoPyAssistant(enable_llm=False).answer(question)
    assert response.sources[0]["id"] == "erro-indexerror"


@pytest.mark.parametrize(
    "question",
    [
        "Qual o total de calorias por refeição?",
        "Quantas calorias devo consumir?",
        "Recomende uma dieta usando Python.",
        "Como ler um CSV e qual o total de calorias por refeição?",
    ],
)
def test_nutrition_requests_do_not_call_gemini(question):
    assistant = NexoPyAssistant(enable_llm=False)
    assistant.llm = Mock()
    response = assistant.answer(question)
    assert response.action == "refuse"
    assert not response.sources
    assistant.llm.generate.assert_not_called()


@pytest.mark.parametrize(
    "question,source",
    [
        ("Como ler um CSV de calorias com pandas?", "pandas-readcsv"),
        ("Como carregar um CSV de nutrição usando pandas?", "pandas-readcsv"),
        ("Como somar a coluna calorias por categoria na tabela pandas?", "pandas-groupby"),
        (
            "Qual função usar para somar a coluna calorias por categoria no pandas?",
            "pandas-groupby",
        ),
    ],
)
def test_programming_with_nutrition_data_is_allowed(question, source):
    response = NexoPyAssistant(enable_llm=False).answer(question)
    assert response.action == "answer"
    assert response.sources[0]["id"] == source


def test_all_known_v2_cases_are_now_regressions():
    cases = Path(__file__).resolve().parent / "casos_independentes_v2.json"
    _, details = evaluate_cases(NexoPyAssistant(enable_llm=False), cases)
    assert len(details) == 12
    assert details["resposta_segura"].all()
