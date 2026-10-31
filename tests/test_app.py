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
    next(button for button in app.button if button.label == "Limpar conversa").click().run()
    app.chat_input[0].set_value("Pode explicar melhor?").run()
    assert not app.exception
    clarification = app.session_state["messages"][-1]
    assert not clarification["sources"]
    assert "Qual assunto" in clarification["content"]


def test_feedback_is_saved_once_and_not_for_user_messages(monkeypatch, tmp_path):
    import sqlite3
    import streamlit as st

    database = tmp_path / "feedback.sqlite3"
    monkeypatch.setenv("USE_GEMINI", "false")
    monkeypatch.setenv("NEXOPY_FEEDBACK_PATH", str(database))
    st.cache_resource.clear()
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
    app.chat_input[0].set_value("O que é um DataFrame?").run()
    assert not app.exception
    assert len(app.text_area) == 1
    assert not database.exists()
    app.text_area[0].set_value("Exemplo útil.")
    next(button for button in app.button if button.label == "👍 Ajudou").click().run()
    assert not app.exception
    assert app.session_state["messages"][-1]["feedback_saved"]
    app.run()
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT rating, comment FROM feedback").fetchall() == [
            ("helpful", "Exemplo útil.")
        ]
    assert not app.text_area
    st.cache_resource.clear()


def test_feedback_write_failure_can_be_retried(monkeypatch, tmp_path):
    import streamlit as st

    blocked = tmp_path / "not-a-directory"
    blocked.write_text("blocked")
    monkeypatch.setenv("USE_GEMINI", "false")
    monkeypatch.setenv("NEXOPY_FEEDBACK_PATH", str(blocked / "feedback.sqlite3"))
    st.cache_resource.clear()
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
    app.chat_input[0].set_value("O que é um DataFrame?").run()
    next(button for button in app.button if button.label == "👎 Não ajudou").click().run()
    assert not app.exception
    assert app.error
    assert not app.session_state["messages"][-1].get("feedback_saved")
    assert app.text_area
    st.cache_resource.clear()
