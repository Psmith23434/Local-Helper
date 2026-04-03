"""Centralised QSS stylesheets built from the active theme."""

from ui.theme import get as T


def global_qss() -> str:
    d = T()
    return f"""
* {{ font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 13px; color: {d['text']}; }}
QMainWindow, QWidget {{ background: {d['bg']}; }}
QDialog {{ background: {d['surface']}; }}

/* ── Menu bar ─────────────────────────────── */
QMenuBar {{
    background: {d['surface']};
    border-bottom: 1px solid {d['border']};
    padding: 2px 4px;
    color: {d['text']};
}}
QMenuBar::item {{ padding: 4px 10px; border-radius: 4px; }}
QMenuBar::item:selected {{ background: {d['accent_dim']}; color: #fff; }}
QMenu {{
    background: {d['surface2']};
    border: 1px solid {d['border']};
    border-radius: 6px;
    padding: 4px;
    color: {d['text']};
}}
QMenu::item {{ padding: 6px 20px; border-radius: 4px; }}
QMenu::item:selected {{ background: {d['accent']}; color: #fff; }}
QMenu::separator {{ height: 1px; background: {d['border']}; margin: 4px 8px; }}

/* ── Tab bar ──────────────────────────────── */
QTabWidget::pane {{
    border: none;
    background: {d['bg']};
}}
QTabBar {{
    background: {d['surface']};
}}
QTabBar::tab {{
    background: {d['tab_inactive']};
    color: {d['muted']};
    padding: 9px 22px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 13px;
    font-weight: 500;
    min-width: 100px;
}}
QTabBar::tab:selected {{
    background: {d['tab_active']};
    color: {d['text']};
    border-bottom: 2px solid {d['accent']};
    font-weight: 700;
}}
QTabBar::tab:hover:!selected {{
    background: {d['surface2']};
    color: {d['text']};
}}

/* ── Scrollbars ───────────────────────────── */
QScrollBar:vertical {{ background: {d['surface']}; width: 6px; border-radius: 3px; }}
QScrollBar::handle:vertical {{ background: {d['scrollbar']}; border-radius: 3px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: {d['muted']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: {d['surface']}; height: 6px; border-radius: 3px; }}
QScrollBar::handle:horizontal {{ background: {d['scrollbar']}; border-radius: 3px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Common widgets ───────────────────────── */
QSplitter::handle {{ background: {d['border']}; width: 1px; }}
QStatusBar {{
    background: {d['surface']};
    color: {d['muted']};
    border-top: 1px solid {d['border']};
    font-size: 11px;
    padding: 2px 8px;
}}
QToolTip {{
    background: {d['surface2']};
    color: {d['text']};
    border: 1px solid {d['border']};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}
QComboBox {{
    background: {d['surface2']};
    border: 1px solid {d['border']};
    border-radius: 6px;
    padding: 5px 8px;
    color: {d['text']};
    font-size: 12px;
    min-width: 140px;
}}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background: {d['surface2']};
    border: 1px solid {d['border']};
    selection-background-color: {d['accent']};
    color: {d['text']};
}}
QCheckBox {{ color: {d['muted']}; font-size: 12px; spacing: 5px; }}
QCheckBox:hover {{ color: {d['text']}; }}
QCheckBox::indicator {{
    width: 14px; height: 14px;
    border: 1px solid {d['border']};
    border-radius: 3px;
    background: {d['surface2']};
}}
QCheckBox::indicator:checked {{ background: {d['accent']}; border-color: {d['accent']}; }}
QLineEdit, QTextEdit {{
    background: {d['surface2']};
    border: 1px solid {d['border']};
    border-radius: 6px;
    color: {d['text']};
    padding: 5px 8px;
    selection-background-color: {d['accent']};
}}
QLineEdit:focus, QTextEdit:focus {{ border-color: {d['accent']}; }}
QLabel {{ background: transparent; }}
QPushButton {{
    background: {d['surface2']};
    border: 1px solid {d['border']};
    border-radius: 6px;
    color: {d['text']};
    padding: 5px 14px;
    font-size: 12px;
}}
QPushButton:hover {{ background: {d['surface3']}; border-color: {d['muted']}; }}
QPushButton:pressed {{ background: {d['faint']}; }}
QPushButton:disabled {{ color: {d['muted']}; background: {d['surface']}; }}
QListWidget {{
    background: transparent;
    border: none;
    outline: none;
}}
QListWidget::item {{
    background: transparent;
    color: {d['text']};
    padding: 7px 10px;
    border-radius: 6px;
    margin: 1px 2px;
    font-size: 12px;
}}
QListWidget::item:hover {{ background: {d['surface2']}; }}
QListWidget::item:selected {{ background: {d['accent_dim']}; color: #fff; }}
QGroupBox {{
    border: 1px solid {d['border']};
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
    color: {d['muted']};
    font-size: 11px;
    font-weight: 700;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
QSlider::groove:horizontal {{
    height: 4px;
    background: {d['border']};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {d['accent']};
    width: 14px; height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::sub-page:horizontal {{ background: {d['accent']}; border-radius: 2px; }}
QSpinBox {{
    background: {d['surface2']};
    border: 1px solid {d['border']};
    border-radius: 6px;
    color: {d['text']};
    padding: 4px 8px;
}}
"""


def accent_btn_qss() -> str:
    d = T()
    return (
        f"QPushButton {{ background: {d['accent']}; color: #fff; font-weight: 700; "
        f"border: none; border-radius: 8px; padding: 8px 18px; }}"
        f"QPushButton:hover {{ background: {d['accent_dim']}; }}"
        f"QPushButton:pressed {{ background: #4a3faa; }}"
        f"QPushButton:disabled {{ background: {d['faint']}; color: {d['muted']}; }}"
    )


def code_btn_qss() -> str:
    d = T()
    return (
        f"QPushButton {{ background: {d['surface3']}; color: {d['muted']}; "
        f"border: 1px solid {d['border']}; border-radius: 5px; "
        f"font-size: 11px; padding: 3px 10px; }}"
        f"QPushButton:hover {{ background: {d['surface2']}; color: {d['text']}; border-color: {d['muted']}; }}"
    )


def thread_list_qss() -> str:
    d = T()
    return (
        f"QListWidget {{ background: transparent; border: none; outline: none; }}"
        f"QListWidget::item {{ color: {d['text']}; padding: 8px 10px; border-radius: 6px; "
        f"margin: 1px 2px; font-size: 12px; }}"
        f"QListWidget::item:hover {{ background: {d['surface2']}; }}"
        f"QListWidget::item:selected {{ background: {d['accent_dim']}; color: #fff; }}"
    )
