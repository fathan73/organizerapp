"""Main UI for Event Committee Management System."""

from __future__ import annotations

import sys

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database import DatabaseManager


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.db = DatabaseManager()

        self.setWindowTitle("Event Committee Management System")
        self.resize(1200, 700)

        self._setup_ui()
        self._connect_signals()
        self.refresh_all()

    # -----------------------------
    # UI Setup
    # -----------------------------
    def _setup_ui(self) -> None:
        root = QWidget()
        root_layout = QHBoxLayout(root)

        self.sidebar = self._build_sidebar()
        self.pages = QStackedWidget()

        self.dashboard_page = self._build_dashboard_page()
        self.kegiatan_page = self._build_kegiatan_page()
        self.panitia_page = self._build_panitia_page()
        self.task_page = self._build_task_page()
        self.keuangan_page = self._build_placeholder_page("Keuangan - Coming Soon")
        self.rapat_page = self._build_placeholder_page("Rapat - Coming Soon")

        self.pages.addWidget(self.dashboard_page)
        self.pages.addWidget(self.kegiatan_page)
        self.pages.addWidget(self.panitia_page)
        self.pages.addWidget(self.task_page)
        self.pages.addWidget(self.keuangan_page)
        self.pages.addWidget(self.rapat_page)

        root_layout.addWidget(self.sidebar, 1)
        root_layout.addWidget(self.pages, 4)

        self.setCentralWidget(root)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(sidebar)

        title = QLabel("Menu")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")

        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_kegiatan = QPushButton("Kegiatan")
        self.btn_panitia = QPushButton("Panitia")
        self.btn_task = QPushButton("Task")
        self.btn_keuangan = QPushButton("Keuangan")
        self.btn_rapat = QPushButton("Rapat")

        for button in [
            self.btn_dashboard,
            self.btn_kegiatan,
            self.btn_panitia,
            self.btn_task,
            self.btn_keuangan,
            self.btn_rapat,
        ]:
            button.setMinimumHeight(40)
            layout.addWidget(button)

        layout.insertWidget(0, title)
        layout.addStretch()
        return sidebar

    def _build_dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        heading = QLabel("Dashboard")
        heading.setStyleSheet("font-size: 24px; font-weight: bold;")

        self.lbl_total_events = QLabel("Total Events: 0")
        self.lbl_total_tasks = QLabel("Total Tasks: 0")
        self.lbl_completed_tasks = QLabel("Completed Tasks: 0")
        self.lbl_incomplete_tasks = QLabel("Incomplete Tasks: 0")
        self.lbl_progress = QLabel("Progress: 0%")

        for label in [
            self.lbl_total_events,
            self.lbl_total_tasks,
            self.lbl_completed_tasks,
            self.lbl_incomplete_tasks,
            self.lbl_progress,
        ]:
            label.setStyleSheet("font-size: 16px;")
            layout.addWidget(label)

        layout.insertWidget(0, heading)
        layout.addStretch()
        return page

    def _build_kegiatan_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        heading = QLabel("Manajemen Kegiatan")
        heading.setStyleSheet("font-size: 22px; font-weight: bold;")

        form = QFormLayout()
        self.event_name_input = QLineEdit()
        self.event_theme_input = QLineEdit()
        self.event_start_input = QDateEdit()
        self.event_end_input = QDateEdit()

        self.event_start_input.setCalendarPopup(True)
        self.event_end_input.setCalendarPopup(True)
        self.event_start_input.setDate(QDate.currentDate())
        self.event_end_input.setDate(QDate.currentDate())

        form.addRow("Nama Kegiatan", self.event_name_input)
        form.addRow("Tema", self.event_theme_input)
        form.addRow("Tanggal Mulai", self.event_start_input)
        form.addRow("Tanggal Selesai", self.event_end_input)

        button_layout = QHBoxLayout()
        self.btn_add_event = QPushButton("Tambah Kegiatan")
        self.btn_delete_event = QPushButton("Hapus Kegiatan Terpilih")
        button_layout.addWidget(self.btn_add_event)
        button_layout.addWidget(self.btn_delete_event)

        self.event_table = QTableWidget()
        self.event_table.setColumnCount(5)
        self.event_table.setHorizontalHeaderLabels(["ID", "Nama", "Tema", "Mulai", "Selesai"])
        self.event_table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(heading)
        layout.addLayout(form)
        layout.addLayout(button_layout)
        layout.addWidget(self.event_table)
        return page

    def _build_panitia_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        heading = QLabel("Manajemen Panitia")
        heading.setStyleSheet("font-size: 22px; font-weight: bold;")

        form = QFormLayout()
        self.panitia_name_input = QLineEdit()
        self.panitia_role_input = QLineEdit()
        self.panitia_division_input = QLineEdit()
        self.panitia_event_combo = QComboBox()

        form.addRow("Nama", self.panitia_name_input)
        form.addRow("Role", self.panitia_role_input)
        form.addRow("Divisi", self.panitia_division_input)
        form.addRow("Kegiatan", self.panitia_event_combo)

        button_layout = QHBoxLayout()
        self.btn_add_panitia = QPushButton("Tambah Panitia")
        self.btn_delete_panitia = QPushButton("Hapus Panitia Terpilih")
        button_layout.addWidget(self.btn_add_panitia)
        button_layout.addWidget(self.btn_delete_panitia)

        self.panitia_table = QTableWidget()
        self.panitia_table.setColumnCount(5)
        self.panitia_table.setHorizontalHeaderLabels(["ID", "Nama", "Role", "Divisi", "Kegiatan"])
        self.panitia_table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(heading)
        layout.addLayout(form)
        layout.addLayout(button_layout)
        layout.addWidget(self.panitia_table)
        return page

    def _build_task_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        heading = QLabel("Manajemen Task")
        heading.setStyleSheet("font-size: 22px; font-weight: bold;")

        form = QFormLayout()
        self.task_name_input = QLineEdit()
        self.task_deadline_input = QDateEdit()
        self.task_deadline_input.setCalendarPopup(True)
        self.task_deadline_input.setDate(QDate.currentDate())
        self.task_status_combo = QComboBox()
        self.task_status_combo.addItems(["Belum", "Proses", "Selesai"])
        self.task_event_combo = QComboBox()

        form.addRow("Nama Task", self.task_name_input)
        form.addRow("Deadline", self.task_deadline_input)
        form.addRow("Status", self.task_status_combo)
        form.addRow("Kegiatan", self.task_event_combo)

        button_layout = QHBoxLayout()
        self.btn_add_task = QPushButton("Tambah Task")
        self.btn_delete_task = QPushButton("Hapus Task Terpilih")
        self.btn_complete_task = QPushButton("Tandai Selesai")

        button_layout.addWidget(self.btn_add_task)
        button_layout.addWidget(self.btn_delete_task)
        button_layout.addWidget(self.btn_complete_task)

        self.task_table = QTableWidget()
        self.task_table.setColumnCount(5)
        self.task_table.setHorizontalHeaderLabels(["ID", "Task", "Deadline", "Status", "Kegiatan"])
        self.task_table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(heading)
        layout.addLayout(form)
        layout.addLayout(button_layout)
        layout.addWidget(self.task_table)
        return page

    def _build_placeholder_page(self, text: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 22px; color: gray;")
        layout.addWidget(label)
        return page

    def _connect_signals(self) -> None:
        # Navigation buttons
        self.btn_dashboard.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        self.btn_kegiatan.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        self.btn_panitia.clicked.connect(lambda: self.pages.setCurrentIndex(2))
        self.btn_task.clicked.connect(lambda: self.pages.setCurrentIndex(3))
        self.btn_keuangan.clicked.connect(lambda: self.pages.setCurrentIndex(4))
        self.btn_rapat.clicked.connect(lambda: self.pages.setCurrentIndex(5))

        # CRUD buttons
        self.btn_add_event.clicked.connect(self.add_event)
        self.btn_delete_event.clicked.connect(self.delete_selected_event)

        self.btn_add_task.clicked.connect(self.add_task)
        self.btn_delete_task.clicked.connect(self.delete_selected_task)
        self.btn_complete_task.clicked.connect(self.complete_selected_task)

        self.btn_add_panitia.clicked.connect(self.add_panitia)
        self.btn_delete_panitia.clicked.connect(self.delete_selected_panitia)

    # -----------------------------
    # Reusable helpers
    # -----------------------------
    def show_warning(self, message: str) -> None:
        QMessageBox.warning(self, "Peringatan", message)

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Error", message)

    def _get_selected_id(self, table: QTableWidget) -> int | None:
        row = table.currentRow()
        if row < 0:
            return None
        item = table.item(row, 0)
        if item is None:
            return None
        return int(item.text())

    def _clear_table(self, table: QTableWidget) -> None:
        table.setRowCount(0)

    # -----------------------------
    # Refresh routines
    # -----------------------------
    def refresh_all(self) -> None:
        self.refresh_events_table()
        self.refresh_tasks_table()
        self.refresh_panitia_table()
        self.refresh_event_combos()
        self.refresh_dashboard()

    def refresh_events_table(self) -> None:
        events = self.db.get_events()
        self._clear_table(self.event_table)
        self.event_table.setRowCount(len(events))

        for row_index, row in enumerate(events):
            self.event_table.setItem(row_index, 0, QTableWidgetItem(str(row["id"])))
            self.event_table.setItem(row_index, 1, QTableWidgetItem(row["name"]))
            self.event_table.setItem(row_index, 2, QTableWidgetItem(row["theme"]))
            self.event_table.setItem(row_index, 3, QTableWidgetItem(row["start_date"]))
            self.event_table.setItem(row_index, 4, QTableWidgetItem(row["end_date"]))

    def refresh_tasks_table(self) -> None:
        tasks = self.db.get_tasks()
        self._clear_table(self.task_table)
        self.task_table.setRowCount(len(tasks))

        for row_index, row in enumerate(tasks):
            self.task_table.setItem(row_index, 0, QTableWidgetItem(str(row["id"])))
            self.task_table.setItem(row_index, 1, QTableWidgetItem(row["task_name"]))
            self.task_table.setItem(row_index, 2, QTableWidgetItem(row["deadline"]))
            self.task_table.setItem(row_index, 3, QTableWidgetItem(row["status"]))
            self.task_table.setItem(row_index, 4, QTableWidgetItem(row["event_name"]))

    def refresh_panitia_table(self) -> None:
        panitia_rows = self.db.get_panitia()
        self._clear_table(self.panitia_table)
        self.panitia_table.setRowCount(len(panitia_rows))

        for row_index, row in enumerate(panitia_rows):
            self.panitia_table.setItem(row_index, 0, QTableWidgetItem(str(row["id"])))
            self.panitia_table.setItem(row_index, 1, QTableWidgetItem(row["name"]))
            self.panitia_table.setItem(row_index, 2, QTableWidgetItem(row["role"]))
            self.panitia_table.setItem(row_index, 3, QTableWidgetItem(row["division"]))
            self.panitia_table.setItem(row_index, 4, QTableWidgetItem(row["event_name"]))

    def refresh_event_combos(self) -> None:
        events = self.db.get_events()

        self.task_event_combo.clear()
        self.panitia_event_combo.clear()

        for row in events:
            label = f"{row['name']} (ID: {row['id']})"
            self.task_event_combo.addItem(label, row["id"])
            self.panitia_event_combo.addItem(label, row["id"])

    def refresh_dashboard(self) -> None:
        stats = self.db.get_dashboard_stats()
        self.lbl_total_events.setText(f"Total Events: {stats['total_events']}")
        self.lbl_total_tasks.setText(f"Total Tasks: {stats['total_tasks']}")
        self.lbl_completed_tasks.setText(f"Completed Tasks: {stats['completed_tasks']}")
        self.lbl_incomplete_tasks.setText(f"Incomplete Tasks: {stats['incomplete_tasks']}")
        self.lbl_progress.setText(f"Progress: {stats['progress_percentage']}%")

    # -----------------------------
    # Event actions
    # -----------------------------
    def add_event(self) -> None:
        name = self.event_name_input.text().strip()
        theme = self.event_theme_input.text().strip()
        start_date = self.event_start_input.date().toString("yyyy-MM-dd")
        end_date = self.event_end_input.date().toString("yyyy-MM-dd")

        if not name or not theme:
            self.show_warning("Nama kegiatan dan tema wajib diisi.")
            return

        try:
            self.db.add_event(name, theme, start_date, end_date)
            self.event_name_input.clear()
            self.event_theme_input.clear()
            self.refresh_all()
        except Exception as error:  # Safety net for UI
            self.show_error(f"Gagal menambah kegiatan: {error}")

    def delete_selected_event(self) -> None:
        event_id = self._get_selected_id(self.event_table)
        if event_id is None:
            self.show_warning("Pilih kegiatan yang ingin dihapus.")
            return

        try:
            self.db.delete_event(event_id)
            self.refresh_all()
        except Exception as error:
            self.show_error(f"Gagal menghapus kegiatan: {error}")

    # -----------------------------
    # Task actions
    # -----------------------------
    def add_task(self) -> None:
        task_name = self.task_name_input.text().strip()
        deadline = self.task_deadline_input.date().toString("yyyy-MM-dd")
        status = self.task_status_combo.currentText()
        event_id = self.task_event_combo.currentData()

        if not task_name:
            self.show_warning("Nama task wajib diisi.")
            return

        if event_id is None:
            self.show_warning("Tambahkan kegiatan terlebih dahulu.")
            return

        try:
            self.db.add_task(task_name, deadline, status, int(event_id))
            self.task_name_input.clear()
            self.task_status_combo.setCurrentIndex(0)
            self.refresh_all()
        except Exception as error:
            self.show_error(f"Gagal menambah task: {error}")

    def delete_selected_task(self) -> None:
        task_id = self._get_selected_id(self.task_table)
        if task_id is None:
            self.show_warning("Pilih task yang ingin dihapus.")
            return

        try:
            self.db.delete_task(task_id)
            self.refresh_all()
        except Exception as error:
            self.show_error(f"Gagal menghapus task: {error}")

    def complete_selected_task(self) -> None:
        task_id = self._get_selected_id(self.task_table)
        if task_id is None:
            self.show_warning("Pilih task yang ingin ditandai selesai.")
            return

        try:
            self.db.mark_task_completed(task_id)
            self.refresh_all()
        except Exception as error:
            self.show_error(f"Gagal mengubah status task: {error}")

    # -----------------------------
    # Panitia actions
    # -----------------------------
    def add_panitia(self) -> None:
        name = self.panitia_name_input.text().strip()
        role = self.panitia_role_input.text().strip()
        division = self.panitia_division_input.text().strip()
        event_id = self.panitia_event_combo.currentData()

        if not name or not role or not division:
            self.show_warning("Nama, role, dan divisi wajib diisi.")
            return

        if event_id is None:
            self.show_warning("Tambahkan kegiatan terlebih dahulu.")
            return

        try:
            self.db.add_panitia(name, role, division, int(event_id))
            self.panitia_name_input.clear()
            self.panitia_role_input.clear()
            self.panitia_division_input.clear()
            self.refresh_all()
        except Exception as error:
            self.show_error(f"Gagal menambah panitia: {error}")

    def delete_selected_panitia(self) -> None:
        member_id = self._get_selected_id(self.panitia_table)
        if member_id is None:
            self.show_warning("Pilih panitia yang ingin dihapus.")
            return

        try:
            self.db.delete_panitia(member_id)
            self.refresh_all()
        except Exception as error:
            self.show_error(f"Gagal menghapus panitia: {error}")


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
