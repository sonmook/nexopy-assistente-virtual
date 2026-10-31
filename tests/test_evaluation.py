import json
from dataclasses import replace

import pytest

from nexopy.assistant import NexoPyAssistant
from nexopy.evaluation import evaluate_cases


def test_reference_cases_pass():
    assistant = NexoPyAssistant(enable_llm=False)
    metrics, details = evaluate_cases(assistant, assistant.settings.evaluation_path)
    assert metrics.total == 20
    assert metrics.assertividade_percentual >= 85
    assert metrics.seguranca_percentual >= 95
    assert metrics.recusas_corretas == int(details["deve_recusar"].sum())


@pytest.mark.parametrize(
    "kind", ["invented_source", "wrong_text", "wrong_top_source", "extra_invalid_source"]
)
def test_invalid_answer_cannot_pass_safety(tmp_path, monkeypatch, kind):
    assistant = NexoPyAssistant(enable_llm=False)
    response = assistant.answer("O que é um DataFrame?")
    if kind == "invented_source":
        response = replace(response, sources=[{"id": "inexistente"}])
    elif kind == "wrong_text":
        response = replace(response, text="Uma resposta sem fundamento.")
    elif kind == "wrong_top_source":
        response = replace(response, sources=[{"id": "git-basico"}])
    else:
        response = replace(response, sources=response.sources + [{"id": "inexistente"}])
    monkeypatch.setattr(assistant, "answer", lambda question: response)
    path = tmp_path / "cases.json"
    path.write_text(
        json.dumps(
            [
                {
                    "pergunta": "O que é um DataFrame?",
                    "id_esperado": "pandas-dataframe",
                    "termos_esperados": ["linhas", "colunas"],
                }
            ]
        )
    )
    metrics, _ = evaluate_cases(assistant, path)
    assert metrics.seguranca_percentual == 0


def test_refusal_with_sources_is_not_safe(tmp_path, monkeypatch):
    assistant = NexoPyAssistant(enable_llm=False)
    response = replace(
        assistant.answer("O que é um DataFrame?"), text="Não encontrei, mas inventei isto."
    )
    monkeypatch.setattr(assistant, "answer", lambda question: response)
    path = tmp_path / "cases.json"
    path.write_text(json.dumps([{"pergunta": "tempo", "deve_recusar": True}]))
    metrics, _ = evaluate_cases(assistant, path)
    assert metrics.seguranca_percentual == 0
    assert metrics.recusas_corretas == 0


@pytest.mark.parametrize("cases", [[], [{"pergunta": "teste", "id_esperado": "pandas-dataframe"}]])
def test_invalid_evaluation_cases_fail_explicitly(tmp_path, cases):
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(cases))
    with pytest.raises(ValueError):
        evaluate_cases(NexoPyAssistant(enable_llm=False), path)
