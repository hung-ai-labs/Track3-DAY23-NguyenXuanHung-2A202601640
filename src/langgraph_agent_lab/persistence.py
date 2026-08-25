"""Checkpointer adapter."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def build_checkpointer(kind: str = "memory", database_url: str | None = None) -> Any | None:
    """Return a LangGraph checkpointer.

    Memory and SQLite are supported. PostgreSQL is loaded lazily when its optional
    dependency is installed.

    For SQLite:
    - pip install langgraph-checkpoint-sqlite
    - Use SqliteSaver with sqlite3.connect() and WAL mode
    - See: https://langchain-ai.github.io/langgraph/how-tos/persistence/
    """
    if kind == "none":
        return None
    if kind == "memory":
        from langgraph.checkpoint.memory import MemorySaver

        return MemorySaver()
    if kind == "sqlite":
        from langgraph.checkpoint.sqlite import SqliteSaver

        raw_path = database_url or "outputs/checkpoints.sqlite"
        path = raw_path.removeprefix("sqlite:///")
        if path != ":memory:":
            Path(path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path, check_same_thread=False)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        return SqliteSaver(conn=connection)
    if kind == "postgres":
        if not database_url:
            raise ValueError("database_url is required for the PostgreSQL checkpointer")
        try:
            from langgraph.checkpoint.postgres import (  # type: ignore[import-not-found]
                PostgresSaver,
            )
        except ImportError as exc:
            raise RuntimeError("Install the 'postgres' project extra") from exc
        saver = PostgresSaver.from_conn_string(database_url)
        saver.setup()
        return saver
    raise ValueError(f"Unknown checkpointer kind: {kind}")
