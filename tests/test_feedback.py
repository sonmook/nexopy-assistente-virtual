import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from nexopy.feedback import save_feedback


def vote(database, message_id="response-1", **overrides):
    values = dict(
        message_id=message_id,
        rating="helpful",
        comment="Bom exemplo.",
        source_ids=["pandas-dataframe"],
        mode="Base local",
        action="answer",
    )
    values.update(overrides)
    return save_feedback(database, **values)


def test_feedback_persists_metadata_once_without_conversation(tmp_path):
    database = tmp_path / "nested" / "feedback.sqlite3"
    assert vote(database)
    assert not vote(database, rating="unhelpful")
    with sqlite3.connect(database) as connection:
        rows = connection.execute("SELECT * FROM feedback").fetchall()
        columns = {row[1] for row in connection.execute("PRAGMA table_info(feedback)")}
    assert len(rows) == 1
    assert rows[0][2:4] == ("helpful", "Bom exemplo.")
    assert json.loads(rows[0][4]) == ["pandas-dataframe"]
    assert columns == {
        "message_id",
        "created_at",
        "rating",
        "comment",
        "source_ids",
        "mode",
        "action",
    }


def test_concurrent_votes_are_not_lost(tmp_path):
    database = tmp_path / "feedback.sqlite3"
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert all(pool.map(lambda index: vote(database, str(index)), range(8)))
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT count(*) FROM feedback").fetchone()[0] == 8


@pytest.mark.parametrize(
    "values", [{"rating": "invalid"}, {"comment": "x" * 501}, {"message_id": ""}]
)
def test_invalid_feedback_does_not_create_database(tmp_path, values):
    database = tmp_path / "feedback.sqlite3"
    with pytest.raises(ValueError):
        vote(database, **values)
    assert not database.exists()
