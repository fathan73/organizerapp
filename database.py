"""Database layer for Event Committee Management System.

This module contains all SQLite access code and reusable CRUD helpers.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


DB_NAME = "event_committee.db"


class DatabaseManager:
    """Handle all database operations for the application."""

    def __init__(self, db_path: str = DB_NAME) -> None:
        self.db_path = str(Path(db_path))
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with row support."""
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _execute(
        self,
        query: str,
        params: tuple[Any, ...] = (),
        *,
        fetch: bool = False,
        fetch_one: bool = False,
        commit: bool = False,
    ) -> Any:
        """Generic query executor to reduce duplicate code."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            if commit:
                conn.commit()

            if fetch_one:
                return cursor.fetchone()
            if fetch:
                return cursor.fetchall()

            return cursor.lastrowid

    def _init_database(self) -> None:
        """Create required tables if they don't exist yet."""
        create_events = """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            theme TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL
        )
        """

        create_tasks = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            deadline TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Belum', 'Proses', 'Selesai')),
            event_id INTEGER NOT NULL,
            FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
        )
        """

        create_panitia = """
        CREATE TABLE IF NOT EXISTS panitia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            division TEXT NOT NULL,
            event_id INTEGER NOT NULL,
            FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
        )
        """

        self._execute(create_events, commit=True)
        self._execute(create_tasks, commit=True)
        self._execute(create_panitia, commit=True)

    # -----------------------------
    # Events CRUD
    # -----------------------------
    def add_event(self, name: str, theme: str, start_date: str, end_date: str) -> int:
        query = """
        INSERT INTO events (name, theme, start_date, end_date)
        VALUES (?, ?, ?, ?)
        """
        return self._execute(query, (name, theme, start_date, end_date), commit=True)

    def get_events(self) -> list[sqlite3.Row]:
        query = "SELECT id, name, theme, start_date, end_date FROM events ORDER BY id DESC"
        return self._execute(query, fetch=True)

    def delete_event(self, event_id: int) -> None:
        query = "DELETE FROM events WHERE id = ?"
        self._execute(query, (event_id,), commit=True)

    # -----------------------------
    # Tasks CRUD
    # -----------------------------
    def add_task(self, task_name: str, deadline: str, status: str, event_id: int) -> int:
        query = """
        INSERT INTO tasks (task_name, deadline, status, event_id)
        VALUES (?, ?, ?, ?)
        """
        return self._execute(query, (task_name, deadline, status, event_id), commit=True)

    def get_tasks(self) -> list[sqlite3.Row]:
        query = """
        SELECT
            tasks.id,
            tasks.task_name,
            tasks.deadline,
            tasks.status,
            tasks.event_id,
            events.name AS event_name
        FROM tasks
        INNER JOIN events ON tasks.event_id = events.id
        ORDER BY tasks.id DESC
        """
        return self._execute(query, fetch=True)

    def delete_task(self, task_id: int) -> None:
        query = "DELETE FROM tasks WHERE id = ?"
        self._execute(query, (task_id,), commit=True)

    def mark_task_completed(self, task_id: int) -> None:
        query = "UPDATE tasks SET status = 'Selesai' WHERE id = ?"
        self._execute(query, (task_id,), commit=True)

    # -----------------------------
    # Panitia CRUD
    # -----------------------------
    def add_panitia(self, name: str, role: str, division: str, event_id: int) -> int:
        query = """
        INSERT INTO panitia (name, role, division, event_id)
        VALUES (?, ?, ?, ?)
        """
        return self._execute(query, (name, role, division, event_id), commit=True)

    def get_panitia(self) -> list[sqlite3.Row]:
        query = """
        SELECT
            panitia.id,
            panitia.name,
            panitia.role,
            panitia.division,
            panitia.event_id,
            events.name AS event_name
        FROM panitia
        INNER JOIN events ON panitia.event_id = events.id
        ORDER BY panitia.id DESC
        """
        return self._execute(query, fetch=True)

    def delete_panitia(self, member_id: int) -> None:
        query = "DELETE FROM panitia WHERE id = ?"
        self._execute(query, (member_id,), commit=True)

    # -----------------------------
    # Dashboard helpers
    # -----------------------------
    def get_dashboard_stats(self) -> dict[str, int | float]:
        total_events = self._execute("SELECT COUNT(*) AS total FROM events", fetch_one=True)["total"]
        total_tasks = self._execute("SELECT COUNT(*) AS total FROM tasks", fetch_one=True)["total"]
        completed_tasks = self._execute(
            "SELECT COUNT(*) AS total FROM tasks WHERE status = 'Selesai'",
            fetch_one=True,
        )["total"]
        incomplete_tasks = total_tasks - completed_tasks

        progress = 0.0
        if total_tasks > 0:
            progress = (completed_tasks / total_tasks) * 100

        return {
            "total_events": int(total_events),
            "total_tasks": int(total_tasks),
            "completed_tasks": int(completed_tasks),
            "incomplete_tasks": int(incomplete_tasks),
            "progress_percentage": round(progress, 2),
        }
