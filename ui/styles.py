"""
ui/styles.py
Dark-mode stylesheet and colour palette for the Application Whitelisting Tool.
"""

# ── Palette ────────────────────────────────────────────────────────────────────
DARK_BG      = "#0d1117"
PANEL_BG     = "#161b22"
CARD_BG      = "#1c2128"
BORDER       = "#30363d"
TEXT_PRIMARY = "#e6edf3"
TEXT_MUTED   = "#8b949e"
ACCENT_BLUE  = "#2f81f7"
ACCENT_GREEN = "#3fb950"
ACCENT_RED   = "#f85149"
ACCENT_AMBER = "#d29922"
ACCENT_PURP  = "#bc8cff"
HOVER_BG     = "#21262d"
SEL_BG       = "#1f3249"

# ── Main QSS Stylesheet ────────────────────────────────────────────────────────
DARK_STYLESHEET = f"""
/* ── Global ───────────────────────────────── */
QWidget {{
    background-color: {DARK_BG};
    color: {TEXT_PRIMARY};
    font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
    font-size: 13px;
}}

QMainWindow, QDialog {{
    background-color: {DARK_BG};
}}

/* ── Labels ───────────────────────────────── */
QLabel {{
    color: {TEXT_PRIMARY};
    background: transparent;
}}

QLabel#title_label {{
    font-size: 22px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    letter-spacing: 0.5px;
}}

QLabel#subtitle_label {{
    font-size: 12px;
    color: {TEXT_MUTED};
}}

QLabel#section_header {{
    font-size: 11px;
    font-weight: 600;
    color: {TEXT_MUTED};
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* ── Stat cards ───────────────────────────── */
QFrame#stat_card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 4px;
}}

/* ── Panels / Frames ──────────────────────── */
QFrame#panel {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}

/* ── Buttons ──────────────────────────────── */
QPushButton {{
    background-color: {CARD_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 16px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {HOVER_BG};
    border-color: #58a6ff;
}}
QPushButton:pressed {{
    background-color: #1c2128;
}}
QPushButton:disabled {{
    color: {TEXT_MUTED};
    border-color: {BORDER};
}}

QPushButton#btn_primary {{
    background-color: {ACCENT_BLUE};
    color: #ffffff;
    border: none;
    font-weight: 600;
}}
QPushButton#btn_primary:hover {{
    background-color: #4d94f7;
}}

QPushButton#btn_danger {{
    background-color: transparent;
    color: {ACCENT_RED};
    border: 1px solid {ACCENT_RED};
}}
QPushButton#btn_danger:hover {{
    background-color: rgba(248, 81, 73, 0.12);
}}

QPushButton#btn_success {{
    background-color: transparent;
    color: {ACCENT_GREEN};
    border: 1px solid {ACCENT_GREEN};
}}
QPushButton#btn_success:hover {{
    background-color: rgba(63, 185, 80, 0.12);
}}

/* ── Input fields ─────────────────────────── */
QLineEdit, QTextEdit {{
    background-color: {CARD_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: {SEL_BG};
}}
QLineEdit:focus, QTextEdit:focus {{
    border: 1px solid {ACCENT_BLUE};
}}

/* ── Table ────────────────────────────────── */
QTableWidget {{
    background-color: {PANEL_BG};
    alternate-background-color: {CARD_BG};
    gridline-color: {BORDER};
    border: 1px solid {BORDER};
    border-radius: 6px;
    outline: none;
}}
QTableWidget::item {{
    padding: 8px 12px;
    border: none;
    color: {TEXT_PRIMARY};
}}
QTableWidget::item:selected {{
    background-color: {SEL_BG};
    color: {TEXT_PRIMARY};
}}
QHeaderView::section {{
    background-color: {CARD_BG};
    color: {TEXT_MUTED};
    border: none;
    border-bottom: 1px solid {BORDER};
    border-right: 1px solid {BORDER};
    padding: 8px 12px;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QTableWidget QScrollBar:vertical {{
    background: {DARK_BG};
    width: 8px;
    border: none;
}}
QTableWidget QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 20px;
}}

/* ── ComboBox ─────────────────────────────── */
QComboBox {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    color: {TEXT_PRIMARY};
    min-width: 120px;
}}
QComboBox:hover {{
    border-color: {ACCENT_BLUE};
}}
QComboBox QAbstractItemView {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER};
    selection-background-color: {SEL_BG};
    color: {TEXT_PRIMARY};
    outline: none;
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

/* ── Tab Bar ──────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 6px;
    background: {PANEL_BG};
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {TEXT_MUTED};
    padding: 8px 20px;
    border-bottom: 2px solid transparent;
    font-weight: 500;
}}
QTabBar::tab:selected {{
    color: {TEXT_PRIMARY};
    border-bottom: 2px solid {ACCENT_BLUE};
}}
QTabBar::tab:hover {{
    color: {TEXT_PRIMARY};
}}

/* ── ScrollBars ───────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* ── GroupBox ─────────────────────────────── */
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    margin-top: 14px;
    padding: 8px;
    color: {TEXT_MUTED};
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    top: -1px;
    padding: 0 6px;
    background: {DARK_BG};
}}

/* ── Status bar ───────────────────────────── */
QStatusBar {{
    background: {PANEL_BG};
    color: {TEXT_MUTED};
    border-top: 1px solid {BORDER};
    font-size: 12px;
}}

/* ── ToolTip ──────────────────────────────── */
QToolTip {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER};
    color: {TEXT_PRIMARY};
    padding: 4px 8px;
    border-radius: 4px;
}}

/* ── MessageBox ───────────────────────────── */
QMessageBox {{
    background-color: {PANEL_BG};
}}
QMessageBox QPushButton {{
    min-width: 80px;
    padding: 6px 16px;
}}
"""
