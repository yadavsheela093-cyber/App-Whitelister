"""
ui/widgets.py
Reusable custom widgets: StatCard, BadgeLabel, ToastNotification.
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRect
from PyQt5.QtGui import QFont, QColor

from ui.styles import (
    CARD_BG, BORDER, TEXT_PRIMARY, TEXT_MUTED,
    ACCENT_GREEN, ACCENT_RED, ACCENT_AMBER, ACCENT_BLUE, PANEL_BG
)


class StatCard(QFrame):
    """A small stat card showing a label and a big number."""

    def __init__(self, title: str, value: str, color: str, parent=None):
        super().__init__(parent)
        self.setObjectName("stat_card")
        self._color = color

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 600;"
            f" text-transform: uppercase; letter-spacing: 0.5px; background: transparent;"
        )

        self._value_lbl = QLabel(value)
        self._value_lbl.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self._value_lbl.setStyleSheet(f"color: {color}; background: transparent;")

        layout.addWidget(self._title_lbl)
        layout.addWidget(self._value_lbl)
        self.setMinimumWidth(140)

    def set_value(self, value: str):
        self._value_lbl.setText(value)


STATUS_COLORS = {
    "ALLOWED":       (ACCENT_GREEN,  "#0d2818"),
    "BLOCKED":       (ACCENT_RED,    "#2d0f0e"),
    "HASH_MISMATCH": (ACCENT_AMBER,  "#2d1f00"),
    "ERROR":         (TEXT_MUTED,    "#1c2128"),
    "INFO":          (ACCENT_BLUE,   "#0d1f3c"),
}


class BadgeLabel(QWidget):
    """Coloured pill badge for status values."""

    def __init__(self, status: str, parent=None):
        super().__init__(parent)
        fg, bg = STATUS_COLORS.get(status, (TEXT_MUTED, CARD_BG))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        lbl = QLabel(status)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            f"color: {fg}; background-color: {bg};"
            f" border: 1px solid {fg}; border-radius: 10px;"
            f" padding: 2px 10px; font-size: 11px; font-weight: 600;"
        )
        layout.addWidget(lbl)


class ToastNotification(QFrame):
    """Floating toast that auto-dismisses after 3 seconds."""

    def __init__(self, message: str, status: str = "INFO", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        fg, bg = STATUS_COLORS.get(status, (TEXT_MUTED, CARD_BG))

        self.setStyleSheet(
            f"QFrame {{ background: {bg}; border: 1px solid {fg};"
            f" border-radius: 8px; padding: 4px; }}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)

        lbl = QLabel(message)
        lbl.setStyleSheet(f"color: {fg}; font-size: 13px; background: transparent;")
        lbl.setWordWrap(True)
        lbl.setMaximumWidth(320)
        layout.addWidget(lbl)

        self.adjustSize()

        QTimer.singleShot(3000, self.close)
