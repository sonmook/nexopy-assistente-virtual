"""Feedback local: não armazena perguntas, respostas ou identificadores pessoais."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

MAX_COMMENT_LENGTH = 500


def save_feedback(
    database: Path,
    *,
    message_id: str,
    rating: str,
    comment: str = "",
    source_ids: list[str],
    mode: str,
    action: str,
) -> bool:
    """Grava um voto por resposta. Reenvios não duplicam nem alteram votos."""
    if rating not in {"helpful", "unhelpful"}:
        raise ValueError("Avaliação inválida.")
    comment = comment.strip()
    if not message_id or len(comment) > MAX_COMMENT_LENGTH:
        raise ValueError("Identificador ou tamanho de comentário inválido.")
    database.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database, timeout=5) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                message_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                rating TEXT NOT NULL CHECK (rating IN ('helpful', 'unhelpful')),
                comment TEXT NOT NULL,
                source_ids TEXT NOT NULL,
                mode TEXT NOT NULL,
                action TEXT NOT NULL
            )
        """)
        cursor = connection.execute(
            "INSERT INTO feedback VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(message_id) DO NOTHING",
            (
                message_id,
                datetime.now(timezone.utc).isoformat(),
                rating,
                comment,
                json.dumps(source_ids, ensure_ascii=False),
                mode,
                action,
            ),
        )
        return cursor.rowcount == 1
