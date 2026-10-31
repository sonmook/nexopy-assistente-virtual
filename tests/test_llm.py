from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from google.genai.interactions import Interaction

from nexopy.assistant import NexoPyAssistant
from nexopy.llm import GeminiProvider, LLMUnavailableError


def provider_with_response(response):
    provider = object.__new__(GeminiProvider)
    provider.model = "test-model"
    provider._client = SimpleNamespace(
        interactions=SimpleNamespace(create=Mock(return_value=response))
    )
    return provider


def sdk_response(contents, status="completed"):
    return Interaction.model_validate(
        {
            "status": status,
            "steps": [{"type": "model_output", "content": contents}],
        }
    )


def test_reads_sdk_final_text_from_steps():
    response = sdk_response(
        [
            {"type": "text", "text": " Primeira parte. "},
            {"type": "text", "text": "Segunda parte. "},
        ]
    )
    provider = provider_with_response(response)
    assert provider.generate("pergunta") == "Primeira parte. Segunda parte."
    arguments = provider._client.interactions.create.call_args.kwargs
    assert arguments["input"] == "pergunta"
    assert arguments["timeout"] == 45
    assert arguments["model"] == "test-model"
    assert arguments["system_instruction"]


@pytest.mark.parametrize("contents", [[], [{"type": "text", "text": "  "}]])
def test_empty_sdk_response_is_unavailable(contents):
    provider = provider_with_response(sdk_response(contents))
    with pytest.raises(LLMUnavailableError, match="vazia"):
        provider.generate("pergunta")


@pytest.mark.parametrize("status", ["failed", "incomplete", "requires_action"])
def test_partial_or_failed_response_is_not_shown_as_complete(status):
    provider = provider_with_response(
        sdk_response(
            [
                {"type": "text", "text": "Resposta parcial"},
            ],
            status=status,
        )
    )
    with pytest.raises(LLMUnavailableError, match="concluiu"):
        provider.generate("pergunta")


def test_provider_error_does_not_expose_remote_details():
    provider = provider_with_response(None)
    provider._client.interactions.create.side_effect = RuntimeError("sensitive-detail")
    with pytest.raises(LLMUnavailableError) as error:
        provider.generate("pergunta")
    assert "sensitive-detail" not in str(error.value)


def test_assistant_reports_effective_mode_on_success_and_fallback():
    assistant = NexoPyAssistant(enable_llm=False)
    local = assistant.answer("O que é um DataFrame?")
    assistant.llm = Mock()
    assistant.llm.generate.return_value = "Resposta gerada."
    generated = assistant.answer("O que é um DataFrame?")
    assert generated.mode == "Gemini + base local"
    assert generated.text == "Resposta gerada."
    assistant.llm.generate.side_effect = LLMUnavailableError("indisponível")
    fallback = assistant.answer("O que é um DataFrame?")
    assert fallback.mode == "Base local"
    assert fallback.text == local.text
    assert fallback.sources == local.sources
    assert fallback.warning
    assert assistant.answer("Olá").mode == "Base local"
    assert assistant.answer("Qual a previsão do tempo amanhã?").mode == "Base local"


def test_initialization_failure_keeps_local_answer(monkeypatch):
    import nexopy.assistant as module

    monkeypatch.setattr(
        module, "GeminiProvider", Mock(side_effect=LLMUnavailableError("indisponível"))
    )
    assistant = NexoPyAssistant(enable_llm=True)
    response = assistant.answer("O que é um DataFrame?")
    assert response.mode == "Base local"
    assert response.warning == "indisponível"
    assert response.sources[0]["id"] == "pandas-dataframe"
