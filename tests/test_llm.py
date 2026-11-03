from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from google.genai.interactions import Interaction

from nexopy.assistant import NexoPyAssistant
from nexopy.llm import GeminiProvider, LLMUnavailableError


def provider_with_response(response):
    with patch("google.genai.Client"):
        provider = GeminiProvider(api_key="test-key", model="test-model")
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
    assert arguments["store"] is False
    assert arguments["generation_config"]["max_output_tokens"] == 1024


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


def test_rate_and_daily_limits_expire_without_reset_on_failure(monkeypatch):
    now = [0.0]
    monkeypatch.setattr("nexopy.llm.monotonic", lambda: now[0])
    provider = provider_with_response(sdk_response([{"type": "text", "text": "ok"}]))
    provider.requests_per_minute = 1
    provider.requests_per_day = 2
    assert provider.generate("question") == "ok"
    with pytest.raises(LLMUnavailableError, match="Limite"):
        provider.generate("question")
    now[0] = 60
    provider._client.interactions.create.side_effect = RuntimeError("failure")
    with pytest.raises(LLMUnavailableError):
        provider.generate("question")
    now[0] = 120
    with pytest.raises(LLMUnavailableError, match="Limite"):
        provider.generate("question")
    assert provider._client.interactions.create.call_count == 2
    now[0] = 86400
    provider._client.interactions.create.side_effect = None
    assert provider.generate("question") == "ok"


def test_concurrent_calls_cannot_exceed_shared_quota():
    from concurrent.futures import ThreadPoolExecutor

    provider = provider_with_response(sdk_response([{"type": "text", "text": "ok"}]))
    provider.requests_per_minute = 3
    def attempt(_):
        try:
            provider.generate("question")
            return True
        except LLMUnavailableError:
            return False
    with ThreadPoolExecutor(max_workers=10) as pool:
        assert sum(pool.map(attempt, range(20))) == 3
    assert provider._client.interactions.create.call_count == 3


def test_oversized_context_never_calls_provider_or_consumes_quota():
    provider = provider_with_response(None)
    provider.max_prompt_chars = 10
    with pytest.raises(LLMUnavailableError, match="contexto"):
        provider.generate("x" * 11)
    provider._client.interactions.create.assert_not_called()
    assert not provider._requests


def test_quota_exhaustion_returns_local_answer():
    assistant = NexoPyAssistant(enable_llm=False)
    local = assistant.answer("O que é um DataFrame?")
    provider = provider_with_response(sdk_response([{"type": "text", "text": "ok"}]))
    provider.requests_per_day = 1
    provider.generate("first request")
    assistant.llm = provider
    result = assistant.answer("O que é um DataFrame?")
    assert result.text == local.text
    assert result.mode == "Base local"
    assert result.warning
    assert provider._client.interactions.create.call_count == 1
