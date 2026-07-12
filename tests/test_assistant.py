from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nexopy.assistant import NexoPyAssistant
from nexopy.config import Settings


def build_assistant() -> NexoPyAssistant:
    return NexoPyAssistant(settings=Settings(), enable_llm=False)


def test_retrieves_module_not_found() -> None:
    response = build_assistant().answer(
        "Como corrigir ModuleNotFoundError no pandas?"
    )
    assert response.sources
    assert response.sources[0]["id"] == "erro-modulenotfound"


def test_retrieves_dataframe() -> None:
    response = build_assistant().answer("O que é um DataFrame?")
    assert response.sources
    assert response.sources[0]["id"] == "pandas-dataframe"


def test_refuses_out_of_scope_question() -> None:
    response = build_assistant().answer(
        "Qual é a previsão do tempo para amanhã?"
    )
    assert response.sources == []
    assert "não encontrei" in response.text.lower()


def test_greeting() -> None:
    response = build_assistant().answer("Olá")
    assert "NexoPy" in response.text
    assert response.confidence == 1.0
