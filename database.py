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
                theme TEXT DEFAULT '',
                start_date TEXT DEFAULT '',
                end_date TEXT DEFAULT '',
                target_dana INTEGER DEFAULT 0
            )
            """,
            commit=True,
        )
        self._migrate_events_location_to_theme()
        self._migrate_events_target_dana()
        self._execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                divisi TEXT DEFAULT '',
                deadline TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Belum' CHECK(status IN ('Belum', 'Selesai')),
                event_id INTEGER NOT NULL,
                FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
            )
            """,
            commit=True,
        )
        self._migrate_tasks_divisi()
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
        self._ensure_indexes()

    # Event CRUD
    def _migrate_events_location_to_theme(self) -> None:
        columns = self._execute("PRAGMA table_info(events)", fetch_all=True)
        column_names = {col["name"] for col in columns}
        if "theme" in column_names:
            return

        self._execute("ALTER TABLE events ADD COLUMN theme TEXT DEFAULT ''", commit=True)
        if "location" in column_names:
            self._execute(
                "UPDATE events SET theme = COALESCE(location, '') WHERE COALESCE(theme, '') = ''",
                commit=True,
            )

    def _migrate_tasks_divisi(self) -> None:
        columns = self._execute("PRAGMA table_info(tasks)", fetch_all=True)
        column_names = {col["name"] for col in columns}
        if "divisi" in column_names:
            return
        self._execute("ALTER TABLE tasks ADD COLUMN divisi TEXT DEFAULT ''", commit=True)

    def _migrate_events_target_dana(self) -> None:
        columns = self._execute("PRAGMA table_info(events)", fetch_all=True)
        column_names = {col["name"] for col in columns}
        if "target_dana" in column_names:
            return
        self._execute("ALTER TABLE events ADD COLUMN target_dana INTEGER DEFAULT 0", commit=True)

    def add_event(self, name: str, theme: str, start_date: str, end_date: str, target_dana: int = 0) -> int:
        return self._execute(
            "INSERT INTO events (name, theme, start_date, end_date, target_dana) VALUES (?, ?, ?, ?, ?)",
            (name, theme, start_date, end_date, target_dana),
            commit=True,
        )

    def _ensure_indexes(self) -> None:
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_tasks_event_search ON tasks(event_id, title, divisi, status)",
            "CREATE INDEX IF NOT EXISTS idx_panitia_event_search ON panitia(event_id, name, role, division, contact)",
            "CREATE INDEX IF NOT EXISTS idx_keuangan_event ON keuangan(event_id, tx_date)",
        ]
        for query in indexes:
            self._execute(query, commit=True)

    def get_events(self) -> list[sqlite3.Row]:
        return self._execute(
            "SELECT id, name, theme, start_date, end_date, target_dana FROM events ORDER BY id DESC",
            fetch_all=True,
        )

    def get_event_by_id(self, event_id: int) -> sqlite3.Row | None:
        return self._execute(
            "SELECT id, name, theme, start_date, end_date, target_dana FROM events WHERE id = ?",
            (event_id,),
            fetch_one=True,
        )

    def delete_event(self, event_id: int) -> None:
        self._execute("DELETE FROM events WHERE id = ?", (event_id,), commit=True)

    # Task CRUD (filtered by event)
    def add_task(self, title: str, divisi: str, deadline: str, notes: str, event_id: int) -> int:
        return self._execute(
            "INSERT INTO tasks (title, divisi, deadline, notes, event_id) VALUES (?, ?, ?, ?, ?)",
            (title, divisi, deadline, notes, event_id),
            commit=True,
        )

    def get_tasks_by_event(self, event_id: int, search: str = "") -> list[sqlite3.Row]:
        search = search.strip().lower()
        if search:
            pattern = f"%{search}%"
            return self._execute(
                """
                SELECT id, title, divisi, deadline, notes, status, event_id
                FROM tasks
                WHERE event_id = ?
                  AND (
                    LOWER(title) LIKE ?
                    OR LOWER(divisi) LIKE ?
                    OR LOWER(deadline) LIKE ?
                    OR LOWER(notes) LIKE ?
                    OR LOWER(status) LIKE ?
                  )
                ORDER BY id DESC
                """,
                (event_id, pattern, pattern, pattern, pattern, pattern),
                fetch_all=True,
            )
        return self._execute(
            """
            SELECT id, title, divisi, deadline, notes, status, event_id
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

    def get_panitia_by_event(self, event_id: int, search: str = "") -> list[sqlite3.Row]:
        search = search.strip().lower()
        if search:
            pattern = f"%{search}%"
            return self._execute(
                """
                SELECT id, name, role, division, contact, event_id
                FROM panitia
                WHERE event_id = ?
                  AND (
                    LOWER(name) LIKE ?
                    OR LOWER(role) LIKE ?
                    OR LOWER(division) LIKE ?
                    OR LOWER(contact) LIKE ?
                  )
                ORDER BY id DESC
                """,
                (event_id, pattern, pattern, pattern, pattern),
                fetch_all=True,
            )
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

    def get_financial_summary(self, event_id: int) -> dict[str, float]:
        row = self._execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN tx_type = 'Masuk' THEN amount ELSE 0 END), 0) AS income,
                COALESCE(SUM(CASE WHEN tx_type = 'Keluar' THEN amount ELSE 0 END), 0) AS expense
            FROM keuangan
            WHERE event_id = ?
            """,
            (event_id,),
            fetch_one=True,
        )
        income = float(row["income"] if row else 0.0)
        expense = float(row["expense"] if row else 0.0)
        return {
            "income": income,
            "expense": expense,
            "balance": income - expense,
        }

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

    def get_division_progress(self, event_id: int) -> list[sqlite3.Row]:
        return self._execute(
            """
            SELECT
                COALESCE(NULLIF(TRIM(divisi), ''), 'Tanpa Divisi') AS divisi,
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'Selesai' THEN 1 ELSE 0 END) AS selesai
            FROM tasks
            WHERE event_id = ?
            GROUP BY COALESCE(NULLIF(TRIM(divisi), ''), 'Tanpa Divisi')
            ORDER BY selesai * 1.0 / NULLIF(COUNT(*), 0) DESC, divisi ASC
            """,
            (event_id,),
            fetch_all=True,
        )

    def update_task(self, task_id: int, title: str, divisi: str, deadline: str, event_id: int) -> None:
        self._execute(
            "UPDATE tasks SET title = ?, divisi = ?, deadline = ? WHERE id = ? AND event_id = ?",
            (title, divisi, deadline, task_id, event_id),
            commit=True,
        )

    def update_event(
        self, event_id: int, name: str, theme: str, start_date: str, end_date: str, target_dana: int = 0
    ) -> None:
        self._execute(
            "UPDATE events SET name = ?, theme = ?, start_date = ?, end_date = ?, target_dana = ? WHERE id = ?",
            (name, theme, start_date, end_date, target_dana, event_id),
            commit=True,
        )

    def update_panitia(
        self, member_id: int, name: str, role: str, division: str, event_id: int
    ) -> None:
        self._execute(
            "UPDATE panitia SET name = ?, role = ?, division = ? WHERE id = ? AND event_id = ?",
            (name, role, division, member_id, event_id),
            commit=True,
        )

    def update_transaksi(
        self, transaction_id: int, tx_type: str, amount: float, description: str, event_id: int
    ) -> None:
        self._execute(
            "UPDATE keuangan SET tx_type = ?, amount = ?, description = ? WHERE id = ? AND event_id = ?",
            (tx_type, amount, description, transaction_id, event_id),
            commit=True,
        )

    def update_task_field(self, task_id: int, field: str, value: Any) -> None:
        allowed = {"title", "divisi", "deadline", "notes", "status"}
        if field not in allowed:
            raise ValueError("Invalid task field")
        self._execute(
            f"UPDATE tasks SET {field} = ? WHERE id = ?",
            (value, task_id),
            commit=True,
        )

    def update_event_field(self, event_id: int, field: str, value: Any) -> None:
        allowed = {"name", "theme", "start_date", "end_date", "target_dana"}
        if field not in allowed:
            raise ValueError("Invalid event field")
        self._execute(
            f"UPDATE events SET {field} = ? WHERE id = ?",
            (value, event_id),
            commit=True,
        )

    def update_panitia_field(self, member_id: int, field: str, value: Any) -> None:
        allowed = {"name", "role", "division", "contact"}
        if field not in allowed:
            raise ValueError("Invalid panitia field")
        self._execute(
            f"UPDATE panitia SET {field} = ? WHERE id = ?",
            (value, member_id),
            commit=True,
        )

    def update_keuangan_field(self, transaction_id: int, field: str, value: Any) -> None:
        allowed = {"tx_type", "amount", "description", "tx_date"}
        if field not in allowed:
            raise ValueError("Invalid keuangan field")
        self._execute(
            f"UPDATE keuangan SET {field} = ? WHERE id = ?",
            (value, transaction_id),
            commit=True,
        )
