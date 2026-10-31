from __future__ import annotations

import sqlite3
import sys
from uuid import uuid4
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nexopy.assistant import NexoPyAssistant
from nexopy.config import Settings
from nexopy.feedback import MAX_COMMENT_LENGTH, save_feedback


st.set_page_config(
    page_title="NexoPy",
    page_icon="🐍",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 15% 10%, rgba(117, 77, 255, .10), transparent 28%),
            radial-gradient(circle at 85% 15%, rgba(39, 199, 158, .08), transparent 24%);
    }
    .nexopy-hero {
        padding: 1.4rem 1.5rem;
        border: 1px solid rgba(140, 140, 160, .25);
        border-radius: 18px;
        background: rgba(255, 255, 255, .035);
        margin-bottom: 1rem;
    }
    .nexopy-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
    }
    .nexopy-subtitle {
        opacity: .78;
        margin-top: .35rem;
    }
    .source-card {
        border-left: 3px solid #7757ff;
        padding: .45rem .75rem;
        margin: .35rem 0;
        background: rgba(119, 87, 255, .06);
        border-radius: 0 10px 10px 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)


@st.cache_resource
def load_assistant() -> NexoPyAssistant:
    return NexoPyAssistant(Settings())


def render_feedback(message: dict) -> None:
    if message.get("feedback_saved"):
        st.caption("Obrigado! Sua avaliação foi registrada.")
        return
    message_id = message.setdefault("id", str(uuid4()))
    with st.expander("Esta resposta ajudou?"):
        st.caption(
            "Ao avaliar, você envia seu voto, comentário opcional, fontes e modo da resposta. "
            "O texto da conversa não é salvo no feedback. Não inclua dados pessoais ou chaves."
        )
        with st.form(f"feedback-{message_id}"):
            comment = st.text_area("Comentário opcional", max_chars=MAX_COMMENT_LENGTH)
            left, right = st.columns(2)
            helpful = left.form_submit_button("👍 Ajudou")
            unhelpful = right.form_submit_button("👎 Não ajudou")
        if helpful or unhelpful:
            try:
                save_feedback(
                    assistant.settings.feedback_path,
                    message_id=message_id,
                    rating="helpful" if helpful else "unhelpful",
                    comment=comment,
                    source_ids=[source["id"] for source in message.get("sources", [])],
                    mode=message.get("mode", "Base local"),
                    action=message.get("action", "answer"),
                )
            except (OSError, sqlite3.Error, ValueError):
                st.error("Não foi possível registrar a avaliação. Tente novamente.")
            else:
                message["feedback_saved"] = True
                st.rerun()


assistant = load_assistant()

st.markdown(
    """
    <div class="nexopy-hero">
        <p class="nexopy-title">🐍 NexoPy</p>
        <p class="nexopy-subtitle">
            Assistente virtual para estudos em Python, Pandas, automação e IA.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.header("Sobre o NexoPy")
    st.caption(
        "O assistente pesquisa primeiro em uma base de conhecimento local "
        "e evita responder quando não encontra contexto suficiente."
    )
    st.metric("Conteúdos cadastrados", len(assistant.knowledge.items))
    st.write(f"**Modo:** {assistant.mode_name}")
    st.write(
        f"**Similaridade mínima:** "
        f"{assistant.settings.min_similarity:.2f}"
    )

    st.divider()
    st.subheader("Assuntos disponíveis")
    for category in assistant.knowledge.categories():
        st.write(f"• {category}")

    st.divider()
    if st.button("Limpar conversa", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption(
        "O NexoPy é um protótipo educacional. Sempre revise comandos "
        "antes de executá-los em projetos reais."
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.info(
        "Exemplos: “Como corrigir ModuleNotFoundError?”, "
        "“O que é um DataFrame?” ou “Qual a ordem para aprender Python?”"
    )

    suggestions = [
        "Como criar um ambiente virtual?",
        "O que é um DataFrame?",
        "Como evitar alucinações em IA?"
    ]
    columns = st.columns(3)
    selected_suggestion = None
    for column, suggestion in zip(columns, suggestions):
        with column:
            if st.button(
                suggestion,
                use_container_width=True,
                key=f"suggestion-{suggestion}"
            ):
                selected_suggestion = suggestion
else:
    selected_suggestion = None

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("mode"):
            st.caption(f"Resposta produzida por: {message['mode']}")

        if message.get("warning"):
            st.warning(message["warning"])

        if message.get("sources"):
            with st.expander("Fontes consultadas"):
                for source in message["sources"]:
                    st.markdown(
                        f"""
                        <div class="source-card">
                            <strong>{source["titulo"]}</strong><br>
                            <small>
                                {source["categoria"]} · similaridade:
                                {source["score"]:.2f}
                            </small>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        if message["role"] == "assistant":
            render_feedback(message)

typed_prompt = st.chat_input(
    "Digite sua dúvida sobre Python, Pandas, automação ou IA..."
)
prompt = selected_suggestion or typed_prompt

if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    history = [
        {"role": item["role"], "content": item["content"]}
        for item in st.session_state.messages[:-1]
    ]

    with st.chat_message("assistant"):
        with st.spinner("Consultando a base de conhecimento..."):
            response = assistant.answer(prompt, history=history)

        st.markdown(response.text)
        st.caption(f"Resposta produzida por: {response.mode}")

        if response.warning:
            st.warning(response.warning)

        if response.sources:
            with st.expander("Fontes consultadas"):
                for source in response.sources:
                    st.markdown(
                        f"""
                        <div class="source-card">
                            <strong>{source["titulo"]}</strong><br>
                            <small>
                                {source["categoria"]} · similaridade:
                                {source["score"]:.2f}
                            </small>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.caption("Nenhuma fonte adequada foi encontrada.")

    st.session_state.messages.append({
        "role": "assistant",
        "content": response.text,
        "sources": response.sources,
        "warning": response.warning,
        "mode": response.mode,
        "action": response.action,
        "id": str(uuid4())
    })

    st.rerun()
