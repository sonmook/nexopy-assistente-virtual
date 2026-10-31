from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_local_chat_returns_answer_and_source(monkeypatch):
    monkeypatch.setenv("USE_GEMINI", "false")
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30
    ).run()
    assert not app.exception
    app.chat_input[0].set_value("O que é um DataFrame?").run()
    assert not app.exception
    response = app.session_state["messages"][-1]
    assert response["sources"][0]["id"] == "pandas-dataframe"
    assert "colunas" in response["content"]
    assert response["mode"] == "Base local"

    app.chat_input[0].set_value("Pode dar outro exemplo?").run()
    assert not app.exception
    assert app.session_state["messages"][-1]["sources"][0]["id"] == "pandas-dataframe"
    app.button[0].click().run()
    app.chat_input[0].set_value("Pode explicar melhor?").run()
    assert not app.exception
    clarification = app.session_state["messages"][-1]
    assert not clarification["sources"]
    assert "Qual assunto" in clarification["content"]
