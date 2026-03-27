from __future__ import annotations

import sys

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QFrame,
    QFormLayout,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
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


class StatCard(QFrame):
    def __init__(self, title: str, icon: str) -> None:
        super().__init__()
        self.setObjectName("card")
        self.title_label = QLabel(f"{icon}  {title}")
        self.value_label = QLabel("0")
        self.value_label.setObjectName("cardValue")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 6)
        shadow.setColor(Qt.GlobalColor.lightGray)
        self.setGraphicsEffect(shadow)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.db = DatabaseManager()
        self.setWindowTitle("Event Committee Management System")
        self.resize(1320, 820)

        self._build_ui()
        self._apply_styles()
        self._connect_signals()
        self.refresh_all()

    def _build_ui(self) -> None:
        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.sidebar = self._build_sidebar()
        self.pages = QStackedWidget()

        self.page_dashboard = self._build_dashboard_page()
        self.page_kegiatan = self._build_event_page()
        self.page_panitia = self._build_panitia_page()
        self.page_task = self._build_task_page()
        self.page_finance = self._build_finance_page()

        self.pages.addWidget(self.page_dashboard)
        self.pages.addWidget(self.page_kegiatan)
        self.pages.addWidget(self.page_panitia)
        self.pages.addWidget(self.page_task)
        self.pages.addWidget(self.page_finance)

        outer.addWidget(self.sidebar)
        outer.addWidget(self.pages, stretch=1)

        self.setCentralWidget(root)

    def _build_sidebar(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("sidebar")
        panel.setFixedWidth(250)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 22, 18, 20)
        layout.setSpacing(10)

        brand = QLabel("🎯 Event Committee")
        brand.setObjectName("brand")
        layout.addWidget(brand)

        self.nav_dashboard = QPushButton("🏠 Dashboard")
        self.nav_kegiatan = QPushButton("📅 Kegiatan")
        self.nav_panitia = QPushButton("👥 Panitia")
        self.nav_task = QPushButton("✅ Task")
        self.nav_finance = QPushButton("💰 Keuangan")

        self.nav_buttons = [
            self.nav_dashboard,
            self.nav_kegiatan,
            self.nav_panitia,
            self.nav_task,
            self.nav_finance,
        ]

        for button in self.nav_buttons:
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(42)
            button.setCheckable(True)
            layout.addWidget(button)

        self.nav_dashboard.setChecked(True)
        layout.addStretch(1)
        return panel

    def _page_shell(self, title: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        layout.addWidget(title_label)
        return page, layout

    def _build_dashboard_page(self) -> QWidget:
        page, layout = self._page_shell("Dashboard")

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)

        self.card_total_events = StatCard("Total Event", "📌")
        self.card_total_tasks = StatCard("Total Task", "🧩")
        self.card_done = StatCard("Task Selesai", "✅")
        self.card_progress = StatCard("Progress", "📈")

        grid.addWidget(self.card_total_events, 0, 0)
        grid.addWidget(self.card_total_tasks, 0, 1)
        grid.addWidget(self.card_done, 1, 0)
        grid.addWidget(self.card_progress, 1, 1)

        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(20, 16, 20, 16)
        info_layout.setSpacing(8)
        self.lbl_incomplete = QLabel("Task belum selesai: 0")
        self.lbl_balance = QLabel("Saldo Keuangan: Rp 0")
        info_layout.addWidget(QLabel("Ringkasan Cepat"))
        info_layout.addWidget(self.lbl_incomplete)
        info_layout.addWidget(self.lbl_balance)

        shadow = QGraphicsDropShadowEffect(info_card)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 5)
        shadow.setColor(Qt.GlobalColor.lightGray)
        info_card.setGraphicsEffect(shadow)

        layout.addLayout(grid)
        layout.addWidget(info_card)
        layout.addStretch(1)
        return page

    def _build_event_page(self) -> QWidget:
        page, layout = self._page_shell("Manajemen Kegiatan")

        form_card = QFrame()
        form_card.setObjectName("card")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(18, 18, 18, 18)
        form_layout.setSpacing(12)

        form = QFormLayout()
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(16)

        self.event_name = QLineEdit()
        self.event_theme = QLineEdit()
        self.event_start = QDateEdit()
        self.event_end = QDateEdit()
        for date_input in (self.event_start, self.event_end):
            date_input.setCalendarPopup(True)
            date_input.setDate(QDate.currentDate())

        form.addRow("Nama Kegiatan", self.event_name)
        form.addRow("Tema", self.event_theme)
        form.addRow("Tanggal Mulai", self.event_start)
        form.addRow("Tanggal Selesai", self.event_end)

        controls = QHBoxLayout()
        self.btn_add_event = QPushButton("Tambah Kegiatan")
        self.btn_delete_event = QPushButton("Hapus Terpilih")
        controls.addWidget(self.btn_add_event)
        controls.addWidget(self.btn_delete_event)
        controls.addStretch(1)

        form_layout.addLayout(form)
        form_layout.addLayout(controls)

        self.table_events = self._build_table(["ID", "Nama", "Tema", "Mulai", "Selesai"])

        layout.addWidget(form_card)
        layout.addWidget(self.table_events, stretch=1)
        return page

    def _build_panitia_page(self) -> QWidget:
        page, layout = self._page_shell("Manajemen Panitia")

        form_card = QFrame()
        form_card.setObjectName("card")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(18, 18, 18, 18)

        form = QFormLayout()
        self.panitia_name = QLineEdit()
        self.panitia_role = QLineEdit()
        self.panitia_division = QLineEdit()
        self.panitia_event = QComboBox()
        form.addRow("Nama", self.panitia_name)
        form.addRow("Role", self.panitia_role)
        form.addRow("Divisi", self.panitia_division)
        form.addRow("Kegiatan", self.panitia_event)

        controls = QHBoxLayout()
        self.btn_add_panitia = QPushButton("Tambah Panitia")
        self.btn_delete_panitia = QPushButton("Hapus Terpilih")
        controls.addWidget(self.btn_add_panitia)
        controls.addWidget(self.btn_delete_panitia)
        controls.addStretch(1)

        form_layout.addLayout(form)
        form_layout.addLayout(controls)

        self.table_panitia = self._build_table(["ID", "Nama", "Role", "Divisi", "Kegiatan"])

        layout.addWidget(form_card)
        layout.addWidget(self.table_panitia, stretch=1)
        return page

    def _build_task_page(self) -> QWidget:
        page, layout = self._page_shell("Manajemen Task")

        form_card = QFrame()
        form_card.setObjectName("card")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(18, 18, 18, 18)

        form = QFormLayout()
        self.task_name = QLineEdit()
        self.task_deadline = QDateEdit()
        self.task_deadline.setCalendarPopup(True)
        self.task_deadline.setDate(QDate.currentDate())
        self.task_status = QComboBox()
        self.task_status.addItems(["Belum", "Proses", "Selesai"])
        self.task_event = QComboBox()

        form.addRow("Nama Task", self.task_name)
        form.addRow("Deadline", self.task_deadline)
        form.addRow("Status", self.task_status)
        form.addRow("Kegiatan", self.task_event)

        controls = QHBoxLayout()
        self.btn_add_task = QPushButton("Tambah Task")
        self.btn_delete_task = QPushButton("Hapus Terpilih")
        self.btn_done_task = QPushButton("Tandai Selesai")
        controls.addWidget(self.btn_add_task)
        controls.addWidget(self.btn_delete_task)
        controls.addWidget(self.btn_done_task)
        controls.addStretch(1)

        form_layout.addLayout(form)
        form_layout.addLayout(controls)

        self.table_tasks = self._build_table(["ID", "Nama", "Deadline", "Status", "Kegiatan"])

        layout.addWidget(form_card)
        layout.addWidget(self.table_tasks, stretch=1)
        return page

    def _build_finance_page(self) -> QWidget:
        page, layout = self._page_shell("Manajemen Keuangan")

        form_card = QFrame()
        form_card.setObjectName("card")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(18, 18, 18, 18)

        form = QFormLayout()
        self.finance_type = QComboBox()
        self.finance_type.addItems(["Masuk", "Keluar"])
        self.finance_amount = QLineEdit()
        self.finance_amount.setPlaceholderText("Contoh: 250000")
        self.finance_desc = QLineEdit()
        self.finance_event = QComboBox()

        form.addRow("Jenis", self.finance_type)
        form.addRow("Jumlah", self.finance_amount)
        form.addRow("Deskripsi", self.finance_desc)
        form.addRow("Kegiatan", self.finance_event)

        controls = QHBoxLayout()
        self.btn_add_finance = QPushButton("Tambah Transaksi")
        self.btn_delete_finance = QPushButton("Hapus Terpilih")
        controls.addWidget(self.btn_add_finance)
        controls.addWidget(self.btn_delete_finance)
        controls.addStretch(1)

        self.finance_balance = QLabel("Saldo: Rp 0")
        self.finance_balance.setObjectName("balanceLabel")

        form_layout.addLayout(form)
        form_layout.addLayout(controls)
        form_layout.addWidget(self.finance_balance)

        self.table_finance = self._build_table(["ID", "Tipe", "Jumlah", "Deskripsi", "Kegiatan"])

        layout.addWidget(form_card)
        layout.addWidget(self.table_finance, stretch=1)
        return page

    def _build_table(self, headers: list[str]) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        return table

    def _apply_styles(self) -> None:
        QApplication.instance().setFont(QFont("Segoe UI", 10))
        self.setStyleSheet(
            """
            QWidget {
                background: #f4f6f8;
                color: #111827;
            }
            #sidebar {
                background: #1f2937;
            }
            #brand {
                color: white;
                font-weight: 700;
                font-size: 18px;
                padding: 6px 8px 16px 8px;
            }
            #pageTitle {
                font-size: 24px;
                font-weight: 700;
                color: #111827;
                background: transparent;
            }
            #card {
                background: white;
                border-radius: 14px;
                border: 1px solid #e5e7eb;
            }
            #cardValue {
                font-size: 34px;
                font-weight: 700;
                color: #2563eb;
            }
            #balanceLabel {
                font-size: 16px;
                font-weight: 700;
                color: #1d4ed8;
                padding-top: 8px;
            }
            QPushButton {
                border: none;
                border-radius: 10px;
                background: #3b82f6;
                color: white;
                padding: 10px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #2563eb;
            }
            QPushButton:pressed {
                background: #1d4ed8;
            }
            #sidebar QPushButton {
                text-align: left;
                padding-left: 14px;
                background: transparent;
                border: 1px solid transparent;
                color: #e5e7eb;
            }
            #sidebar QPushButton:hover {
                background: rgba(59,130,246,0.2);
                border-color: rgba(59,130,246,0.4);
            }
            #sidebar QPushButton:checked {
                background: #3b82f6;
                color: white;
            }
            QLineEdit, QComboBox, QDateEdit {
                background: white;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                padding: 8px 10px;
                min-height: 18px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                border: 1px solid #3b82f6;
            }
            QTableWidget {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                gridline-color: #f3f4f6;
                selection-background-color: #dbeafe;
                selection-color: #111827;
            }
            QHeaderView::section {
                background: #f9fafb;
                border: none;
                border-bottom: 1px solid #e5e7eb;
                padding: 10px;
                font-weight: 700;
            }
            """
        )

    def _connect_signals(self) -> None:
        self.nav_dashboard.clicked.connect(lambda: self._switch_page(0, self.nav_dashboard))
        self.nav_kegiatan.clicked.connect(lambda: self._switch_page(1, self.nav_kegiatan))
        self.nav_panitia.clicked.connect(lambda: self._switch_page(2, self.nav_panitia))
        self.nav_task.clicked.connect(lambda: self._switch_page(3, self.nav_task))
        self.nav_finance.clicked.connect(lambda: self._switch_page(4, self.nav_finance))

        self.btn_add_event.clicked.connect(self.add_event)
        self.btn_delete_event.clicked.connect(self.delete_selected_event)

        self.btn_add_task.clicked.connect(self.add_task)
        self.btn_delete_task.clicked.connect(self.delete_selected_task)
        self.btn_done_task.clicked.connect(self.mark_task_done)

        self.btn_add_panitia.clicked.connect(self.add_panitia)
        self.btn_delete_panitia.clicked.connect(self.delete_selected_panitia)

        self.btn_add_finance.clicked.connect(self.add_finance)
        self.btn_delete_finance.clicked.connect(self.delete_selected_finance)

    def _switch_page(self, index: int, active_button: QPushButton) -> None:
        self.pages.setCurrentIndex(index)
        for button in self.nav_buttons:
            button.setChecked(button is active_button)

    def _selected_row_id(self, table: QTableWidget) -> int | None:
        row = table.currentRow()
        if row < 0:
            return None
        item = table.item(row, 0)
        return int(item.text()) if item else None

    def _warn(self, message: str) -> None:
        QMessageBox.warning(self, "Validasi", message)

    def _error(self, message: str) -> None:
        QMessageBox.critical(self, "Error", message)

    def refresh_all(self) -> None:
        self.refresh_event_combos()
        self.refresh_event_table()
        self.refresh_task_table()
        self.refresh_panitia_table()
        self.refresh_finance_table()
        self.refresh_dashboard()

    def refresh_event_combos(self) -> None:
        events = self.db.get_events()
        for combo in (self.task_event, self.panitia_event, self.finance_event):
            combo.clear()
            for event in events:
                combo.addItem(f"{event['name']} ({event['theme']})", event["id"])

    def refresh_event_table(self) -> None:
        rows = self.db.get_events()
        self.table_events.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.table_events.setItem(i, 0, QTableWidgetItem(str(row["id"])))
            self.table_events.setItem(i, 1, QTableWidgetItem(row["name"]))
            self.table_events.setItem(i, 2, QTableWidgetItem(row["theme"]))
            self.table_events.setItem(i, 3, QTableWidgetItem(row["start_date"]))
            self.table_events.setItem(i, 4, QTableWidgetItem(row["end_date"]))

    def refresh_task_table(self) -> None:
        rows = self.db.get_tasks()
        self.table_tasks.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.table_tasks.setItem(i, 0, QTableWidgetItem(str(row["id"])))
            self.table_tasks.setItem(i, 1, QTableWidgetItem(row["name"]))
            self.table_tasks.setItem(i, 2, QTableWidgetItem(row["deadline"]))
            self.table_tasks.setItem(i, 3, QTableWidgetItem(row["status"]))
            self.table_tasks.setItem(i, 4, QTableWidgetItem(row["event_name"]))

    def refresh_panitia_table(self) -> None:
        rows = self.db.get_panitia()
        self.table_panitia.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.table_panitia.setItem(i, 0, QTableWidgetItem(str(row["id"])))
            self.table_panitia.setItem(i, 1, QTableWidgetItem(row["name"]))
            self.table_panitia.setItem(i, 2, QTableWidgetItem(row["role"]))
            self.table_panitia.setItem(i, 3, QTableWidgetItem(row["division"]))
            self.table_panitia.setItem(i, 4, QTableWidgetItem(row["event_name"]))

    def refresh_finance_table(self) -> None:
        rows = self.db.get_keuangan()
        self.table_finance.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.table_finance.setItem(i, 0, QTableWidgetItem(str(row["id"])))
            self.table_finance.setItem(i, 1, QTableWidgetItem(row["type"]))
            self.table_finance.setItem(i, 2, QTableWidgetItem(f"Rp {row['amount']:,.0f}".replace(",", ".")))
            self.table_finance.setItem(i, 3, QTableWidgetItem(row["description"]))
            self.table_finance.setItem(i, 4, QTableWidgetItem(row["event_name"]))

        self.finance_balance.setText(
            f"Saldo: Rp {self.db.get_finance_balance():,.0f}".replace(",", ".")
        )

    def refresh_dashboard(self) -> None:
        stats = self.db.get_dashboard_stats()
        self.card_total_events.set_value(str(stats["total_events"]))
        self.card_total_tasks.set_value(str(stats["total_tasks"]))
        self.card_done.set_value(str(stats["completed_tasks"]))
        self.card_progress.set_value(f"{stats['progress_percentage']}%")
        self.lbl_incomplete.setText(f"Task belum selesai: {stats['incomplete_tasks']}")
        self.lbl_balance.setText(
            f"Saldo Keuangan: Rp {self.db.get_finance_balance():,.0f}".replace(",", ".")
        )

    def add_event(self) -> None:
        name = self.event_name.text().strip()
        theme = self.event_theme.text().strip()
        start_date = self.event_start.date().toString("yyyy-MM-dd")
        end_date = self.event_end.date().toString("yyyy-MM-dd")

        if not name or not theme:
            self._warn("Nama kegiatan dan tema wajib diisi.")
            return
        if self.event_end.date() < self.event_start.date():
            self._warn("Tanggal selesai tidak boleh lebih awal dari tanggal mulai.")
            return

        try:
            self.db.add_event(name, theme, start_date, end_date)
            self.event_name.clear()
            self.event_theme.clear()
            self.refresh_all()
        except Exception as err:
            self._error(f"Gagal menambah kegiatan: {err}")

    def delete_selected_event(self) -> None:
        event_id = self._selected_row_id(self.table_events)
        if event_id is None:
            self._warn("Pilih data kegiatan yang akan dihapus.")
            return
        try:
            self.db.delete_event(event_id)
            self.refresh_all()
        except Exception as err:
            self._error(f"Gagal menghapus kegiatan: {err}")

    def add_task(self) -> None:
        name = self.task_name.text().strip()
        deadline = self.task_deadline.date().toString("yyyy-MM-dd")
        status = self.task_status.currentText()
        event_id = self.task_event.currentData()

        if not name:
            self._warn("Nama task wajib diisi.")
            return
        if event_id is None:
            self._warn("Silakan buat kegiatan terlebih dahulu.")
            return

        try:
            self.db.add_task(name, deadline, status, int(event_id))
            self.task_name.clear()
            self.task_status.setCurrentIndex(0)
            self.refresh_all()
        except Exception as err:
            self._error(f"Gagal menambah task: {err}")

    def delete_selected_task(self) -> None:
        task_id = self._selected_row_id(self.table_tasks)
        if task_id is None:
            self._warn("Pilih data task yang akan dihapus.")
            return
        try:
            self.db.delete_task(task_id)
            self.refresh_all()
        except Exception as err:
            self._error(f"Gagal menghapus task: {err}")

    def mark_task_done(self) -> None:
        task_id = self._selected_row_id(self.table_tasks)
        if task_id is None:
            self._warn("Pilih task yang ingin ditandai selesai.")
            return
        try:
            self.db.mark_task_done(task_id)
            self.refresh_all()
        except Exception as err:
            self._error(f"Gagal menandai task selesai: {err}")

    def add_panitia(self) -> None:
        name = self.panitia_name.text().strip()
        role = self.panitia_role.text().strip()
        division = self.panitia_division.text().strip()
        event_id = self.panitia_event.currentData()

        if not name or not role or not division:
            self._warn("Nama, role, dan divisi wajib diisi.")
            return
        if event_id is None:
            self._warn("Silakan buat kegiatan terlebih dahulu.")
            return

        try:
            self.db.add_panitia(name, role, division, int(event_id))
            self.panitia_name.clear()
            self.panitia_role.clear()
            self.panitia_division.clear()
            self.refresh_all()
        except Exception as err:
            self._error(f"Gagal menambah panitia: {err}")

    def delete_selected_panitia(self) -> None:
        member_id = self._selected_row_id(self.table_panitia)
        if member_id is None:
            self._warn("Pilih anggota panitia yang akan dihapus.")
            return
        try:
            self.db.delete_panitia(member_id)
            self.refresh_all()
        except Exception as err:
            self._error(f"Gagal menghapus panitia: {err}")

    def add_finance(self) -> None:
        tx_type = self.finance_type.currentText()
        amount_text = self.finance_amount.text().strip().replace(".", "").replace(",", ".")
        description = self.finance_desc.text().strip()
        event_id = self.finance_event.currentData()

        if not amount_text or not description:
            self._warn("Jumlah dan deskripsi wajib diisi.")
            return
        if event_id is None:
            self._warn("Silakan buat kegiatan terlebih dahulu.")
            return

        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            self._warn("Jumlah harus berupa angka positif.")
            return

        try:
            self.db.add_keuangan(tx_type, amount, description, int(event_id))
            self.finance_amount.clear()
            self.finance_desc.clear()
            self.refresh_all()
        except Exception as err:
            self._error(f"Gagal menambah transaksi: {err}")

    def delete_selected_finance(self) -> None:
        tx_id = self._selected_row_id(self.table_finance)
        if tx_id is None:
            self._warn("Pilih transaksi yang akan dihapus.")
            return
        try:
            self.db.delete_keuangan(tx_id)
            self.refresh_all()
        except Exception as err:
            self._error(f"Gagal menghapus transaksi: {err}")


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
