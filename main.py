from __future__ import annotations

import importlib
import math
import re
import sys
from pathlib import Path
from typing import Any, cast

from PyQt6.QtCore import QDate, QEvent, QTimer, Qt
from PyQt6.QtGui import QColor, QEnterEvent, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
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
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database import DatabaseManager

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
except Exception:
    FigureCanvas = None
    Figure = None


class SortableTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other: QTableWidgetItem) -> bool:
        left = self.data(Qt.ItemDataRole.UserRole)
        right = other.data(Qt.ItemDataRole.UserRole)
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left < right
        return str(left).lower() < str(right).lower()


class StatCard(QFrame):
    def __init__(self, title: str, icon: str) -> None:
        super().__init__()
        self.setObjectName("statCard")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.value_label = QLabel("0")
        self.value_label.setObjectName("statValue")
        self.title_label = QLabel(f"{icon} {title}")
        self.title_label.setObjectName("statTitle")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)
        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)
        layout.addStretch()
        self.setMinimumHeight(142)

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(24)
        self.shadow.setOffset(0, 6)
        self.shadow.setColor(QColor(17, 24, 39, 28))
        self.setGraphicsEffect(self.shadow)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)

    def enterEvent(self, event: QEnterEvent) -> None:
        self.shadow.setBlurRadius(34)
        self.shadow.setOffset(0, 10)
        self.shadow.setColor(QColor(17, 24, 39, 42))
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.shadow.setBlurRadius(24)
        self.shadow.setOffset(0, 6)
        self.shadow.setColor(QColor(17, 24, 39, 28))
        super().leaveEvent(event)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.db = DatabaseManager()
        self.current_event_id: int | None = None
        self.current_event_name = ""

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
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(18)

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
        sidebar.setFixedWidth(270)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 22, 18, 22)
        layout.setSpacing(10)

        brand = QLabel("\U0001f3af Event Committee")
        brand.setObjectName("brand")
        layout.addWidget(brand)
        subtitle = QLabel("Management System")
        subtitle.setObjectName("brandSubtitle")
        layout.addWidget(subtitle)
        layout.addSpacing(16)

        self.nav_dashboard = QPushButton("\U0001f4ca  Dashboard")
        self.nav_events = QPushButton("\U0001f4c1  Kegiatan")
        self.nav_tasks = QPushButton("\U0001f4cc  Tasks")
        self.nav_panitia = QPushButton("\U0001f465  Panitia")
        self.nav_finance = QPushButton("\U0001f4b0  Keuangan")

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
            btn.setMinimumHeight(44)
            layout.addWidget(btn)

        self.nav_dashboard.setChecked(True)
        layout.addStretch()
        hint = QLabel("Workspace aktif mengikuti event yang dipilih.")
        hint.setObjectName("sidebarHint")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        return sidebar

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)

        title_block = QVBoxLayout()
        title_block.setContentsMargins(0, 0, 0, 0)
        title_block.setSpacing(2)
        title = QLabel("Event Committee Management System")
        title.setObjectName("headerTitle")
        self.workspace_label = QLabel("Belum ada event aktif")
        self.workspace_label.setObjectName("workspaceLabel")
        title_block.addWidget(title)
        title_block.addWidget(self.workspace_label)
        layout.addLayout(title_block)
        layout.addStretch()

        self.feedback_label = QLabel("")
        self.feedback_label.setObjectName("feedbackLabel")
        self.feedback_label.setVisible(False)
        layout.addWidget(self.feedback_label)

        selector_block = QVBoxLayout()
        selector_block.setContentsMargins(0, 0, 0, 0)
        selector_block.setSpacing(4)
        label = QLabel("Pilih Kegiatan")
        label.setObjectName("selectorLabel")
        self.event_selector = QComboBox()
        self.event_selector.setMinimumWidth(300)
        selector_block.addWidget(label)
        selector_block.addWidget(self.event_selector)
        layout.addLayout(selector_block)
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

    def create_card(self, object_name: str = "panelCard", *, shadow: bool = False) -> QFrame:
        card = QFrame()
        card.setObjectName(object_name)
        if shadow:
            card_shadow = QGraphicsDropShadowEffect(card)
            card_shadow.setBlurRadius(24)
            card_shadow.setOffset(0, 6)
            card_shadow.setColor(QColor(17, 24, 39, 28))
            card.setGraphicsEffect(card_shadow)
        return card

    def show_empty_state(self, message: str, *, min_height: int = 120) -> QLabel:
        label = QLabel(message)
        label.setObjectName("emptyState")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setMinimumHeight(min_height)
        return label

    def _build_dashboard_page(self) -> QWidget:
        page, layout = self._build_page_container("Dashboard (Per Kegiatan)")

        grid = QGridLayout()
        grid.setSpacing(16)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.card_events = StatCard("Events", "\U0001f4c1")
        self.card_total = StatCard("Tasks", "\U0001f4cc")
        self.card_done = StatCard("Done", "\u2705")
        self.card_progress = StatCard("Progress", "\U0001f4ca")

        grid.addWidget(self.card_events, 0, 0)
        grid.addWidget(self.card_total, 0, 1)
        grid.addWidget(self.card_done, 1, 0)
        grid.addWidget(self.card_progress, 1, 1)

        dashboard_actions = QHBoxLayout()
        dashboard_actions.setContentsMargins(0, 0, 0, 0)
        dashboard_actions.addStretch()
        self.btn_export_pdf = QPushButton("Export PDF")
        self.btn_export_pdf.setProperty("primary", True)
        self.btn_export_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
        dashboard_actions.addWidget(self.btn_export_pdf)

        finance_summary = self.create_card(shadow=True)
        fs_layout = QVBoxLayout(finance_summary)
        fs_layout.setContentsMargins(20, 18, 20, 18)
        fs_layout.setSpacing(8)
        fs_title = QLabel("Saldo Keuangan")
        fs_title.setObjectName("sectionTitle")
        fs_layout.addWidget(fs_title)
        fs_layout.addWidget(QLabel("Akumulasi transaksi event aktif"))
        self.lbl_balance = QLabel("Rp 0")
        self.lbl_balance.setObjectName("balance")
        self.lbl_target_dana = QLabel("Target dana: Rp 0")
        self.lbl_target_dana.setObjectName("divisionMeta")
        self.finance_target_progress = QProgressBar()
        self.finance_target_progress.setRange(0, 100)
        self.finance_target_progress.setValue(0)
        self.finance_target_progress.setFormat("0%")
        self.finance_target_progress.setTextVisible(True)
        fs_layout.addWidget(self.lbl_balance)
        fs_layout.addWidget(self.lbl_target_dana)
        fs_layout.addWidget(self.finance_target_progress)
        fs_layout.addStretch()

        self.task_chart_panel = self.create_card(shadow=True)
        chart_layout = QVBoxLayout(self.task_chart_panel)
        chart_layout.setContentsMargins(20, 18, 20, 18)
        chart_layout.setSpacing(12)
        chart_title = QLabel("Status Task")
        chart_title.setObjectName("sectionTitle")
        chart_layout.addWidget(chart_title)
        self.task_chart_widget = QWidget()
        self.task_chart_layout = QVBoxLayout(self.task_chart_widget)
        self.task_chart_layout.setContentsMargins(0, 0, 0, 0)
        self.task_chart_layout.setSpacing(0)
        chart_layout.addWidget(self.task_chart_widget, 1)

        self.division_panel = self.create_card(shadow=True)
        division_layout = QVBoxLayout(self.division_panel)
        division_layout.setContentsMargins(20, 18, 20, 18)
        division_layout.setSpacing(12)
        division_title = QLabel("Progress Divisi")
        division_title.setObjectName("sectionTitle")
        division_layout.addWidget(division_title)

        self.division_list_widget = QWidget()
        self.division_list_layout = QVBoxLayout(self.division_list_widget)
        self.division_list_layout.setContentsMargins(0, 0, 0, 0)
        self.division_list_layout.setSpacing(10)
        division_layout.addWidget(self.division_list_widget, 1)

        lower_layout = QHBoxLayout()
        lower_layout.setSpacing(16)
        lower_layout.addWidget(finance_summary, 1)
        lower_layout.addWidget(self.task_chart_panel, 1)
        lower_layout.addWidget(self.division_panel, 2)

        layout.addLayout(grid)
        layout.addLayout(dashboard_actions)
        layout.addLayout(lower_layout)
        layout.addStretch(1)
        return page

    def _build_event_page(self) -> QWidget:
        page, layout = self._build_page_container("Manajemen Kegiatan")

        form_card = QFrame()
        form_card.setObjectName("panelCard")
        form_layout = QFormLayout(form_card)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setContentsMargins(16, 16, 16, 16)
        form_layout.setSpacing(10)

        self.event_name_input = QLineEdit()
        self.event_name_input.setPlaceholderText("Contoh: Seminar Teknologi 2026")
        self.event_theme_input = QLineEdit()
        self.event_theme_input.setPlaceholderText("Tema kegiatan")
        self.event_target_input = QLineEdit()
        self.event_target_input.setPlaceholderText("Contoh: 7000000")
        self.event_start_input = QDateEdit()
        self.event_end_input = QDateEdit()
        for date_edit in (self.event_start_input, self.event_end_input):
            date_edit.setCalendarPopup(True)
            date_edit.setDate(QDate.currentDate())

        form_layout.addRow("Nama Kegiatan", self.event_name_input)
        form_layout.addRow("Tema", self.event_theme_input)
        form_layout.addRow("Target Dana", self.event_target_input)
        form_layout.addRow("Tanggal Mulai", self.event_start_input)
        form_layout.addRow("Tanggal Selesai", self.event_end_input)

        buttons = QHBoxLayout()
        self.btn_event_add = QPushButton("Tambah Event")
        self.btn_event_add.setProperty("primary", True)
        self.btn_event_add.setCursor(Qt.CursorShape.PointingHandCursor)
        buttons.addWidget(self.btn_event_add)
        buttons.addStretch()

        event_container = QVBoxLayout()
        event_container.setSpacing(10)
        event_container.addWidget(form_card)
        event_container.addLayout(buttons)

        self.table_events = self._create_table(["ID", "Nama", "Tema", "Target Dana", "Mulai", "Selesai", "Actions"])
        self._setup_action_table(self.table_events, 6)
        layout.addLayout(event_container)
        layout.addWidget(self.table_events, 1)
        return page

    def _build_task_page(self) -> QWidget:
        page, layout = self._build_page_container("Manajemen Tasks (Event Aktif)")

        form_card = QFrame()
        form_card.setObjectName("panelCard")
        form_layout = QFormLayout(form_card)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setContentsMargins(16, 16, 16, 16)
        form_layout.setSpacing(10)

        self.task_title_input = QLineEdit()
        self.task_title_input.setPlaceholderText("Judul task")
        self.task_deadline_input = QDateEdit()
        self.task_deadline_input.setCalendarPopup(True)
        self.task_deadline_input.setDate(QDate.currentDate())
        self.task_notes_input = QLineEdit()
        self.task_notes_input.setPlaceholderText("Catatan singkat")
        self.task_division_input = QComboBox()
        self.task_division_input.setEditable(True)
        self.task_division_input.addItems(
            ["Acara", "Humas", "Publikasi & Dokumentasi", "Perlengkapan", "Dana & Usaha"]
        )
        if self.task_division_input.lineEdit() is not None:
            self.task_division_input.lineEdit().setPlaceholderText("Pilih / ketik divisi")

        form_layout.addRow("Task", self.task_title_input)
        form_layout.addRow("Divisi", self.task_division_input)
        form_layout.addRow("Deadline", self.task_deadline_input)
        form_layout.addRow("Catatan", self.task_notes_input)

        controls = QHBoxLayout()
        self.btn_task_add = QPushButton("Tambah Task")
        self.btn_task_add.setProperty("primary", True)
        self.btn_task_add.setCursor(Qt.CursorShape.PointingHandCursor)
        controls.addWidget(self.btn_task_add)
        controls.addStretch()

        self.task_search_input = QLineEdit()
        self.task_search_input.setPlaceholderText("Cari task atau divisi...")

        self.table_tasks = self._create_table(["ID", "Task", "Divisi", "Deadline", "Catatan", "Status", "Actions"])
        self._setup_action_table(self.table_tasks, 6)

        layout.addWidget(form_card)
        layout.addLayout(controls)
        layout.addWidget(self.task_search_input)
        layout.addWidget(self.table_tasks, 1)
        return page

    def _build_panitia_page(self) -> QWidget:
        page, layout = self._build_page_container("Manajemen Panitia (Event Aktif)")

        form_card = QFrame()
        form_card.setObjectName("panelCard")
        form_layout = QFormLayout(form_card)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
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
        self.btn_panitia_add.setProperty("primary", True)
        self.btn_panitia_add.setCursor(Qt.CursorShape.PointingHandCursor)
        controls.addWidget(self.btn_panitia_add)
        controls.addStretch()

        self.panitia_search_input = QLineEdit()
        self.panitia_search_input.setObjectName("panitiaSearch")
        self.panitia_search_input.setPlaceholderText("Cari nama, jabatan, atau divisi...")

        self.table_panitia = self._create_table(["Nama", "Jabatan", "Divisi", "Aksi"])
        self.table_panitia.setObjectName("panitiaTable")
        self.create_table_style(self.table_panitia)
        self._setup_action_table(self.table_panitia, 3)

        layout.addWidget(form_card)
        layout.addLayout(controls)
        layout.addWidget(self.panitia_search_input)
        layout.addWidget(self.table_panitia, 1)
        return page

    def _build_finance_page(self) -> QWidget:
        page, layout = self._build_page_container("Manajemen Keuangan (Event Aktif)")

        form_card = QFrame()
        form_card.setObjectName("panelCard")
        form_layout = QFormLayout(form_card)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
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
        self.btn_finance_add.setProperty("primary", True)
        self.btn_finance_add.setCursor(Qt.CursorShape.PointingHandCursor)
        controls.addWidget(self.btn_finance_add)
        controls.addStretch()

        self.table_finance = self._create_table(["ID", "Tipe", "Nominal", "Deskripsi", "Tanggal", "Actions"])
        self._setup_action_table(self.table_finance, 5)
        layout.addWidget(form_card)
        layout.addLayout(controls)
        layout.addWidget(self.table_finance, 1)
        return page

    def _create_table(self, headers: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(70)
        table.verticalHeader().setMinimumSectionSize(70)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.setMouseTracking(True)
        table.setSortingEnabled(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return table

    def _setup_action_table(self, table: QTableWidget, action_col: int) -> None:
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(action_col, QHeaderView.ResizeMode.ResizeToContents)
        if table is getattr(self, "table_panitia", None):
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setStretchLastSection(False)
            header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

    def _connect_signals(self) -> None:
        self.nav_dashboard.clicked.connect(lambda: self.switch_page(0))
        self.nav_events.clicked.connect(lambda: self.switch_page(1))
        self.nav_tasks.clicked.connect(lambda: self.switch_page(2))
        self.nav_panitia.clicked.connect(lambda: self.switch_page(3))
        self.nav_finance.clicked.connect(lambda: self.switch_page(4))

        self.event_selector.currentIndexChanged.connect(self.on_event_changed)

        self.btn_event_add.clicked.connect(self.add_event)

        self.btn_task_add.clicked.connect(self.add_task)

        self.btn_panitia_add.clicked.connect(self.add_panitia)

        self.btn_finance_add.clicked.connect(self.add_finance)

        self.btn_export_pdf.clicked.connect(self.export_pdf_report)
        self.task_search_input.textChanged.connect(self.refresh_tasks)
        self.panitia_search_input.textChanged.connect(self.refresh_panitia)

    def _apply_styles(self) -> None:
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #f4f6f8; color: #111827; }
            QLabel { background: transparent; }
            #sidebar { background: #1f2937; }
            #brand { background: transparent; color: #f9fafb; font-weight: 800; font-size: 20px; }
            #brandSubtitle { background: transparent; color: #9ca3af; font-weight: 600; }
            #sidebarHint { background: #111827; color: #cbd5e1; border-radius: 8px; padding: 12px; }
            #header { background: white; border: 1px solid #e5e7eb; border-radius: 8px; }
            #headerTitle { background: transparent; font-size: 18px; font-weight: 800; }
            #workspaceLabel { background: transparent; color: #3b82f6; font-weight: 800; }
            #feedbackLabel { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; border-radius: 8px; padding: 8px 12px; font-weight: 800; }
            #selectorLabel { background: transparent; color: #374151; font-size: 12px; font-weight: 800; }
            #pageTitle { background: transparent; font-size: 24px; font-weight: 900; }

            QPushButton {
                background: #e5e7eb;
                border: none;
                border-radius: 8px;
                color: #111827;
                padding: 9px 14px;
                font-weight: 800;
            }
            QPushButton:hover { background: #d1d5db; }
            QPushButton:pressed { padding-top: 10px; padding-bottom: 8px; }
            QPushButton[primary="true"] { background: #3b82f6; color: white; padding-left: 18px; padding-right: 18px; }
            QPushButton[primary="true"]:hover { background: #2563eb; }

            QPushButton[action="true"] {
                border-radius: 8px;
                border: none;
                padding: 6px 10px;
                min-width: 34px;
                min-height: 34px;
                max-height: 34px;
                font-size: 14px;
                font-weight: 900;
            }
            QPushButton[action="true"][tone="edit"] { background: #dbeafe; color: #1d4ed8; }
            QPushButton[action="true"][tone="edit"]:hover { background: #bfdbfe; }
            QPushButton[action="true"][tone="success"] { background: #dcfce7; color: #15803d; }
            QPushButton[action="true"][tone="success"]:hover { background: #bbf7d0; }
            QPushButton[action="true"][tone="danger"] { background: #fee2e2; color: #dc2626; }
            QPushButton[action="true"][tone="danger"]:hover { background: #fecaca; }
            QPushButton[action="true"]:pressed { padding-top: 7px; padding-bottom: 5px; }
            QPushButton[action="true"]:disabled { background: #f3f4f6; color: #9ca3af; }

            #sidebar QPushButton {
                background: transparent;
                color: #e5e7eb;
                text-align: left;
                padding-left: 14px;
                border-radius: 8px;
            }
            #sidebar QPushButton:hover { background: #374151; padding-left: 18px; }
            #sidebar QPushButton:checked { background: #3b82f6; color: white; }

            QLineEdit, QDateEdit, QComboBox {
                background: white;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 9px 10px;
                min-height: 22px;
                selection-background-color: #3b82f6;
            }
            QLineEdit:hover, QDateEdit:hover, QComboBox:hover { border: 1px solid #9ca3af; }
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus { border: 1px solid #3b82f6; }
            QComboBox::drop-down, QDateEdit::drop-down { border: none; width: 28px; }

            #panelCard, #statCard {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
            #statValue { background: transparent; font-size: 38px; font-weight: 900; color: #111827; }
            #statTitle { background: transparent; color: #6b7280; font-weight: 800; }
            #balance { background: transparent; font-size: 32px; font-weight: 900; color: #3b82f6; }
            #sectionTitle { background: transparent; font-size: 16px; font-weight: 800; }
            #divisionRow, #divisionRowLow { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; }
            #divisionRowLow { background: #fff7ed; border: 1px solid #fed7aa; }
            #divisionMeta { background: transparent; color: #6b7280; font-weight: 700; }
            #divisionPercent { background: transparent; font-weight: 900; color: #111827; }
            #emptyState { background: transparent; color: #9ca3af; font-weight: 800; padding: 18px; }

            QProgressBar { background: #e5e7eb; border: none; border-radius: 6px; height: 12px; }
            QProgressBar::chunk { border-radius: 6px; background: #3b82f6; }
            QProgressBar#divisionBarLow::chunk { background: #f59e0b; }
            QProgressBar#divisionBarMid::chunk { background: #3b82f6; }
            QProgressBar#divisionBarHigh::chunk { background: #10b981; }

            QTableWidget {
                background: white;
                alternate-background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                gridline-color: transparent;
                outline: 0;
            }
            QTableWidget::item { border-bottom: 1px solid #eef2f7; padding: 8px; }
            QTableWidget::item:hover { background: #eff6ff; }
            QTableWidget::item:selected { background: #dbeafe; color: #111827; }
            QHeaderView::section {
                background: #f1f5f9;
                color: #334155;
                border: none;
                border-bottom: 1px solid #e5e7eb;
                padding: 10px 8px;
                font-weight: 900;
            }
            QDialog { background: #f4f6f8; }
            """
        )

    def create_table_style(self, table: QTableWidget) -> None:
        table.setStyleSheet(
            """
            QTableWidget#panitiaTable {
                background: #ffffff;
                alternate-background-color: #f8fafc;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                gridline-color: transparent;
                outline: 0;
                font-size: 10.5pt;
            }
            QTableWidget#panitiaTable::item {
                border: none;
                border-bottom: 1px solid #eef2f7;
                padding: 10px 12px;
            }
            QTableWidget#panitiaTable::item:hover {
                background: #f1f5f9;
            }
            QTableWidget#panitiaTable::item:selected {
                background: #dbeafe;
                color: #111827;
            }
            QHeaderView::section {
                background: #f3f4f6;
                color: #1f2937;
                border: none;
                border-bottom: 1px solid #e5e7eb;
                padding: 11px 10px;
                font-weight: 800;
                font-size: 11pt;
            }
            QLineEdit#panitiaSearch {
                background: #ffffff;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                padding: 10px 12px;
                font-size: 10.5pt;
            }
            """
        )

    def create_badge(self, text: str) -> QLabel:
        label = QLabel(text or "-")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        division_text = (text or "").strip().lower()
        badge_map = {
            "acara": ("#dbeafe", "#1d4ed8"),
            "konsumsi": ("#dcfce7", "#166534"),
            "humas": ("#ffedd5", "#c2410c"),
        }
        background, foreground = badge_map.get(division_text, ("#e5e7eb", "#374151"))
        label.setStyleSheet(
            f"""
            QLabel {{
                background: {background};
                color: {foreground};
                border-radius: 10px;
                padding: 6px 12px;
                font-size: 10pt;
                font-weight: 700;
            }}
            """
        )
        return label

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
        self.current_event_name = self.event_selector.currentText().split(" (#")[0] if event_id is not None else ""
        self._update_workspace_label()
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
            self.current_event_name = self.event_selector.currentText().split(" (#")[0]
        else:
            self.current_event_id = None
            self.current_event_name = ""

        self.event_selector.blockSignals(False)
        self._update_workspace_label()
        self.refresh_event_table()
        self.refresh_context_pages()

    def refresh_context_pages(self) -> None:
        self.refresh_tasks()
        self.refresh_panitia()
        self.refresh_finance()
        self.refresh_dashboard()

    def refresh_event_table(self) -> None:
        data = self.db.get_events()
        self.table_events.blockSignals(True)
        self.table_events.setSortingEnabled(False)
        self.table_events.clearSpans()
        self.table_events.setRowCount(0)
        for row_data in data:
            row = self.table_events.rowCount()
            self.table_events.insertRow(row)
            items = [
                self._create_text_item(str(row_data["id"]), editable=False, user_data=int(row_data["id"]), center=True),
                self._create_text_item(row_data["name"], editable=False),
                self._create_text_item(row_data["theme"] or "-", editable=False),
                self._create_text_item(
                    self._format_rupiah(float(row_data["target_dana"] or 0)),
                    editable=False,
                    user_data=float(row_data["target_dana"] or 0),
                    center=True,
                ),
                self._create_text_item(row_data["start_date"] or "-", editable=False, center=True),
                self._create_text_item(row_data["end_date"] or "-", editable=False, center=True),
            ]
            for col, item in enumerate(items):
                self.table_events.setItem(row, col, item)
            edit_btn = self._create_action_button("\u270f", "Edit data")
            edit_btn.clicked.connect(
                lambda _,
                eid=row_data["id"],
                name=row_data["name"],
                theme=row_data["theme"],
                start=row_data["start_date"],
                end=row_data["end_date"],
                target=row_data["target_dana"]: self._open_event_edit_dialog(eid, name, theme, start, end, target)
            )
            delete_btn = self._create_action_button("\U0001f5d1", "Hapus data", danger=True)
            delete_btn.clicked.connect(
                lambda _, eid=row_data["id"], name=row_data["name"]: self._handle_event_delete(eid, name)
            )
            self.table_events.setItem(row, 6, self._create_text_item("", editable=False))
            self.table_events.setCellWidget(row, 6, self._build_action_cell([edit_btn, delete_btn]))
        self._set_empty_table(self.table_events, "Silakan buat kegiatan terlebih dahulu")
        self.table_events.setSortingEnabled(bool(data))
        self.table_events.blockSignals(False)

    def refresh_tasks(self) -> None:
        self.table_tasks.blockSignals(True)
        self.table_tasks.setSortingEnabled(False)
        self.table_tasks.clearSpans()
        self.table_tasks.setRowCount(0)
        event_id = self.current_event_id
        if event_id is None:
            self._set_empty_table(self.table_tasks, "Silakan buat kegiatan terlebih dahulu")
            self.table_tasks.blockSignals(False)
            return
        search_text = self.task_search_input.text().strip()
        data = self.db.get_tasks_by_event(event_id, search_text)
        for task in data:
            row = self.table_tasks.rowCount()
            self.table_tasks.insertRow(row)
            completed = task["status"] == "Selesai"
            status_text = "Completed" if completed else "Pending"
            items = [
                self._create_text_item(str(task["id"]), editable=False, user_data=int(task["id"]), center=True),
                self._create_text_item(task["title"], editable=False),
                self._create_text_item(task["divisi"] or "-", editable=False, center=True),
                self._create_text_item(task["deadline"] or "-", editable=False, center=True),
                self._create_text_item(task["notes"] or "-", editable=False),
                self._create_text_item(status_text, editable=False, center=True),
            ]
            for col, item in enumerate(items):
                self.table_tasks.setItem(row, col, item)
            done_btn = self._create_action_button("\u2714", "Tandai selesai", success=True)
            done_btn.setEnabled(not completed)
            done_btn.clicked.connect(lambda _, tid=task["id"]: self._handle_task_done(tid))
            edit_btn = self._create_action_button("\u270f", "Edit data")
            edit_btn.clicked.connect(
                lambda _,
                tid=task["id"],
                title=task["title"],
                divisi=task["divisi"],
                deadline=task["deadline"]: self._open_task_edit_dialog(tid, title, divisi, deadline)
            )
            delete_btn = self._create_action_button("\U0001f5d1", "Hapus data", danger=True)
            delete_btn.clicked.connect(
                lambda _, tid=task["id"], title=task["title"]: self._handle_task_delete(tid, title)
            )
            self.table_tasks.setItem(row, 6, self._create_text_item("", editable=False))
            self.table_tasks.setCellWidget(row, 6, self._build_action_cell([done_btn, edit_btn, delete_btn]))
            self._apply_task_row_style(row, completed)
        self._set_empty_table(self.table_tasks, "Belum ada task")
        self.table_tasks.setSortingEnabled(bool(data))
        self.table_tasks.blockSignals(False)

    def refresh_panitia(self) -> None:
        self.table_panitia.blockSignals(True)
        self.table_panitia.setSortingEnabled(False)
        self.table_panitia.clearSpans()
        self.table_panitia.setRowCount(0)
        event_id = self.current_event_id
        if event_id is None:
            self._set_empty_table(self.table_panitia, "Silakan buat kegiatan terlebih dahulu")
            self.table_panitia.blockSignals(False)
            return
        search_text = self.panitia_search_input.text().strip().lower()
        raw_data = self.db.get_panitia_by_event(event_id)
        data = []
        for member in raw_data:
            if not search_text:
                data.append(member)
                continue
            haystack = " ".join(
                [
                    str(member["name"] or "").lower(),
                    str(member["role"] or "").lower(),
                    str(member["division"] or "").lower(),
                ]
            )
            if search_text in haystack:
                data.append(member)
        for member in data:
            row = self.table_panitia.rowCount()
            self.table_panitia.insertRow(row)
            items = [
                self._create_text_item(member["name"], editable=False),
                self._create_text_item(member["role"], editable=False, center=True),
            ]
            for col, item in enumerate(items):
                self.table_panitia.setItem(row, col, item)
            self.table_panitia.setCellWidget(row, 2, self.create_badge(member["division"] or "-"))
            edit_btn = self._create_action_button("\u270f", "Edit data")
            edit_btn.clicked.connect(
                lambda _,
                mid=member["id"],
                name=member["name"],
                role=member["role"],
                division=member["division"]: self._open_panitia_edit_dialog(mid, name, role, division)
            )
            delete_btn = self._create_action_button("\U0001f5d1", "Hapus data", danger=True)
            delete_btn.clicked.connect(
                lambda _, mid=member["id"], name=member["name"]: self._handle_panitia_delete(mid, name)
            )
            self.table_panitia.setItem(row, 3, self._create_text_item("", editable=False, center=True))
            self.table_panitia.setCellWidget(row, 3, self._build_action_cell([edit_btn, delete_btn]))
        self._set_empty_table(self.table_panitia, "Belum ada anggota panitia")
        self.table_panitia.setSortingEnabled(bool(data))
        self.table_panitia.blockSignals(False)

    def refresh_finance(self) -> None:
        self.table_finance.blockSignals(True)
        self.table_finance.setSortingEnabled(False)
        self.table_finance.clearSpans()
        self.table_finance.setRowCount(0)
        event_id = self.current_event_id
        if event_id is None:
            self._set_empty_table(self.table_finance, "Silakan buat kegiatan terlebih dahulu")
            self.table_finance.blockSignals(False)
            return
        data = self.db.get_keuangan_by_event(event_id)
        for tx in data:
            row = self.table_finance.rowCount()
            self.table_finance.insertRow(row)
            amount_value = float(tx["amount"])
            items = [
                self._create_text_item(str(tx["id"]), editable=False, user_data=int(tx["id"]), center=True),
                self._create_text_item(tx["tx_type"], editable=False, center=True),
                self._create_text_item(
                    self._format_rupiah(amount_value),
                    editable=False,
                    user_data=amount_value,
                    center=True,
                ),
                self._create_text_item(tx["description"] or "-", editable=False),
                self._create_text_item(tx["tx_date"] or "-", editable=False, center=True),
            ]
            for col, item in enumerate(items):
                self.table_finance.setItem(row, col, item)
            self._apply_finance_row_style(row, tx["tx_type"] == "Masuk")
            edit_btn = self._create_action_button("\u270f", "Edit data")
            edit_btn.clicked.connect(
                lambda _,
                tid=tx["id"],
                tx_type=tx["tx_type"],
                amount=amount_value,
                description=tx["description"]: self._open_finance_edit_dialog(tid, tx_type, amount, description)
            )
            delete_btn = self._create_action_button("\U0001f5d1", "Hapus data", danger=True)
            delete_btn.clicked.connect(
                lambda _, tid=tx["id"], desc=tx["description"]: self._handle_finance_delete(tid, desc)
            )
            self.table_finance.setItem(row, 5, self._create_text_item("", editable=False))
            self.table_finance.setCellWidget(row, 5, self._build_action_cell([edit_btn, delete_btn]))
        self._set_empty_table(self.table_finance, "Belum ada transaksi")
        self.table_finance.setSortingEnabled(bool(data))
        self.table_finance.blockSignals(False)

    def refresh_dashboard(self) -> None:
        self.card_events.set_value(str(len(self.db.get_events())))
        event_id = self.current_event_id
        if event_id is None:
            self.card_total.set_value("0")
            self.card_done.set_value("0")
            self.card_progress.set_value("0%")
            self._update_finance_target_card(0.0, 0.0)
            self._render_task_status_chart(0, 0, "Silakan buat kegiatan terlebih dahulu")
            self._render_division_progress([], "Silakan buat kegiatan terlebih dahulu")
            return

        stats = self.db.get_dashboard_stats(event_id)
        division_rows = self.db.get_division_progress(event_id)
        event = self.db.get_event_by_id(event_id)
        target_dana = float(event["target_dana"] or 0) if event is not None else 0.0
        total_tasks = int(stats["total_tasks"] or 0)
        completed_tasks = int(stats["completed_tasks"] or 0)
        incomplete_tasks = max(0, int(stats["incomplete_tasks"] or 0))
        progress = float(stats["progress"] or 0)
        self.card_total.set_value(str(total_tasks))
        self.card_done.set_value(str(completed_tasks))
        self.card_progress.set_value(f"{progress:g}%")
        self._update_finance_target_card(float(stats["balance"]), target_dana)
        self._render_task_status_chart(completed_tasks, incomplete_tasks)
        self._render_division_progress(division_rows)

    def _update_finance_target_card(self, balance: float, target_dana: float) -> None:
        self.lbl_balance.setText(f"{self._format_rupiah(balance)} / {self._format_rupiah(target_dana)}")
        self.lbl_target_dana.setText(f"Target dana: {self._format_rupiah(target_dana)}")
        progress = int(
            round(
                (balance / target_dana * 100)
                if target_dana > 0 and math.isfinite(balance) and math.isfinite(target_dana)
                else 0
            )
        )
        progress = max(0, min(progress, 100))
        self.finance_target_progress.setValue(progress)
        self.finance_target_progress.setFormat(f"{progress}%")

    def _render_task_status_chart(self, completed: int, pending: int, message: str = "Belum ada task") -> None:
        self._clear_layout(self.task_chart_layout)

        values = [float(max(0, completed)), float(max(0, pending))]
        if not all(math.isfinite(value) for value in values):
            self.task_chart_layout.addWidget(self.show_empty_state(message, min_height=180))
            return

        total = sum(values)
        if total <= 0:
            self.task_chart_layout.addWidget(self.show_empty_state(message, min_height=180))
            return

        if Figure is None or FigureCanvas is None:
            fallback = self.show_empty_state(
                f"Completed: {int(values[0])} | Pending: {int(values[1])}",
                min_height=180,
            )
            self.task_chart_layout.addWidget(fallback)
            return

        try:
            figure = Figure(figsize=(5.5, 5.5), dpi=100, facecolor="white")
            canvas = FigureCanvas(figure)
            canvas.setMinimumHeight(220)
            axes = figure.add_subplot(111)
            axes.pie(
                 values,
                 colors=["#10b981", "#f59e0b"],
                autopct=lambda pct: f"{pct:.0f}%" if pct > 0 else "",
                startangle=90,
                textprops={"color": "#111827", "fontsize": 10, "fontweight": "bold"},
                wedgeprops={"linewidth": 1, "edgecolor": "white"},
                )
            axes.legend(
                ["Selesai", "Belum"],
                loc="lower center",
                bbox_to_anchor=(0.5, -0.1),
                ncol=2,
                frameon=False
                )
            axes.axis("equal")
            axes.set_title("", fontsize=11, pad=10)
            axes.set_axis_off()
            figure.tight_layout(pad=1.5)
            self.task_chart_layout.addWidget(canvas)
            canvas.draw_idle()
        except Exception:
            self._clear_layout(self.task_chart_layout)
            self.task_chart_layout.addWidget(self.show_empty_state(message, min_height=180))

    def export_pdf_report(self) -> None:
        if not self._require_event_context():
            return
        event_id = self.current_event_id
        if event_id is None:
            return

        try:
            colors = cast(Any, importlib.import_module("reportlab.lib.colors"))
            pagesizes = cast(Any, importlib.import_module("reportlab.lib.pagesizes"))
            styles_module = cast(Any, importlib.import_module("reportlab.lib.styles"))
            platypus = cast(Any, importlib.import_module("reportlab.platypus"))
        except ModuleNotFoundError:
            QMessageBox.critical(
                self,
                "ReportLab Belum Terpasang",
                "Fitur export PDF membutuhkan package reportlab.",
            )
            return

        a4_page = pagesizes.A4
        paragraph_cls = platypus.Paragraph
        simple_doc_template_cls = platypus.SimpleDocTemplate
        spacer_cls = platypus.Spacer
        table_cls = platypus.Table
        table_style_cls = platypus.TableStyle

        event = self.db.get_event_by_id(event_id)
        if event is None:
            self._show_invalid("Event aktif tidak ditemukan.")
            return

        stats = self.db.get_dashboard_stats(event_id)
        division_rows = self.db.get_division_progress(event_id)
        panitia_rows = self.db.get_panitia_by_event(event_id)
        finance = self.db.get_financial_summary(event_id)

        safe_name = self._safe_filename(event["name"])
        output_path = Path(__file__).resolve().parent / f"report_{safe_name}.pdf"

        styles = styles_module.getSampleStyleSheet()
        story = [
            paragraph_cls(f"Event Report: {event['name']}", styles["Title"]),
            spacer_cls(1, 14),
        ]

        story.extend(
            self._pdf_section(
                "Event Information",
                [
                    ["Event Name", event["name"] or "-"],
                    ["Theme", event["theme"] or "-"],
                    ["Target Dana", self._format_rupiah(float(event["target_dana"] or 0))],
                    ["Start Date", event["start_date"] or "-"],
                    ["End Date", event["end_date"] or "-"],
                ],
                styles,
                colors,
                paragraph_cls,
                spacer_cls,
                table_cls,
                table_style_cls,
            )
        )
        story.extend(
            self._pdf_section(
                "Task Summary",
                [
                    ["Total Tasks", str(stats["total_tasks"])],
                    ["Completed Tasks", str(stats["completed_tasks"])],
                    ["Incomplete Tasks", str(stats["incomplete_tasks"])],
                    ["Progress", f"{stats['progress']}%"],
                ],
                styles,
                colors,
                paragraph_cls,
                spacer_cls,
                table_cls,
                table_style_cls,
            )
        )

        division_data = [["Division", "Total Tasks", "Completed Tasks", "Progress"]]
        for row in division_rows:
            total = int(row["total"] or 0)
            completed = int(row["selesai"] or 0)
            progress = round((completed / total * 100) if total else 0)
            division_data.append([row["divisi"], str(total), str(completed), f"{progress}%"])
        if len(division_data) == 1:
            division_data.append(["Belum ada data divisi", "-", "-", "-"])
        story.extend(
            self._pdf_section(
                "Division Progress",
                division_data,
                styles,
                colors,
                paragraph_cls,
                spacer_cls,
                table_cls,
                table_style_cls,
                header=True,
            )
        )

        panitia_data = [["Name", "Role", "Division"]]
        for row in panitia_rows:
            panitia_data.append([row["name"] or "-", row["role"] or "-", row["division"] or "-"])
        if len(panitia_data) == 1:
            panitia_data.append(["Belum ada anggota panitia", "-", "-"])
        story.extend(
            self._pdf_section(
                "Panitia List",
                panitia_data,
                styles,
                colors,
                paragraph_cls,
                spacer_cls,
                table_cls,
                table_style_cls,
                header=True,
            )
        )

        story.extend(
            self._pdf_section(
                "Financial Summary",
                [
                    ["Total Income", self._format_rupiah(float(finance["income"]))],
                    ["Total Expense", self._format_rupiah(float(finance["expense"]))],
                    ["Final Balance", self._format_rupiah(float(finance["balance"]))],
                    ["Target Dana", self._format_rupiah(float(event["target_dana"] or 0))],
                ],
                styles,
                colors,
                paragraph_cls,
                spacer_cls,
                table_cls,
                table_style_cls,
            )
        )

        document = simple_doc_template_cls(
            str(output_path),
            pagesize=a4_page,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        document.build(story)
        self._show_success(f"PDF berhasil dibuat: {output_path.name}")

    def _pdf_section(
        self,
        title: str,
        rows: list[list[str]],
        styles: Any,
        colors: Any,
        paragraph_cls: Any,
        spacer_cls: Any,
        table_cls: Any,
        table_style_cls: Any,
        *,
        header: bool = False,
    ) -> list[Any]:
        elements = [
            paragraph_cls(title, styles["Heading2"]),
            spacer_cls(1, 6),
        ]
        table = table_cls(rows, hAlign="LEFT")
        table_style = [
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
        if header:
            table_style.extend(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        else:
            table_style.append(("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"))
        table.setStyle(table_style_cls(table_style))
        elements.extend([table, spacer_cls(1, 14)])
        return elements

    def _safe_filename(self, value: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
        cleaned = cleaned.strip("_")
        return cleaned or "event"

    def _parse_money_input(self, value: str) -> int | None:
        text = value.strip().replace(".", "").replace(",", "")
        if not text:
            return 0
        if not text.isdigit():
            return None
        amount = int(text)
        return amount if amount >= 0 else None

    def _format_rupiah(self, value: float) -> str:
        return f"Rp {int(round(value)):,}".replace(",", ".")

    def add_event(self) -> None:
        name = self.event_name_input.text().strip()
        theme = self.event_theme_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Tidak Valid", "Nama kegiatan wajib diisi.")
            return
        target_dana = self._parse_money_input(self.event_target_input.text())
        if target_dana is None:
            self._show_invalid("Target dana harus berupa angka dan tidak boleh negatif.")
            return
        if self.event_end_input.date() < self.event_start_input.date():
            self._show_invalid("Tanggal selesai tidak boleh sebelum tanggal mulai.")
            return

        start_date = self.event_start_input.date().toString("yyyy-MM-dd")
        end_date = self.event_end_input.date().toString("yyyy-MM-dd")
        self.db.add_event(name, theme, start_date, end_date, target_dana)

        self.event_name_input.clear()
        self.event_theme_input.clear()
        self.event_target_input.clear()
        self.refresh_events_and_context()
        self._show_success("Event berhasil ditambahkan.")

    def _handle_event_delete(self, event_id: int, name: str) -> None:
        if not self._confirm_delete("Hapus Event", f"Hapus event '{name}'?"):
            return
        self.db.delete_event(event_id)
        self.refresh_events_and_context()
        self._show_success("Event berhasil dihapus.")

    def _open_event_edit_dialog(
        self, event_id: int, name: str, theme: str, start_date: str, end_date: str, target_dana: int | float = 0
    ) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Event")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        name_input = QLineEdit(name)
        theme_input = QLineEdit(theme)
        target_input = QLineEdit(str(int(float(target_dana or 0))))
        start_input = QDateEdit()
        start_input.setCalendarPopup(True)
        end_input = QDateEdit()
        end_input.setCalendarPopup(True)

        start_qdate = QDate.fromString(start_date, "yyyy-MM-dd")
        end_qdate = QDate.fromString(end_date, "yyyy-MM-dd")
        start_input.setDate(start_qdate if start_qdate.isValid() else QDate.currentDate())
        end_input.setDate(end_qdate if end_qdate.isValid() else QDate.currentDate())

        form.addRow("Nama Kegiatan", name_input)
        form.addRow("Tema", theme_input)
        form.addRow("Target Dana", target_input)
        form.addRow("Tanggal Mulai", start_input)
        form.addRow("Tanggal Selesai", end_input)

        layout.addLayout(form)

        actions = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_save = QPushButton("Save")
        btn_save.setProperty("primary", True)
        actions.addStretch()
        actions.addWidget(btn_cancel)
        actions.addWidget(btn_save)
        layout.addLayout(actions)

        btn_cancel.clicked.connect(dialog.reject)

        def on_save() -> None:
            new_name = name_input.text().strip()
            if not new_name:
                self._show_invalid("Nama kegiatan wajib diisi.")
                return
            new_target = self._parse_money_input(target_input.text())
            if new_target is None:
                self._show_invalid("Target dana harus berupa angka dan tidak boleh negatif.")
                return
            if end_input.date() < start_input.date():
                self._show_invalid("Tanggal selesai tidak boleh sebelum tanggal mulai.")
                return
            new_theme = theme_input.text().strip()
            new_start = start_input.date().toString("yyyy-MM-dd")
            new_end = end_input.date().toString("yyyy-MM-dd")
            self.db.update_event(event_id, new_name, new_theme, new_start, new_end, new_target)
            self._update_event_selector_text(event_id, new_name)
            if self.current_event_id == event_id:
                self.current_event_name = new_name
                self._update_workspace_label()
            dialog.accept()
            self.refresh_event_table()
            self.refresh_dashboard()
            self._show_success("Event berhasil diperbarui.")

        btn_save.clicked.connect(on_save)
        dialog.exec()

    def add_task(self) -> None:
        if not self._require_event_context():
            return
        event_id = self.current_event_id
        if event_id is None:
            return

        title = self.task_title_input.text().strip()
        notes = self.task_notes_input.text().strip()
        division = self.task_division_input.currentText().strip()
        if not title:
            QMessageBox.warning(self, "Input Tidak Valid", "Judul task tidak boleh kosong.")
            return
        if not division:
            QMessageBox.warning(self, "Input Tidak Valid", "Divisi wajib diisi.")
            return

        deadline = self.task_deadline_input.date().toString("yyyy-MM-dd")
        self.db.add_task(title, division, deadline, notes, event_id)
        self.task_title_input.clear()
        self.task_notes_input.clear()
        self.refresh_tasks()
        self.refresh_dashboard()
        self._show_success("Task berhasil ditambahkan.")

    def _handle_task_done(self, task_id: int) -> None:
        if not self._require_event_context():
            return
        event_id = self.current_event_id
        if event_id is None:
            return
        self.db.mark_task_done(task_id, event_id)
        self.refresh_tasks()
        self.refresh_dashboard()
        self._show_success("Task ditandai selesai.")

    def _handle_task_delete(self, task_id: int, title: str) -> None:
        if not self._require_event_context():
            return
        event_id = self.current_event_id
        if event_id is None:
            return
        if not self._confirm_delete("Hapus Task", f"Hapus task '{title}'?"):
            return
        self.db.delete_task(task_id, event_id)
        self.refresh_tasks()
        self.refresh_dashboard()
        self._show_success("Task berhasil dihapus.")

    def _open_task_edit_dialog(self, task_id: int, title: str, divisi: str, deadline: str) -> None:
        if not self._require_event_context():
            return
        event_id = self.current_event_id
        if event_id is None:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Task")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        title_input = QLineEdit(title)
        division_input = QComboBox()
        division_input.setEditable(True)
        division_input.addItems(
            ["Acara", "Humas", "Publikasi & Dokumentasi", "Perlengkapan", "Dana & Usaha"]
        )
        division_input.setCurrentText(divisi)

        deadline_input = QDateEdit()
        deadline_input.setCalendarPopup(True)
        deadline_qdate = QDate.fromString(deadline, "yyyy-MM-dd")
        deadline_input.setDate(deadline_qdate if deadline_qdate.isValid() else QDate.currentDate())

        form.addRow("Task", title_input)
        form.addRow("Divisi", division_input)
        form.addRow("Deadline", deadline_input)

        layout.addLayout(form)

        actions = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_save = QPushButton("Save")
        btn_save.setProperty("primary", True)
        actions.addStretch()
        actions.addWidget(btn_cancel)
        actions.addWidget(btn_save)
        layout.addLayout(actions)

        btn_cancel.clicked.connect(dialog.reject)

        def on_save() -> None:
            new_title = title_input.text().strip()
            new_division = division_input.currentText().strip()
            if not new_title:
                self._show_invalid("Judul task tidak boleh kosong.")
                return
            if not new_division:
                self._show_invalid("Divisi wajib diisi.")
                return
            new_deadline = deadline_input.date().toString("yyyy-MM-dd")
            self.db.update_task(task_id, new_title, new_division, new_deadline, event_id)
            dialog.accept()
            self.refresh_tasks()
            self.refresh_dashboard()
            self._show_success("Task berhasil diperbarui.")

        btn_save.clicked.connect(on_save)
        dialog.exec()

    def add_panitia(self) -> None:
        if not self._require_event_context():
            return
        event_id = self.current_event_id
        if event_id is None:
            return

        name = self.panitia_name_input.text().strip()
        role = self.panitia_role_input.text().strip()
        division = self.panitia_division_input.text().strip()
        contact = self.panitia_contact_input.text().strip()

        if not name or not role:
            QMessageBox.warning(self, "Input Tidak Valid", "Nama dan role panitia wajib diisi.")
            return

        self.db.add_panitia(name, role, division, contact, event_id)
        self.panitia_name_input.clear()
        self.panitia_role_input.clear()
        self.panitia_division_input.clear()
        self.panitia_contact_input.clear()
        self.refresh_panitia()
        self._show_success("Anggota panitia berhasil ditambahkan.")

    def _handle_panitia_delete(self, member_id: int, name: str) -> None:
        if not self._require_event_context():
            return
        event_id = self.current_event_id
        if event_id is None:
            return
        if not self._confirm_delete("Hapus Panitia", f"Hapus anggota '{name}'?"):
            return
        self.db.delete_panitia(member_id, event_id)
        self.refresh_panitia()
        self._show_success("Anggota berhasil dihapus.")

    def _open_panitia_edit_dialog(self, member_id: int, name: str, role: str, division: str) -> None:
        if not self._require_event_context():
            return
        event_id = self.current_event_id
        if event_id is None:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Panitia")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        name_input = QLineEdit(name)
        role_input = QLineEdit(role)
        division_input = QLineEdit(division)

        form.addRow("Nama", name_input)
        form.addRow("Role", role_input)
        form.addRow("Divisi", division_input)

        layout.addLayout(form)

        actions = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_save = QPushButton("Save")
        btn_save.setProperty("primary", True)
        actions.addStretch()
        actions.addWidget(btn_cancel)
        actions.addWidget(btn_save)
        layout.addLayout(actions)

        btn_cancel.clicked.connect(dialog.reject)

        def on_save() -> None:
            new_name = name_input.text().strip()
            new_role = role_input.text().strip()
            new_division = division_input.text().strip()
            if not new_name or not new_role:
                self._show_invalid("Nama dan role panitia wajib diisi.")
                return
            self.db.update_panitia(member_id, new_name, new_role, new_division, event_id)
            dialog.accept()
            self.refresh_panitia()
            self._show_success("Panitia berhasil diperbarui.")

        btn_save.clicked.connect(on_save)
        dialog.exec()

    def add_finance(self) -> None:
        if not self._require_event_context():
            return
        event_id = self.current_event_id
        if event_id is None:
            return

        tx_type = self.finance_type_input.currentText()
        amount_text = self.finance_amount_input.text().strip()
        description = self.finance_desc_input.text().strip()

        if not amount_text:
            QMessageBox.warning(self, "Input Tidak Valid", "Nominal transaksi wajib diisi.")
            return

        amount = self._parse_money_input(amount_text)
        if amount is None:
            QMessageBox.warning(self, "Input Tidak Valid", "Nominal harus berupa angka dan tidak boleh negatif.")
            return

        if amount < 0:
            QMessageBox.warning(self, "Input Tidak Valid", "Nominal tidak boleh negatif.")
            return

        tx_date = self.finance_date_input.date().toString("yyyy-MM-dd")
        self.db.add_keuangan(tx_type, amount, description, tx_date, event_id)
        self.finance_amount_input.clear()
        self.finance_desc_input.clear()
        self.refresh_finance()
        self.refresh_dashboard()
        self._show_success("Transaksi berhasil ditambahkan.")

    def _handle_finance_delete(self, transaction_id: int, description: str) -> None:
        if not self._require_event_context():
            return
        event_id = self.current_event_id
        if event_id is None:
            return
        if not self._confirm_delete("Hapus Transaksi", f"Hapus transaksi '{description}'?"):
            return
        self.db.delete_keuangan(transaction_id, event_id)
        self.refresh_finance()
        self.refresh_dashboard()
        self._show_success("Transaksi berhasil dihapus.")

    def _open_finance_edit_dialog(
        self, transaction_id: int, tx_type: str, amount: float, description: str
    ) -> None:
        if not self._require_event_context():
            return
        event_id = self.current_event_id
        if event_id is None:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Transaksi")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        type_input = QComboBox()
        type_input.addItems(["Masuk", "Keluar"])
        type_input.setCurrentText(tx_type)

        amount_input = QLineEdit(f"{amount:g}")
        desc_input = QLineEdit(description)

        form.addRow("Tipe", type_input)
        form.addRow("Nominal", amount_input)
        form.addRow("Deskripsi", desc_input)

        layout.addLayout(form)

        actions = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_save = QPushButton("Save")
        btn_save.setProperty("primary", True)
        actions.addStretch()
        actions.addWidget(btn_cancel)
        actions.addWidget(btn_save)
        layout.addLayout(actions)

        btn_cancel.clicked.connect(dialog.reject)

        def on_save() -> None:
            new_type = type_input.currentText().strip()
            amount_text = amount_input.text().strip()
            if not amount_text:
                self._show_invalid("Nominal transaksi wajib diisi.")
                return
            new_amount = self._parse_money_input(amount_text)
            if new_amount is None:
                self._show_invalid("Nominal harus berupa angka dan tidak boleh negatif.")
                return
            if new_amount < 0:
                self._show_invalid("Nominal tidak boleh negatif.")
                return
            new_description = desc_input.text().strip()
            self.db.update_transaksi(transaction_id, new_type, new_amount, new_description, event_id)
            dialog.accept()
            self.refresh_finance()
            self.refresh_dashboard()
            self._show_success("Transaksi berhasil diperbarui.")

        btn_save.clicked.connect(on_save)
        dialog.exec()

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    child_widget = child.widget()
                    if child_widget is not None:
                        child_widget.deleteLater()

    def _render_division_progress(self, rows: list, message: str = "Belum ada data divisi") -> None:
        self._clear_layout(self.division_list_layout)
        if not rows:
            self.division_list_layout.addWidget(self.show_empty_state(message))
            return

        for row in rows:
            total = int(row["total"]) if row["total"] is not None else 0
            selesai = int(row["selesai"]) if row["selesai"] is not None else 0
            progress = int(round((selesai / total * 100) if total > 0 else 0))
            progress = max(0, min(progress, 100))
            divisi = row["divisi"]

            row_frame = QFrame()
            row_frame.setObjectName("divisionRowLow" if progress < 50 else "divisionRow")
            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(12, 10, 12, 10)
            row_layout.setSpacing(10)

            name_label = QLabel(divisi)
            name_label.setMinimumWidth(120)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(progress)
            bar.setTextVisible(False)
            bar.setObjectName("divisionBarLow" if progress < 50 else "divisionBarMid" if progress < 80 else "divisionBarHigh")

            counts_label = QLabel(f"{selesai} dari {total} task selesai")
            counts_label.setObjectName("divisionMeta")
            percent_label = QLabel(f"{progress}%")
            percent_label.setObjectName("divisionPercent")
            percent_label.setMinimumWidth(54)
            percent_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            row_layout.addWidget(name_label)
            row_layout.addWidget(bar, 1)
            row_layout.addWidget(counts_label)
            row_layout.addWidget(percent_label)

            self.division_list_layout.addWidget(row_frame)

    def _set_empty_table(self, table: QTableWidget, message: str = "Belum ada data") -> None:
        if table.rowCount() > 0:
            return
        table.insertRow(0)
        table.setSpan(0, 0, 1, table.columnCount())
        item = self._create_text_item(message, editable=False, center=True)
        item.setForeground(QColor("#9ca3af"))
        font = item.font()
        font.setBold(True)
        if table is self.table_panitia:
            font.setPointSize(12)
        item.setFont(font)
        table.setItem(0, 0, item)
        table.setRowHeight(0, 72 if table is self.table_panitia else 62)

    def _create_text_item(
        self, text: str, *, editable: bool = False, user_data: object | None = None, center: bool = False
    ) -> QTableWidgetItem:
        item = SortableTableWidgetItem(str(text))
        item.setData(Qt.ItemDataRole.UserRole, user_data if user_data is not None else str(text))
        if not editable:
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item.setToolTip(str(text))
        if center:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return item

    def _create_action_button(
        self, text: str, tooltip: str, *, danger: bool = False, success: bool = False, wide: bool = False
    ) -> QPushButton:
        btn = QPushButton(text)
        btn.setProperty("action", True)
        tone = "danger" if danger else "success" if success else "edit"
        btn.setProperty("tone", tone)
        if danger:
            btn.setProperty("danger", True)
        if success:
            btn.setProperty("success", True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.setFont(QFont("Segoe UI Emoji", 11, QFont.Weight.Bold))
        if wide:
            btn.setFixedHeight(34)
            btn.setMinimumWidth(78)
        else:
            btn.setFixedSize(34, 34)
        return btn

    def _build_action_cell(self, buttons: list[QPushButton]) -> QWidget:
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        wrapper.setMinimumHeight(44)
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for btn in buttons:
            btn.setSizePolicy(btn.sizePolicy().Policy.Fixed, btn.sizePolicy().Policy.Fixed)
            layout.addWidget(btn)
        return wrapper

    def _apply_task_row_style(self, row: int, completed: bool) -> None:
        background = QColor("#ecfdf5") if completed else QColor("#fffbeb")
        foreground = QColor("#047857") if completed else QColor("#b45309")
        status_item = self.table_tasks.item(row, 5)
        if status_item is not None:
            status_item.setBackground(background)
            status_item.setForeground(foreground)
            status_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

    def _apply_finance_row_style(self, row: int, income: bool) -> None:
        color = QColor("#047857") if income else QColor("#b91c1c")
        background = QColor("#ecfdf5") if income else QColor("#fef2f2")
        for col in (1, 2):
            item = self.table_finance.item(row, col)
            if item is not None:
                item.setForeground(color)
                item.setBackground(background)
                item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

    def _confirm_delete(self, title: str, message: str) -> bool:
        response = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return response == QMessageBox.StandardButton.Yes

    def _show_invalid(self, message: str) -> None:
        QMessageBox.warning(self, "Input Tidak Valid", message)

    def _show_success(self, message: str) -> None:
        self.feedback_label.setText(message)
        self.feedback_label.setVisible(True)
        QTimer.singleShot(2600, lambda: self.feedback_label.setVisible(False))

    def _update_workspace_label(self) -> None:
        if self.current_event_id is None:
            self.workspace_label.setText("Belum ada event aktif")
            return
        self.workspace_label.setText(f"Workspace aktif: {self.current_event_name} (#{self.current_event_id})")

    def _update_event_selector_text(self, event_id: int, name: str) -> None:
        for i in range(self.event_selector.count()):
            if int(self.event_selector.itemData(i)) == event_id:
                self.event_selector.setItemText(i, f"{name} (#{event_id})")
                break


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
