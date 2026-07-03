from pathlib import Path
import sqlite3
from typing import Mapping


CASE_COLUMNS = [
    "transcript_text",
    "issue_text",
    "response_text",
    "recommended_category",
    "final_category",
    "responsible_owner",
    "review_status",
    "reviewer",
    "internal_note",
]


def init_case_store(db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reviewed_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                transcript_text TEXT NOT NULL DEFAULT '',
                issue_text TEXT NOT NULL DEFAULT '',
                response_text TEXT NOT NULL DEFAULT '',
                recommended_category TEXT NOT NULL DEFAULT '',
                final_category TEXT NOT NULL DEFAULT '',
                responsible_owner TEXT NOT NULL DEFAULT '',
                review_status TEXT NOT NULL DEFAULT 'draft',
                reviewer TEXT NOT NULL DEFAULT '',
                internal_note TEXT NOT NULL DEFAULT ''
            )
            """
        )


def save_reviewed_case(db_path: str | Path, values: Mapping[str, object]) -> int:
    init_case_store(db_path)
    payload = {column: str(values.get(column, "") or "") for column in CASE_COLUMNS}
    placeholders = ", ".join("?" for _ in CASE_COLUMNS)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.execute(
            f"INSERT INTO reviewed_cases ({', '.join(CASE_COLUMNS)}) VALUES ({placeholders})",
            [payload[column] for column in CASE_COLUMNS],
        )
        return int(cursor.lastrowid)


def list_reviewed_cases(db_path: str | Path) -> list[dict[str, object]]:
    init_case_store(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("SELECT * FROM reviewed_cases ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]
