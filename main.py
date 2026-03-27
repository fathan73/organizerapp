from __future__ import annotations

import sys

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QFrame,
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
        self.setObjectName("statCard")
        self.value_label = QLabel("0")
        self.value_label.setObjectName("statValue")
        self.title_label = QLabel(f"{icon} {title}")
        self.title_label.setObjectName("statTitle")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)
        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(Qt.GlobalColor.lightGray)
        self.setGraphicsEffect(shadow)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.db = DatabaseManager()
        self.current_event_id: int | None = None

        self.setWindowTitle("Event Committee Management System")
        self.resize(1380, 860)

        self._build_ui()
        self._apply_styles()
        self._connect_signals()
        self.refresh_events_and_context()

    def _build_ui(self) -> None:
        container = QWidget()
        root_layout = QHBoxLayout(container)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())

        self.main_panel = QWidget()
        main_layout = QVBoxLayout(self.main_panel)
        main_layout.setContentsMargins(20, 16, 20, 20)
        main_layout.setSpacing(14)

        main_layout.addWidget(self._build_header())

        self.stack = QStackedWidget()
        self.dashboard_page = self._build_dashboard_page()
        self.event_page = self._build_event_page()
        self.task_page = self._build_task_page()
        self.panitia_page = self._build_panitia_page()
        self.finance_page = self._build_finance_page()

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.event_page)
        self.stack.addWidget(self.task_page)
        self.stack.addWidget(self.panitia_page)
        self.stack.addWidget(self.finance_page)

        main_layout.addWidget(self.stack, 1)
        root_layout.addWidget(self.main_panel, 1)

        self.setCentralWidget(container)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 18, 16, 18)
        layout.setSpacing(10)

        brand = QLabel("🎯 Event Committee")
        brand.setObjectName("brand")
        layout.addWidget(brand)

        self.nav_dashboard = QPushButton("📊 Dashboard")
        self.nav_events = QPushButton("📅 Kegiatan")
        self.nav_tasks = QPushButton("✅ Tasks")
        self.nav_panitia = QPushButton("👥 Panitia")
        self.nav_finance = QPushButton("💰 Keuangan")

        self.nav_buttons = [
            self.nav_dashboard,
            self.nav_events,
            self.nav_tasks,
            self.nav_panitia,
            self.nav_finance,
        ]

        for btn in self.nav_buttons:
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(40)
            layout.addWidget(btn)

        self.nav_dashboard.setChecked(True)
        layout.addStretch()
        return sidebar

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        title = QLabel("Event Committee Management System")
        title.setObjectName("headerTitle")
        layout.addWidget(title)
        layout.addStretch()

        label = QLabel("Pilih Kegiatan")
        label.setObjectName("selectorLabel")
        self.event_selector = QComboBox()
        self.event_selector.setMinimumWidth(260)

        layout.addWidget(label)
        layout.addWidget(self.event_selector)
        return header

    def _build_page_container(self, title: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        page_title = QLabel(title)
        page_title.setObjectName("pageTitle")
        layout.addWidget(page_title)
        return page, layout

    def _build_dashboard_page(self) -> QWidget:
        page, layout = self._build_page_container("Dashboard (Per Kegiatan)")

        grid = QGridLayout()
        grid.setSpacing(14)

        self.card_total = StatCard("Total Task", "🧩")
        self.card_done = StatCard("Task Selesai", "✅")
        self.card_pending = StatCard("Task Belum Selesai", "🕒")
        self.card_progress = StatCard("Progress", "📈")

        grid.addWidget(self.card_total, 0, 0)
        grid.addWidget(self.card_done, 0, 1)
        grid.addWidget(self.card_pending, 1, 0)
        grid.addWidget(self.card_progress, 1, 1)

        finance_summary = QFrame()
        finance_summary.setObjectName("panelCard")
        fs_layout = QVBoxLayout(finance_summary)
        fs_layout.setContentsMargins(16, 16, 16, 16)
        fs_layout.setSpacing(6)
        fs_layout.addWidget(QLabel("💳 Saldo Keuangan (Event Aktif)"))
        self.lbl_balance = QLabel("Rp 0")
        self.lbl_balance.setObjectName("balance")
        fs_layout.addWidget(self.lbl_balance)

        shadow = QGraphicsDropShadowEffect(finance_summary)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(Qt.GlobalColor.lightGray)
        finance_summary.setGraphicsEffect(shadow)

        layout.addLayout(grid)
        layout.addWidget(finance_summary)
        layout.addStretch(1)
        return page

    def _build_event_page(self) -> QWidget:
        page, layout = self._build_page_container("Manajemen Kegiatan")

        form_card = QFrame()
        form_card.setObjectName("panelCard")
        form_layout = QFormLayout(form_card)
        form_layout.setContentsMargins(16, 16, 16, 16)
        form_layout.setSpacing(10)

        self.event_name_input = QLineEdit()
        self.event_name_input.setPlaceholderText("Contoh: Seminar Teknologi 2026")
        self.event_theme_input = QLineEdit()
        self.event_theme_input.setPlaceholderText("Tema kegiatan")
        self.event_start_input = QDateEdit()
        self.event_end_input = QDateEdit()
        for date_edit in (self.event_start_input, self.event_end_input):
            date_edit.setCalendarPopup(True)
            date_edit.setDate(QDate.currentDate())

        form_layout.addRow("Nama Kegiatan", self.event_name_input)
        form_layout.addRow("Tema", self.event_theme_input)
        form_layout.addRow("Tanggal Mulai", self.event_start_input)
        form_layout.addRow("Tanggal Selesai", self.event_end_input)

        buttons = QHBoxLayout()
        self.btn_event_add = QPushButton("Tambah Event")
        self.btn_event_delete = QPushButton("Hapus Event Terpilih")
        buttons.addWidget(self.btn_event_add)
        buttons.addWidget(self.btn_event_delete)
        buttons.addStretch()

        event_container = QVBoxLayout()
        event_container.setSpacing(10)
        event_container.addWidget(form_card)
        event_container.addLayout(buttons)

        self.table_events = self._create_table(["ID", "Nama", "Tema", "Mulai", "Selesai"])
        layout.addLayout(event_container)
        layout.addWidget(self.table_events, 1)
        return page

    def _build_task_page(self) -> QWidget:
        page, layout = self._build_page_container("Manajemen Tasks (Event Aktif)")

        form_card = QFrame()
        form_card.setObjectName("panelCard")
        form_layout = QFormLayout(form_card)
        form_layout.setContentsMargins(16, 16, 16, 16)
        form_layout.setSpacing(10)

        self.task_title_input = QLineEdit()
        self.task_title_input.setPlaceholderText("Judul task")
        self.task_deadline_input = QDateEdit()
        self.task_deadline_input.setCalendarPopup(True)
        self.task_deadline_input.setDate(QDate.currentDate())
        self.task_notes_input = QLineEdit()
        self.task_notes_input.setPlaceholderText("Catatan singkat")

        form_layout.addRow("Task", self.task_title_input)
        form_layout.addRow("Deadline", self.task_deadline_input)
        form_layout.addRow("Catatan", self.task_notes_input)

        controls = QHBoxLayout()
        self.btn_task_add = QPushButton("Tambah Task")
        self.btn_task_done = QPushButton("Tandai Selesai")
        self.btn_task_delete = QPushButton("Hapus Task")
        controls.addWidget(self.btn_task_add)
        controls.addWidget(self.btn_task_done)
        controls.addWidget(self.btn_task_delete)
        controls.addStretch()

        self.table_tasks = self._create_table(["ID", "Task", "Deadline", "Catatan", "Status"])

        layout.addWidget(form_card)
        layout.addLayout(controls)
        layout.addWidget(self.table_tasks, 1)
        return page

    def _build_panitia_page(self) -> QWidget:
        page, layout = self._build_page_container("Manajemen Panitia (Event Aktif)")

        form_card = QFrame()
        form_card.setObjectName("panelCard")
        form_layout = QFormLayout(form_card)
        form_layout.setContentsMargins(16, 16, 16, 16)
        form_layout.setSpacing(10)

        self.panitia_name_input = QLineEdit()
        self.panitia_name_input.setPlaceholderText("Nama anggota")
        self.panitia_role_input = QLineEdit()
        self.panitia_role_input.setPlaceholderText("Peran")
        self.panitia_division_input = QLineEdit()
        self.panitia_division_input.setPlaceholderText("Divisi")
        self.panitia_contact_input = QLineEdit()
        self.panitia_contact_input.setPlaceholderText("Kontak")

        form_layout.addRow("Nama", self.panitia_name_input)
        form_layout.addRow("Role", self.panitia_role_input)
        form_layout.addRow("Divisi", self.panitia_division_input)
        form_layout.addRow("Kontak", self.panitia_contact_input)

        controls = QHBoxLayout()
        self.btn_panitia_add = QPushButton("Tambah Anggota")
        self.btn_panitia_delete = QPushButton("Hapus Anggota")
        controls.addWidget(self.btn_panitia_add)
        controls.addWidget(self.btn_panitia_delete)
        controls.addStretch()

        self.table_panitia = self._create_table(["ID", "Nama", "Role", "Divisi", "Kontak"])

        layout.addWidget(form_card)
        layout.addLayout(controls)
        layout.addWidget(self.table_panitia, 1)
        return page

    def _build_finance_page(self) -> QWidget:
        page, layout = self._build_page_container("Manajemen Keuangan (Event Aktif)")

        form_card = QFrame()
        form_card.setObjectName("panelCard")
        form_layout = QFormLayout(form_card)
        form_layout.setContentsMargins(16, 16, 16, 16)
        form_layout.setSpacing(10)

        self.finance_type_input = QComboBox()
        self.finance_type_input.addItems(["Masuk", "Keluar"])
        self.finance_amount_input = QLineEdit()
        self.finance_amount_input.setPlaceholderText("Nominal transaksi")
        self.finance_desc_input = QLineEdit()
        self.finance_desc_input.setPlaceholderText("Deskripsi")
        self.finance_date_input = QDateEdit()
        self.finance_date_input.setCalendarPopup(True)
        self.finance_date_input.setDate(QDate.currentDate())

        form_layout.addRow("Tipe", self.finance_type_input)
        form_layout.addRow("Nominal", self.finance_amount_input)
        form_layout.addRow("Deskripsi", self.finance_desc_input)
        form_layout.addRow("Tanggal", self.finance_date_input)

        controls = QHBoxLayout()
        self.btn_finance_add = QPushButton("Tambah Transaksi")
        self.btn_finance_delete = QPushButton("Hapus Transaksi")
        controls.addWidget(self.btn_finance_add)
        controls.addWidget(self.btn_finance_delete)
        controls.addStretch()

        self.table_finance = self._create_table(["ID", "Tipe", "Nominal", "Deskripsi", "Tanggal"])
        layout.addWidget(form_card)
        layout.addLayout(controls)
        layout.addWidget(self.table_finance, 1)
        return page

    def _create_table(self, headers: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        return table

    def _connect_signals(self) -> None:
        self.nav_dashboard.clicked.connect(lambda: self.switch_page(0))
        self.nav_events.clicked.connect(lambda: self.switch_page(1))
        self.nav_tasks.clicked.connect(lambda: self.switch_page(2))
        self.nav_panitia.clicked.connect(lambda: self.switch_page(3))
        self.nav_finance.clicked.connect(lambda: self.switch_page(4))

        self.event_selector.currentIndexChanged.connect(self.on_event_changed)

        self.btn_event_add.clicked.connect(self.add_event)
        self.btn_event_delete.clicked.connect(self.delete_selected_event)

        self.btn_task_add.clicked.connect(self.add_task)
        self.btn_task_done.clicked.connect(self.mark_task_done)
        self.btn_task_delete.clicked.connect(self.delete_task)

        self.btn_panitia_add.clicked.connect(self.add_panitia)
        self.btn_panitia_delete.clicked.connect(self.delete_panitia)

        self.btn_finance_add.clicked.connect(self.add_finance)
        self.btn_finance_delete.clicked.connect(self.delete_finance)

    def _apply_styles(self) -> None:
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #f4f6f8; color: #111827; }
            #sidebar { background: #1f2937; }
            #brand { color: #f9fafb; font-weight: 700; font-size: 18px; margin-bottom: 8px; }
            #header { background: white; border-radius: 12px; }
            #headerTitle { font-size: 16px; font-weight: 700; }
            #selectorLabel { color: #374151; font-weight: 600; }
            #pageTitle { font-size: 20px; font-weight: 700; }

            QPushButton {
                background: #e5e7eb;
                border: none;
                border-radius: 10px;
                padding: 10px 14px;
                font-weight: 600;
            }
            QPushButton:hover { background: #d1d5db; }

            #sidebar QPushButton {
                background: transparent;
                color: #e5e7eb;
                text-align: left;
                padding-left: 12px;
                border-radius: 8px;
            }
            #sidebar QPushButton:hover { background: #374151; }
            #sidebar QPushButton:checked { background: #3b82f6; color: white; }

            QLineEdit, QDateEdit, QComboBox {
                background: white;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                padding: 8px;
            }
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus {
                border: 1px solid #3b82f6;
            }

            #panelCard, #statCard {
                background: white;
                border-radius: 14px;
            }
            #statValue { font-size: 30px; font-weight: 800; color: #1f2937; }
            #statTitle { color: #6b7280; font-weight: 600; }
            #balance { font-size: 26px; font-weight: 800; color: #3b82f6; }

            QTableWidget {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                gridline-color: #e5e7eb;
            }
            QHeaderView::section {
                background: #eef2ff;
                border: none;
                padding: 8px;
                font-weight: 700;
            }
            """
        )

    def switch_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

    def _require_event_context(self) -> bool:
        if self.current_event_id is None:
            QMessageBox.warning(self, "Event Belum Dipilih", "Tambahkan dan pilih event terlebih dahulu.")
            return False
        return True

    def on_event_changed(self) -> None:
        event_id = self.event_selector.currentData()
        self.current_event_id = int(event_id) if event_id is not None else None
        self.refresh_context_pages()

    def refresh_events_and_context(self) -> None:
        events = self.db.get_events()

        previous = self.current_event_id
        self.event_selector.blockSignals(True)
        self.event_selector.clear()

        selected_index = -1
        for row in events:
            self.event_selector.addItem(f"{row['name']} (#{row['id']})", row["id"])
            if previous == row["id"]:
                selected_index = self.event_selector.count() - 1

        if self.event_selector.count() > 0:
            self.event_selector.setCurrentIndex(0 if selected_index < 0 else selected_index)
            self.current_event_id = int(self.event_selector.currentData())
        else:
            self.current_event_id = None

        self.event_selector.blockSignals(False)
        self.refresh_event_table()
        self.refresh_context_pages()

    def refresh_context_pages(self) -> None:
        self.refresh_tasks()
        self.refresh_panitia()
        self.refresh_finance()
        self.refresh_dashboard()

    def refresh_event_table(self) -> None:
        data = self.db.get_events()
        self.table_events.setRowCount(0)
        for row_data in data:
            row = self.table_events.rowCount()
            self.table_events.insertRow(row)
            values = [
                str(row_data["id"]),
                row_data["name"],
                row_data["theme"],
                row_data["start_date"],
                row_data["end_date"],
            ]
            for col, value in enumerate(values):
                self.table_events.setItem(row, col, QTableWidgetItem(value))

    def refresh_tasks(self) -> None:
        self.table_tasks.setRowCount(0)
        if self.current_event_id is None:
            return
        data = self.db.get_tasks_by_event(self.current_event_id)
        for task in data:
            row = self.table_tasks.rowCount()
            self.table_tasks.insertRow(row)
            values = [
                str(task["id"]),
                task["title"],
                task["deadline"],
                task["notes"],
                task["status"],
            ]
            for col, value in enumerate(values):
                self.table_tasks.setItem(row, col, QTableWidgetItem(str(value)))

    def refresh_panitia(self) -> None:
        self.table_panitia.setRowCount(0)
        if self.current_event_id is None:
            return
        data = self.db.get_panitia_by_event(self.current_event_id)
        for member in data:
            row = self.table_panitia.rowCount()
            self.table_panitia.insertRow(row)
            values = [
                str(member["id"]),
                member["name"],
                member["role"],
                member["division"],
                member["contact"],
            ]
            for col, value in enumerate(values):
                self.table_panitia.setItem(row, col, QTableWidgetItem(str(value)))

    def refresh_finance(self) -> None:
        self.table_finance.setRowCount(0)
        if self.current_event_id is None:
            return
        data = self.db.get_keuangan_by_event(self.current_event_id)
        for tx in data:
            row = self.table_finance.rowCount()
            self.table_finance.insertRow(row)
            values = [
                str(tx["id"]),
                tx["tx_type"],
                f"{float(tx['amount']):,.2f}",
                tx["description"],
                tx["tx_date"],
            ]
            for col, value in enumerate(values):
                self.table_finance.setItem(row, col, QTableWidgetItem(str(value)))

    def refresh_dashboard(self) -> None:
        if self.current_event_id is None:
            self.card_total.set_value("0")
            self.card_done.set_value("0")
            self.card_pending.set_value("0")
            self.card_progress.set_value("0%")
            self.lbl_balance.setText("Rp 0")
            return

        stats = self.db.get_dashboard_stats(self.current_event_id)
        self.card_total.set_value(str(stats["total_tasks"]))
        self.card_done.set_value(str(stats["completed_tasks"]))
        self.card_pending.set_value(str(stats["incomplete_tasks"]))
        self.card_progress.set_value(f"{stats['progress']}%")
        self.lbl_balance.setText(f"Rp {stats['balance']:,.2f}")

    def add_event(self) -> None:
        name = self.event_name_input.text().strip()
        theme = self.event_theme_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Tidak Valid", "Nama kegiatan wajib diisi.")
            return

        start_date = self.event_start_input.date().toString("yyyy-MM-dd")
        end_date = self.event_end_input.date().toString("yyyy-MM-dd")
        self.db.add_event(name, theme, start_date, end_date)

        self.event_name_input.clear()
        self.event_theme_input.clear()
        self.refresh_events_and_context()

    def delete_selected_event(self) -> None:
        row = self.table_events.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Pilih Data", "Pilih event yang akan dihapus.")
            return
        event_id = int(self.table_events.item(row, 0).text())
        self.db.delete_event(event_id)
        self.refresh_events_and_context()

    def add_task(self) -> None:
        if not self._require_event_context():
            return

        title = self.task_title_input.text().strip()
        notes = self.task_notes_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Input Tidak Valid", "Judul task tidak boleh kosong.")
            return

        deadline = self.task_deadline_input.date().toString("yyyy-MM-dd")
        self.db.add_task(title, deadline, notes, self.current_event_id)
        self.task_title_input.clear()
        self.task_notes_input.clear()
        self.refresh_context_pages()

    def mark_task_done(self) -> None:
        if not self._require_event_context():
            return
        row = self.table_tasks.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Pilih Data", "Pilih task yang ingin ditandai selesai.")
            return

        task_id = int(self.table_tasks.item(row, 0).text())
        self.db.mark_task_done(task_id, self.current_event_id)
        self.refresh_context_pages()

    def delete_task(self) -> None:
        if not self._require_event_context():
            return
        row = self.table_tasks.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Pilih Data", "Pilih task yang ingin dihapus.")
            return

        task_id = int(self.table_tasks.item(row, 0).text())
        self.db.delete_task(task_id, self.current_event_id)
        self.refresh_context_pages()

    def add_panitia(self) -> None:
        if not self._require_event_context():
            return

        name = self.panitia_name_input.text().strip()
        role = self.panitia_role_input.text().strip()
        division = self.panitia_division_input.text().strip()
        contact = self.panitia_contact_input.text().strip()

        if not name or not role:
            QMessageBox.warning(self, "Input Tidak Valid", "Nama dan role panitia wajib diisi.")
            return

        self.db.add_panitia(name, role, division, contact, self.current_event_id)
        self.panitia_name_input.clear()
        self.panitia_role_input.clear()
        self.panitia_division_input.clear()
        self.panitia_contact_input.clear()
        self.refresh_context_pages()

    def delete_panitia(self) -> None:
        if not self._require_event_context():
            return
        row = self.table_panitia.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Pilih Data", "Pilih anggota yang ingin dihapus.")
            return

        member_id = int(self.table_panitia.item(row, 0).text())
        self.db.delete_panitia(member_id, self.current_event_id)
        self.refresh_context_pages()

    def add_finance(self) -> None:
        if not self._require_event_context():
            return

        tx_type = self.finance_type_input.currentText()
        amount_text = self.finance_amount_input.text().strip().replace(",", "")
        description = self.finance_desc_input.text().strip()

        if not amount_text:
            QMessageBox.warning(self, "Input Tidak Valid", "Nominal transaksi wajib diisi.")
            return

        try:
            amount = float(amount_text)
        except ValueError:
            QMessageBox.warning(self, "Input Tidak Valid", "Nominal harus berupa angka.")
            return

        if amount < 0:
            QMessageBox.warning(self, "Input Tidak Valid", "Nominal tidak boleh negatif.")
            return

        tx_date = self.finance_date_input.date().toString("yyyy-MM-dd")
        self.db.add_keuangan(tx_type, amount, description, tx_date, self.current_event_id)
        self.finance_amount_input.clear()
        self.finance_desc_input.clear()
        self.refresh_context_pages()

    def delete_finance(self) -> None:
        if not self._require_event_context():
            return
        row = self.table_finance.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Pilih Data", "Pilih transaksi yang ingin dihapus.")
            return

        tx_id = int(self.table_finance.item(row, 0).text())
        self.db.delete_keuangan(tx_id, self.current_event_id)
        self.refresh_context_pages()


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
