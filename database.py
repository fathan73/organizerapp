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
            cursor = conn.cursor()
            cursor.execute(query, params)
            if commit:
                conn.commit()
            if fetch_one:
                return cursor.fetchone()
            if fetch_all:
                return cursor.fetchall()
            return cursor.lastrowid

    def _initialize_database(self) -> None:
        self._execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT DEFAULT '',
                start_date TEXT DEFAULT '',
                end_date TEXT DEFAULT ''
            )
            """,
            commit=True,
        )
        self._execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                deadline TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Belum' CHECK(status IN ('Belum', 'Selesai')),
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
                division TEXT DEFAULT '',
                contact TEXT DEFAULT '',
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
                tx_type TEXT NOT NULL CHECK(tx_type IN ('Masuk', 'Keluar')),
                amount REAL NOT NULL CHECK(amount >= 0),
                description TEXT DEFAULT '',
                tx_date TEXT DEFAULT '',
                event_id INTEGER NOT NULL,
                FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
            )
            """,
            commit=True,
        )

    # Event CRUD
    def add_event(self, name: str, location: str, start_date: str, end_date: str) -> int:
        return self._execute(
            "INSERT INTO events (name, location, start_date, end_date) VALUES (?, ?, ?, ?)",
            (name, location, start_date, end_date),
            commit=True,
        )

    def get_events(self) -> list[sqlite3.Row]:
        return self._execute(
            "SELECT id, name, location, start_date, end_date FROM events ORDER BY id DESC",
            fetch_all=True,
        )

    def delete_event(self, event_id: int) -> None:
        self._execute("DELETE FROM events WHERE id = ?", (event_id,), commit=True)

    # Task CRUD (filtered by event)
    def add_task(self, title: str, deadline: str, notes: str, event_id: int) -> int:
        return self._execute(
            "INSERT INTO tasks (title, deadline, notes, event_id) VALUES (?, ?, ?, ?)",
            (title, deadline, notes, event_id),
            commit=True,
        )

    def get_tasks_by_event(self, event_id: int) -> list[sqlite3.Row]:
        return self._execute(
            """
            SELECT id, title, deadline, notes, status, event_id
            FROM tasks
            WHERE event_id = ?
            ORDER BY id DESC
            """,
            (event_id,),
            fetch_all=True,
        )

    def delete_task(self, task_id: int, event_id: int) -> None:
        self._execute("DELETE FROM tasks WHERE id = ? AND event_id = ?", (task_id, event_id), commit=True)

    def mark_task_done(self, task_id: int, event_id: int) -> None:
        self._execute(
            "UPDATE tasks SET status = 'Selesai' WHERE id = ? AND event_id = ?",
            (task_id, event_id),
            commit=True,
        )

    # Panitia CRUD (filtered by event)
    def add_panitia(self, name: str, role: str, division: str, contact: str, event_id: int) -> int:
        return self._execute(
            "INSERT INTO panitia (name, role, division, contact, event_id) VALUES (?, ?, ?, ?, ?)",
            (name, role, division, contact, event_id),
            commit=True,
        )

    def get_panitia_by_event(self, event_id: int) -> list[sqlite3.Row]:
        return self._execute(
            """
            SELECT id, name, role, division, contact, event_id
            FROM panitia
            WHERE event_id = ?
            ORDER BY id DESC
            """,
            (event_id,),
            fetch_all=True,
        )

    def delete_panitia(self, member_id: int, event_id: int) -> None:
        self._execute(
            "DELETE FROM panitia WHERE id = ? AND event_id = ?",
            (member_id, event_id),
            commit=True,
        )

    # Keuangan CRUD (filtered by event)
    def add_keuangan(self, tx_type: str, amount: float, description: str, tx_date: str, event_id: int) -> int:
        return self._execute(
            "INSERT INTO keuangan (tx_type, amount, description, tx_date, event_id) VALUES (?, ?, ?, ?, ?)",
            (tx_type, amount, description, tx_date, event_id),
            commit=True,
        )

    def get_keuangan_by_event(self, event_id: int) -> list[sqlite3.Row]:
        return self._execute(
            """
            SELECT id, tx_type, amount, description, tx_date, event_id
            FROM keuangan
            WHERE event_id = ?
            ORDER BY id DESC
            """,
            (event_id,),
            fetch_all=True,
        )

    def delete_keuangan(self, transaction_id: int, event_id: int) -> None:
        self._execute(
            "DELETE FROM keuangan WHERE id = ? AND event_id = ?",
            (transaction_id, event_id),
            commit=True,
        )

    # Dashboard stats (per event)
    def get_dashboard_stats(self, event_id: int) -> dict[str, float | int]:
        total_row = self._execute(
            "SELECT COUNT(*) AS total FROM tasks WHERE event_id = ?",
            (event_id,),
            fetch_one=True,
        )
        done_row = self._execute(
            "SELECT COUNT(*) AS done FROM tasks WHERE event_id = ? AND status = 'Selesai'",
            (event_id,),
            fetch_one=True,
        )
        balance_row = self._execute(
            """
            SELECT COALESCE(
                SUM(CASE WHEN tx_type = 'Masuk' THEN amount ELSE -amount END),
                0
            ) AS balance
            FROM keuangan
            WHERE event_id = ?
            """,
            (event_id,),
            fetch_one=True,
        )

        total_tasks = int(total_row["total"] if total_row else 0)
        completed_tasks = int(done_row["done"] if done_row else 0)
        incomplete_tasks = total_tasks - completed_tasks
        progress = round((completed_tasks / total_tasks * 100) if total_tasks else 0.0, 2)
        balance = float(balance_row["balance"] if balance_row else 0.0)

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "incomplete_tasks": incomplete_tasks,
            "progress": progress,
            "balance": balance,
        }
