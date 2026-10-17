"""
ui/dialogs.py
Modal dialogs: Add Application, Admin Login, Change Password.
"""

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QCheckBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.styles import (
    PANEL_BG, CARD_BG, BORDER, TEXT_PRIMARY, TEXT_MUTED,
    ACCENT_BLUE, ACCENT_RED, ACCENT_GREEN
)
from core import security


class AddAppDialog(QDialog):
    """Dialog for adding a new application to the whitelist."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Application to Whitelist")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._filepath = ""
        self._hash     = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # ── Title ──────────────────────────────────────────
        title = QLabel("Add Application")
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        layout.addWidget(title)

        sub = QLabel("Select an executable to add to the whitelist.")
        sub.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(sub)

        # ── File picker ─────────────────────────────────────
        file_row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Path to .exe file…")
        self.path_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedWidth(90)
        browse_btn.clicked.connect(self._browse)
        file_row.addWidget(self.path_edit)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        # ── Display name ────────────────────────────────────
        layout.addWidget(QLabel("Display Name"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Friendly name (auto-filled from filename)…")
        layout.addWidget(self.name_edit)

        # ── Hash preview ────────────────────────────────────
        hash_frame = QFrame()
        hash_frame.setStyleSheet(
            f"background: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 6px; padding: 4px;"
        )
        hash_layout = QVBoxLayout(hash_frame)
        hash_layout.setContentsMargins(10, 8, 10, 8)
        hash_layout.setSpacing(2)

        hash_title = QLabel("SHA-256 Hash")
        hash_title.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 600;")
        self.hash_label = QLabel("—")
        self.hash_label.setStyleSheet(
            f"color: {ACCENT_BLUE}; font-family: 'Consolas', monospace; font-size: 11px;"
        )
        self.hash_label.setWordWrap(True)
        hash_layout.addWidget(hash_title)
        hash_layout.addWidget(self.hash_label)
        layout.addWidget(hash_frame)

        # ── Buttons ─────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        self.add_btn = QPushButton("Add to Whitelist")
        self.add_btn.setObjectName("btn_primary")
        self.add_btn.setEnabled(False)
        self.add_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self.add_btn)
        layout.addLayout(btn_row)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Executable",
            os.path.expanduser("~"),
            "Executables (*.exe *.app *.sh *.py);;All Files (*)"
        )
        if not path:
            return
        self.path_edit.setText(path)

        # Auto-fill name
        if not self.name_edit.text():
            self.name_edit.setText(os.path.splitext(os.path.basename(path))[0])

        # Compute hash in-place (fast enough for UI)
        try:
            self._hash = security.compute_sha256(path)
            self._filepath = path
            self.hash_label.setText(self._hash)
            self.hash_label.setStyleSheet(
                f"color: {ACCENT_GREEN}; font-family: 'Consolas', monospace; font-size: 11px;"
            )
            self.add_btn.setEnabled(True)
        except RuntimeError as e:
            self.hash_label.setText(f"Error: {e}")
            self.hash_label.setStyleSheet(
                f"color: {ACCENT_RED}; font-family: 'Consolas', monospace; font-size: 11px;"
            )
            self.add_btn.setEnabled(False)

    def get_data(self) -> dict:
        return {
            "name":   self.name_edit.text().strip() or os.path.basename(self._filepath),
            "path":   self._filepath,
            "sha256": self._hash,
        }


class LoginDialog(QDialog):
    """Admin password prompt shown at startup if a password is configured."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Admin Authentication")
        self.setFixedWidth(380)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(28, 28, 28, 28)

        title = QLabel("🔐  Admin Login")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)

        sub = QLabel("Enter admin password to continue.")
        sub.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(sub)

        self.pwd_edit = QLineEdit()
        self.pwd_edit.setEchoMode(QLineEdit.Password)
        self.pwd_edit.setPlaceholderText("Password…")
        self.pwd_edit.returnPressed.connect(self._try_login)
        layout.addWidget(self.pwd_edit)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {ACCENT_RED}; font-size: 12px;")
        layout.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        login_btn = QPushButton("Login")
        login_btn.setObjectName("btn_primary")
        login_btn.clicked.connect(self._try_login)
        btn_row.addWidget(login_btn)
        layout.addLayout(btn_row)

    def _try_login(self):
        if security.verify_admin_password(self.pwd_edit.text()):
            self.accept()
        else:
            self.error_label.setText("Incorrect password. Please try again.")
            self.pwd_edit.clear()
            self.pwd_edit.setFocus()


class SetPasswordDialog(QDialog):
    """Dialog to set or change the admin password."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Admin Password")
        self.setFixedWidth(400)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(28, 28, 28, 28)

        title = QLabel("Set Admin Password")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        layout.addWidget(title)

        layout.addWidget(QLabel("New Password"))
        self.pwd1 = QLineEdit()
        self.pwd1.setEchoMode(QLineEdit.Password)
        self.pwd1.setPlaceholderText("Enter new password…")
        layout.addWidget(self.pwd1)

        layout.addWidget(QLabel("Confirm Password"))
        self.pwd2 = QLineEdit()
        self.pwd2.setEchoMode(QLineEdit.Password)
        self.pwd2.setPlaceholderText("Repeat password…")
        layout.addWidget(self.pwd2)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {ACCENT_RED}; font-size: 12px;")
        layout.addWidget(self.error_label)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save Password")
        save_btn.setObjectName("btn_primary")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _save(self):
        p1 = self.pwd1.text()
        p2 = self.pwd2.text()
        if not p1:
            self.error_label.setText("Password cannot be empty.")
            return
        if p1 != p2:
            self.error_label.setText("Passwords do not match.")
            return
        security.set_admin_password(p1)
        QMessageBox.information(self, "Success", "Admin password updated.")
        self.accept()
