import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from forgeai.config.settings import settings


@dataclass
class ChatMetrics:
    thread_id: str
    timestamp: float
    request_latency: float
    first_token_latency: float | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0


class MetricsManager:
    def __init__(self) -> None:
        self.db_path: Path = settings.forgeai_dir / "db" / "metrics.db"
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT,
                    timestamp REAL,
                    request_latency REAL,
                    first_token_latency REAL,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    total_tokens INTEGER,
                    cached_tokens INTEGER
                )
                """,
            )

    def save_metrics(self, metrics: ChatMetrics) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO chat_metrics (
                    thread_id,
                    timestamp,
                    request_latency,
                    first_token_latency,
                    input_tokens,
                    output_tokens,
                    total_tokens,
                    cached_tokens
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metrics.thread_id,
                    metrics.timestamp,
                    metrics.request_latency,
                    metrics.first_token_latency,
                    metrics.input_tokens,
                    metrics.output_tokens,
                    metrics.total_tokens,
                    metrics.cached_tokens,
                ),
            )

    def get_session_summary(self, thread_id: str) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total_requests,
                    SUM(request_latency) as total_latency,
                    AVG(request_latency) as avg_latency,
                    AVG(first_token_latency) as avg_ttft,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(total_tokens) as total_tokens,
                    SUM(cached_tokens) as total_cached_tokens
                FROM chat_metrics
                WHERE thread_id = ?
                """,
                (thread_id,),
            )

            row = cursor.fetchone()

            return dict(row) if row else {}


__all__ = ["ChatMetrics", "MetricsManager"]
