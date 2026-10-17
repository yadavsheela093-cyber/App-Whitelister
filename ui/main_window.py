"""
ui/main_window.py
Main application window for the Application Whitelisting Tool.
Tabs: Dashboard, Whitelist, Logs, Settings.
"""

import os
import sys
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QComboBox, QTabWidget, QFrame,
    QFileDialog, QMessageBox, QHeaderView, QSplitter,
    QGroupBox, QCheckBox, QStatusBar, QAbstractItemView,
    QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QFont, QIcon

from core import database as db, security
from core.exporter import export_logs_csv, export_whitelist_csv
from ui.styles import (
    DARK_STYLESHEET, ACCENT_GREEN, ACCENT_RED, ACCENT_AMBER,
    ACCENT_BLUE, TEXT_MUTED, TEXT_PRIMARY, PANEL_BG, CARD_BG, BORDER
)
from ui.widgets import StatCard, BadgeLabel, ToastNotification
from ui.dialogs import AddAppDialog, SetPasswordDialog


# ─────────────────────────────────────────────
#  Background refresh worker
# ─────────────────────────────────────────────

class RefreshWorker(QThread):
    stats_ready = pyqtSignal(dict)

    def run(self):
        self.stats_ready.emit(db.get_stats())


# ─────────────────────────────────────────────
#  Main Window
# ─────────────────────────────────────────────

