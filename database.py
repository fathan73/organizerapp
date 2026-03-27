from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


DB_NAME = "event_committee.db"


class DatabaseManager:
    def __init__(self, db_path: str = DB_NAME) -> None:
        self.db_path = str(Path(db_path))
        self._initialize_database()

    def _connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _execute(
        self,
        query: str,
        params: tuple[Any, ...] = (),
        *,
        fetch_all: bool = False,
        fetch_one: bool = False,
        commit: bool = False,
    ) -> Any:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            if commit:
                conn.commit()
            if fetch_one:
                return cur.fetchone()
            if fetch_all:
                return cur.fetchall()
            return cur.lastrowid

    def _initialize_database(self) -> None:
        self._execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                theme TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL
            )
            """,
            commit=True,
        )
        self._execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                deadline TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('Belum', 'Proses', 'Selesai')),
                event_id INTEGER NOT NULL,
                FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
            )
            """,
            commit=True,
        )
        self._execute(
            """
            CREATE TABLE IF NOT EXISTS panitia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                division TEXT NOT NULL,
                event_id INTEGER NOT NULL,
                FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
            )
            """,
            commit=True,
        )
        self._execute(
            """
            CREATE TABLE IF NOT EXISTS keuangan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK(type IN ('Masuk', 'Keluar')),
                amount REAL NOT NULL CHECK(amount >= 0),
                description TEXT NOT NULL,
                event_id INTEGER NOT NULL,
                FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
            )
            """,
            commit=True,
        )

    def add_event(self, name: str, theme: str, start_date: str, end_date: str) -> int:
        return self._execute(
            "INSERT INTO events (name, theme, start_date, end_date) VALUES (?, ?, ?, ?)",
            (name, theme, start_date, end_date),
            commit=True,
        )

    def get_events(self) -> list[sqlite3.Row]:
        return self._execute(
            "SELECT id, name, theme, start_date, end_date FROM events ORDER BY start_date DESC, id DESC",
            fetch_all=True,
        )

    def delete_event(self, event_id: int) -> None:
        self._execute("DELETE FROM events WHERE id = ?", (event_id,), commit=True)

    def add_task(self, name: str, deadline: str, status: str, event_id: int) -> int:
        return self._execute(
            "INSERT INTO tasks (name, deadline, status, event_id) VALUES (?, ?, ?, ?)",
            (name, deadline, status, event_id),
            commit=True,
        )

    def get_tasks(self) -> list[sqlite3.Row]:
        return self._execute(
            """
            SELECT
                t.id,
                t.name,
                t.deadline,
                t.status,
                t.event_id,
                e.name AS event_name
            FROM tasks t
            JOIN events e ON e.id = t.event_id
            ORDER BY t.deadline ASC, t.id DESC
            """,
            fetch_all=True,
        )

    def delete_task(self, task_id: int) -> None:
        self._execute("DELETE FROM tasks WHERE id = ?", (task_id,), commit=True)

    def mark_task_done(self, task_id: int) -> None:
        self._execute("UPDATE tasks SET status = 'Selesai' WHERE id = ?", (task_id,), commit=True)

    def add_panitia(self, name: str, role: str, division: str, event_id: int) -> int:
        return self._execute(
            "INSERT INTO panitia (name, role, division, event_id) VALUES (?, ?, ?, ?)",
            (name, role, division, event_id),
            commit=True,
        )

    def get_panitia(self) -> list[sqlite3.Row]:
        return self._execute(
            """
            SELECT
                p.id,
                p.name,
                p.role,
                p.division,
                p.event_id,
                e.name AS event_name
            FROM panitia p
            JOIN events e ON e.id = p.event_id
            ORDER BY p.id DESC
            """,
            fetch_all=True,
        )

    def delete_panitia(self, member_id: int) -> None:
        self._execute("DELETE FROM panitia WHERE id = ?", (member_id,), commit=True)

    def add_keuangan(self, tx_type: str, amount: float, description: str, event_id: int) -> int:
        return self._execute(
            "INSERT INTO keuangan (type, amount, description, event_id) VALUES (?, ?, ?, ?)",
            (tx_type, amount, description, event_id),
            commit=True,
        )

    def get_keuangan(self) -> list[sqlite3.Row]:
        return self._execute(
            """
            SELECT
                k.id,
                k.type,
                k.amount,
                k.description,
                k.event_id,
                e.name AS event_name
            FROM keuangan k
            JOIN events e ON e.id = k.event_id
            ORDER BY k.id DESC
            """,
            fetch_all=True,
        )

    def delete_keuangan(self, transaction_id: int) -> None:
        self._execute("DELETE FROM keuangan WHERE id = ?", (transaction_id,), commit=True)

    def get_finance_balance(self) -> float:
        row = self._execute(
            """
            SELECT COALESCE(SUM(
                CASE
                    WHEN type = 'Masuk' THEN amount
                    WHEN type = 'Keluar' THEN -amount
                    ELSE 0
                END
            ), 0) AS balance
            FROM keuangan
            """,
            fetch_one=True,
        )
        return float(row["balance"] if row else 0)

    def get_dashboard_stats(self) -> dict[str, int | float]:
        total_events = int(self._execute("SELECT COUNT(*) AS total FROM events", fetch_one=True)["total"])
        total_tasks = int(self._execute("SELECT COUNT(*) AS total FROM tasks", fetch_one=True)["total"])
        completed_tasks = int(
            self._execute("SELECT COUNT(*) AS total FROM tasks WHERE status = 'Selesai'", fetch_one=True)["total"]
        )
        incomplete_tasks = total_tasks - completed_tasks
        progress_percentage = round((completed_tasks / total_tasks * 100) if total_tasks else 0.0, 2)

        return {
            "total_events": total_events,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "incomplete_tasks": incomplete_tasks,
            "progress_percentage": progress_percentage,
        }
