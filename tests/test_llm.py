from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from google.genai._interactions.types.interaction import Interaction
from google.genai._interactions.types.text_content import TextContent

from nexopy.assistant import NexoPyAssistant
from nexopy.llm import GeminiProvider, LLMUnavailableError


def provider_with_response(response):
    provider = object.__new__(GeminiProvider)
    provider.model = "test-model"
    provider._client = SimpleNamespace(
        interactions=SimpleNamespace(create=Mock(return_value=response))
    )
    return provider


def test_reads_sdk_text_blocks_and_ignores_other_content():
    response = Interaction.model_construct(
        outputs=[
            TextContent(type="text", text=" Primeira parte. "),
            SimpleNamespace(type="image"),
            TextContent(type="text", text="Segunda parte."),
        ]
    )
    provider = provider_with_response(response)
    assert provider.generate("pergunta") == "Primeira parte.\n\nSegunda parte."
    assert provider._client.interactions.create.call_args.kwargs["input"] == "pergunta"


@pytest.mark.parametrize("outputs", [None, [], [TextContent(type="text", text="  ")]])
def test_empty_sdk_response_is_unavailable(outputs):
    provider = provider_with_response(Interaction.model_construct(outputs=outputs))
    with pytest.raises(LLMUnavailableError, match="vazia"):
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