class MainWindow(QMainWindow):

    # Signal emitted by the process monitor thread → safe UI update
    violation_signal = pyqtSignal(str, str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AppWhitelister  —  Application Whitelisting Tool")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 780)
        self.setStyleSheet(DARK_STYLESHEET)

        db.init_db()

        self._monitor: security.ProcessMonitor | None = None
        self._monitoring_active = False

        self.violation_signal.connect(self._handle_violation)

        self._build_ui()
        self._refresh_stats()
        self._load_whitelist()
        self._load_logs()

        # Auto-refresh every 10 seconds
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._auto_refresh)
        self._timer.start(10_000)

    # ──────────────────────────────────────────
    #  UI Construction
    # ──────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_header())

        # Tab container
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self._build_dashboard_tab(),  "  Dashboard  ")
        self.tabs.addTab(self._build_whitelist_tab(),  "  Whitelist  ")
        self.tabs.addTab(self._build_logs_tab(),       "  Logs  ")
        self.tabs.addTab(self._build_settings_tab(),   "  Settings  ")
        root_layout.addWidget(self.tabs)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._status("Ready")

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setStyleSheet(
            f"background: {PANEL_BG}; border-bottom: 1px solid {BORDER};"
        )
        header.setFixedHeight(64)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        # Logo + title
        shield = QLabel("🛡")
        shield.setFont(QFont("Segoe UI Emoji", 22))
        shield.setStyleSheet("background: transparent;")

        title = QLabel("AppWhitelister")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")

        version = QLabel("v1.0")
        version.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 11px; background: transparent; margin-top: 6px;"
        )

        # Monitor toggle button
        self.monitor_btn = QPushButton("▶  Start Monitor")
        self.monitor_btn.setObjectName("btn_success")
        self.monitor_btn.setFixedWidth(160)
        self.monitor_btn.clicked.connect(self._toggle_monitor)

        layout.addWidget(shield)
        layout.addSpacing(8)
        layout.addWidget(title)
        layout.addSpacing(6)
        layout.addWidget(version)
        layout.addStretch()
        layout.addWidget(self.monitor_btn)

        return header

    # ── Dashboard ──────────────────────────────────────────────────────────

    def _build_dashboard_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Stat cards row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.card_wl       = StatCard("Whitelisted",   "0", ACCENT_BLUE)
        self.card_allowed  = StatCard("Allowed",        "0", ACCENT_GREEN)
        self.card_blocked  = StatCard("Blocked",        "0", ACCENT_RED)
        self.card_mismatch = StatCard("Hash Mismatches","0", ACCENT_AMBER)
        self.card_total    = StatCard("Total Events",   "0", "#bc8cff")

        for card in (self.card_wl, self.card_allowed, self.card_blocked,
                     self.card_mismatch, self.card_total):
            cards_layout.addWidget(card)
        layout.addLayout(cards_layout)

        # ── Recent activity ────────────────────────────────────────────────
        act_frame = QFrame()
        act_frame.setObjectName("panel")
        act_layout = QVBoxLayout(act_frame)
        act_layout.setContentsMargins(16, 14, 16, 14)
        act_layout.setSpacing(10)

        hdr = QHBoxLayout()
        lbl = QLabel("Recent Activity")
        lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        refresh_btn = QPushButton("↻  Refresh")
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self._auto_refresh)
        hdr.addWidget(lbl)
        hdr.addStretch()
        hdr.addWidget(refresh_btn)
        act_layout.addLayout(hdr)

        self.recent_table = self._make_table(
            ["Timestamp", "Application", "Path", "Status", "Reason"]
        )
        self.recent_table.setMaximumHeight(280)
        act_layout.addWidget(self.recent_table)
        layout.addWidget(act_frame)

        # ── Quick-launch ───────────────────────────────────────────────────
        ql_frame = QFrame()
        ql_frame.setObjectName("panel")
        ql_layout = QVBoxLayout(ql_frame)
        ql_layout.setContentsMargins(16, 14, 16, 14)
        ql_layout.setSpacing(10)

        ql_hdr = QLabel("Quick Launch")
        ql_hdr.setFont(QFont("Segoe UI", 13, QFont.Bold))
        ql_layout.addWidget(ql_hdr)

        ql_row = QHBoxLayout()
        self.ql_path_edit = QLineEdit()
        self.ql_path_edit.setPlaceholderText("Path to executable…")
        ql_browse = QPushButton("Browse")
        ql_browse.setFixedWidth(80)
        ql_browse.clicked.connect(self._ql_browse)
        ql_run = QPushButton("Validate & Launch")
        ql_run.setObjectName("btn_primary")
        ql_run.setFixedWidth(150)
        ql_run.clicked.connect(self._ql_run)
        ql_row.addWidget(self.ql_path_edit)
        ql_row.addWidget(ql_browse)
        ql_row.addWidget(ql_run)
        ql_layout.addLayout(ql_row)

        self.ql_result_lbl = QLabel("")
        self.ql_result_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        ql_layout.addWidget(self.ql_result_lbl)
        layout.addWidget(ql_frame)

        layout.addStretch()
        return tab

    # ── Whitelist ──────────────────────────────────────────────────────────

    def _build_whitelist_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Toolbar
        toolbar = QHBoxLayout()
        self.wl_search = QLineEdit()
        self.wl_search.setPlaceholderText("🔍  Search by name or path…")
        self.wl_search.setMaximumWidth(320)
        self.wl_search.textChanged.connect(self._load_whitelist)

        add_btn = QPushButton("＋  Add Application")
        add_btn.setObjectName("btn_primary")
        add_btn.clicked.connect(self._add_app)

        remove_btn = QPushButton("✕  Remove Selected")
        remove_btn.setObjectName("btn_danger")
        remove_btn.clicked.connect(self._remove_app)

        run_btn = QPushButton("▶  Run Selected")
        run_btn.setObjectName("btn_success")
        run_btn.clicked.connect(self._run_selected)

        export_btn = QPushButton("↓  Export CSV")
        export_btn.clicked.connect(self._export_whitelist)

        toolbar.addWidget(self.wl_search)
        toolbar.addStretch()
        toolbar.addWidget(add_btn)
        toolbar.addWidget(remove_btn)
        toolbar.addWidget(run_btn)
        toolbar.addWidget(export_btn)
        layout.addLayout(toolbar)

        # Table
        self.wl_table = self._make_table(
            ["ID", "Name", "Path", "SHA-256 (first 16)", "Added On", "Status"]
        )
        self.wl_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.wl_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.wl_table.setContextMenuPolicy(Qt.ActionsContextMenu)
        layout.addWidget(self.wl_table)

        return tab

    # ── Logs ───────────────────────────────────────────────────────────────

    def _build_logs_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Toolbar
        toolbar = QHBoxLayout()
        self.log_filter = QComboBox()
        self.log_filter.addItems(["ALL", "ALLOWED", "BLOCKED", "HASH_MISMATCH", "ERROR"])
        self.log_filter.currentTextChanged.connect(self._load_logs)

        refresh_btn = QPushButton("↻  Refresh")
        refresh_btn.clicked.connect(self._load_logs)

        export_btn = QPushButton("↓  Export CSV")
        export_btn.clicked.connect(self._export_logs)

        clear_btn = QPushButton("⊘  Clear Logs")
        clear_btn.setObjectName("btn_danger")
        clear_btn.clicked.connect(self._clear_logs)

        toolbar.addWidget(QLabel("Filter:"))
        toolbar.addWidget(self.log_filter)
        toolbar.addStretch()
        toolbar.addWidget(refresh_btn)
        toolbar.addWidget(export_btn)
        toolbar.addWidget(clear_btn)
        layout.addLayout(toolbar)

        # Table
        self.log_table = self._make_table(
            ["ID", "Timestamp", "App Name", "Path", "Status", "Reason"]
        )
        self.log_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        layout.addWidget(self.log_table)

        return tab

    # ── Settings ───────────────────────────────────────────────────────────

    def _build_settings_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        # Security group
        sec_group = QGroupBox("Security")
        sec_layout = QVBoxLayout(sec_group)
        sec_layout.setSpacing(12)

        pwd_btn = QPushButton("🔑  Set / Change Admin Password")
        pwd_btn.setFixedWidth(260)
        pwd_btn.clicked.connect(self._set_password)
        sec_layout.addWidget(pwd_btn)

        self.hash_check = QCheckBox("Enforce hash verification on every launch")
        self.hash_check.setChecked(True)
        sec_layout.addWidget(self.hash_check)

        layout.addWidget(sec_group)

        # Monitor group
        mon_group = QGroupBox("Background Monitor")
        mon_layout = QVBoxLayout(mon_group)
        mon_layout.setSpacing(10)

        interval_row = QHBoxLayout()
        interval_row.addWidget(QLabel("Poll interval (seconds):"))
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["3", "5", "10", "30", "60"])
        self.interval_combo.setCurrentText("5")
        self.interval_combo.setFixedWidth(80)
        interval_row.addWidget(self.interval_combo)
        interval_row.addStretch()
        mon_layout.addLayout(interval_row)

        skip_sys = QCheckBox("Skip Windows system directories (recommended)")
        skip_sys.setChecked(True)
        skip_sys.setEnabled(False)   # always on — display only
        mon_layout.addWidget(skip_sys)

        layout.addWidget(mon_group)

        # DB group
        db_group = QGroupBox("Database")
        db_layout = QVBoxLayout(db_group)

        db_path_lbl = QLabel(f"Database path:  {db.DB_PATH}")
        db_path_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        db_path_lbl.setWordWrap(True)
        db_layout.addWidget(db_path_lbl)

        clear_db_btn = QPushButton("⊘  Clear All Logs")
        clear_db_btn.setObjectName("btn_danger")
        clear_db_btn.setFixedWidth(160)
        clear_db_btn.clicked.connect(self._clear_logs)
        db_layout.addWidget(clear_db_btn)

        layout.addWidget(db_group)

        # About
        about = QLabel(
            "AppWhitelister v1.0  ·  Built with Python 3 + PyQt5  ·  "
            "Portfolio / Final-Year Project"
        )
        about.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        layout.addStretch()
        layout.addWidget(about)

        return tab

    # ──────────────────────────────────────────
    #  Helpers
    # ──────────────────────────────────────────

    @staticmethod
    def _make_table(columns: list[str]) -> QTableWidget:
        tbl = QTableWidget()
        tbl.setColumnCount(len(columns))
        tbl.setHorizontalHeaderLabels(columns)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.setAlternatingRowColors(True)
        tbl.verticalHeader().setVisible(False)
        tbl.horizontalHeader().setStretchLastSection(True)
        tbl.setShowGrid(False)
        tbl.setSortingEnabled(True)
        return tbl

    def _status(self, msg: str) -> None:
        self.status_bar.showMessage(f"  {msg}  ·  {datetime.now().strftime('%H:%M:%S')}")

    def _toast(self, message: str, status: str = "INFO") -> None:
        toast = ToastNotification(message, status, self)
        toast.show_in(self)

    # ──────────────────────────────────────────
    #  Data Loaders
    # ──────────────────────────────────────────

    def _refresh_stats(self):
        stats = db.get_stats()
        self.card_wl.set_value(str(stats["whitelisted"]))
        self.card_allowed.set_value(str(stats["allowed"]))
        self.card_blocked.set_value(str(stats["blocked"]))
        self.card_mismatch.set_value(str(stats["hash_mismatch"]))
        self.card_total.set_value(str(stats["total_logs"]))

    def _load_whitelist(self):
        search = self.wl_search.text() if hasattr(self, "wl_search") else ""
        apps = db.get_all_apps(search)
        tbl = self.wl_table
        tbl.setRowCount(0)
        tbl.setSortingEnabled(False)
        for row_idx, app in enumerate(apps):
            tbl.insertRow(row_idx)
            tbl.setItem(row_idx, 0, QTableWidgetItem(str(app["id"])))
            tbl.setItem(row_idx, 1, QTableWidgetItem(app["name"]))
            tbl.setItem(row_idx, 2, QTableWidgetItem(app["path"]))
            tbl.setItem(row_idx, 3, QTableWidgetItem(app["sha256"][:16] + "…"))
            tbl.setItem(row_idx, 4, QTableWidgetItem(app["added_on"]))

            # Status badge widget
            status_text = "ACTIVE" if app["enabled"] else "DISABLED"
            badge = BadgeLabel(status_text)
            tbl.setCellWidget(row_idx, 5, badge)
            tbl.setRowHeight(row_idx, 44)

        tbl.setSortingEnabled(True)
        tbl.resizeColumnToContents(0)
        tbl.resizeColumnToContents(5)

    def _load_logs(self):
        status_filter = self.log_filter.currentText() if hasattr(self, "log_filter") else "ALL"
        logs = db.get_logs(status_filter)
        tbl = self.log_table
        tbl.setRowCount(0)
        tbl.setSortingEnabled(False)

        STATUS_COLORS = {
            "ALLOWED":       ACCENT_GREEN,
            "BLOCKED":       ACCENT_RED,
            "HASH_MISMATCH": ACCENT_AMBER,
            "ERROR":         TEXT_MUTED,
        }

        for row_idx, log in enumerate(logs):
            tbl.insertRow(row_idx)
            tbl.setItem(row_idx, 0, QTableWidgetItem(str(log["id"])))
            tbl.setItem(row_idx, 1, QTableWidgetItem(log["timestamp"]))
            tbl.setItem(row_idx, 2, QTableWidgetItem(log["app_name"]))
            tbl.setItem(row_idx, 3, QTableWidgetItem(log["path"]))

            badge = BadgeLabel(log["status"])
            tbl.setCellWidget(row_idx, 4, badge)

            reason_item = QTableWidgetItem(log["reason"] or "")
            reason_item.setForeground(QColor(TEXT_MUTED))
            tbl.setItem(row_idx, 5, reason_item)
            tbl.setRowHeight(row_idx, 40)

        tbl.setSortingEnabled(True)
        tbl.resizeColumnToContents(0)
        tbl.resizeColumnToContents(1)

        # Also populate recent-activity table (first 20 rows)
        recent_logs = db.get_logs("ALL", limit=20)
        rt = self.recent_table
        rt.setRowCount(0)
        rt.setSortingEnabled(False)
        for row_idx, log in enumerate(recent_logs):
            rt.insertRow(row_idx)
            rt.setItem(row_idx, 0, QTableWidgetItem(log["timestamp"]))
            rt.setItem(row_idx, 1, QTableWidgetItem(log["app_name"]))
            rt.setItem(row_idx, 2, QTableWidgetItem(log["path"]))
            badge = BadgeLabel(log["status"])
            rt.setCellWidget(row_idx, 3, badge)
            reason_item = QTableWidgetItem(log["reason"] or "")
            reason_item.setForeground(QColor(TEXT_MUTED))
            rt.setItem(row_idx, 4, reason_item)
            rt.setRowHeight(row_idx, 40)
        rt.setSortingEnabled(True)

    def _auto_refresh(self):
        self._refresh_stats()
        self._load_whitelist()
        self._load_logs()
        self._status("Auto-refreshed")

    # ──────────────────────────────────────────
    #  Whitelist Actions
    # ──────────────────────────────────────────

    def _add_app(self):
        dlg = AddAppDialog(self)
        if dlg.exec_() != AddAppDialog.Accepted:
            return
        data = dlg.get_data()
        ok, msg = db.add_app(data["name"], data["path"], data["sha256"])
        if ok:
            self._toast(f"Added: {data['name']}", "ALLOWED")
            self._status(msg)
            self._auto_refresh()
        else:
            QMessageBox.warning(self, "Cannot Add", msg)

    def _remove_app(self):
        row = self.wl_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Remove", "Please select an application first.")
            return
        app_id   = int(self.wl_table.item(row, 0).text())
        app_name = self.wl_table.item(row, 1).text()
        reply = QMessageBox.question(
            self, "Confirm Remove",
            f"Remove '{app_name}' from the whitelist?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            ok, msg = db.remove_app(app_id)
            self._toast(f"Removed: {app_name}", "BLOCKED")
            self._status(msg)
            self._auto_refresh()

    def _run_selected(self):
        row = self.wl_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Run", "Please select an application first.")
            return
        path = self.wl_table.item(row, 2).text()
        ok, msg = security.launch_application(path)
        status = "ALLOWED" if ok else "BLOCKED"
        self._toast(msg, status)
        self._status(msg)
        self._auto_refresh()

    def _export_whitelist(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Whitelist", "whitelist_export.csv", "CSV Files (*.csv)"
        )
        if path:
            ok, msg = export_whitelist_csv(path)
            QMessageBox.information(self, "Export", msg)

    # ──────────────────────────────────────────
    #  Log Actions
    # ──────────────────────────────────────────

    def _export_logs(self):
        status_filter = self.log_filter.currentText()
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Logs", "logs_export.csv", "CSV Files (*.csv)"
        )
        if path:
            ok, msg = export_logs_csv(path, status_filter)
            QMessageBox.information(self, "Export", msg)

    def _clear_logs(self):
        reply = QMessageBox.question(
            self, "Clear Logs",
            "Delete ALL log entries permanently?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            count = db.clear_logs()
            self._toast(f"Cleared {count} log entries.", "INFO")
            self._auto_refresh()

    # ──────────────────────────────────────────
    #  Quick Launch
    # ──────────────────────────────────────────

    def _ql_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Executable",
            os.path.expanduser("~"),
            "Executables (*.exe *.app *.sh *.py);;All Files (*)"
        )
        if path:
            self.ql_path_edit.setText(path)

    def _ql_run(self):
        path = self.ql_path_edit.text().strip()
        if not path:
            self.ql_result_lbl.setText("Please select a file first.")
            return
        ok, msg = security.launch_application(path)
        color = ACCENT_GREEN if ok else ACCENT_RED
        self.ql_result_lbl.setText(msg)
        self.ql_result_lbl.setStyleSheet(f"color: {color}; font-size: 12px;")
        status = "ALLOWED" if ok else "BLOCKED"
        self._toast(msg, status)
        self._auto_refresh()

    # ──────────────────────────────────────────
    #  Monitor
    # ──────────────────────────────────────────

    def _toggle_monitor(self):
        if self._monitoring_active:
            self._stop_monitor()
        else:
            self._start_monitor()

    def _start_monitor(self):
        interval = float(self.interval_combo.currentText())
        self._monitor = security.ProcessMonitor(
            on_violation=lambda n, p, r: self.violation_signal.emit(n, p, r),
            poll_interval=interval
        )
        self._monitor.start()
        self._monitoring_active = True
        self.monitor_btn.setText("■  Stop Monitor")
        self.monitor_btn.setObjectName("btn_danger")
        self.monitor_btn.setStyleSheet(
            f"color: {ACCENT_RED}; border: 1px solid {ACCENT_RED};"
            f" background: transparent; border-radius: 6px; padding: 6px 16px; font-weight: 500;"
        )
        self._status("Background monitor started")
        self._toast("Monitor started — watching processes.", "INFO")

    def _stop_monitor(self):
        if self._monitor:
            self._monitor.stop()
            self._monitor = None
        self._monitoring_active = False
        self.monitor_btn.setText("▶  Start Monitor")
        self.monitor_btn.setObjectName("btn_success")
        self.monitor_btn.setStyleSheet(
            f"color: {ACCENT_GREEN}; border: 1px solid {ACCENT_GREEN};"
            f" background: transparent; border-radius: 6px; padding: 6px 16px; font-weight: 500;"
        )
        self._status("Monitor stopped")

    def _handle_violation(self, name: str, path: str, reason: str):
        """Called on main thread when monitor detects an unlisted/mismatched process."""
        short_name = name if len(name) < 30 else name[:27] + "…"
        self._toast(f"⚠ Blocked: {short_name}\n{reason}", "BLOCKED")
        self._status(f"Violation detected: {name}")
        self._auto_refresh()

    # ──────────────────────────────────────────
    #  Settings
    # ──────────────────────────────────────────

    def _set_password(self):
        dlg = SetPasswordDialog(self)
        dlg.exec_()

    # ──────────────────────────────────────────
    #  Lifecycle
    # ──────────────────────────────────────────

    def closeEvent(self, event):
        self._stop_monitor()
        event.accept()
