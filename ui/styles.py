"""Centralised QSS stylesheets built from the active theme."""

from ui.theme import get as T


def global_qss() -> str:
    d = T()
    bg      = d["bg"]        # #0d0d0d  — the one true dark
    surf    = d["surface"]   # #141414
    surf2   = d["surface2"]  # #1a1a1a
    surf3   = d["surface3"]  # #1f1f1f
    border  = d["border"]    # #2a2a2a
    text    = d["text"]
    muted   = d["muted"]
    accent  = d["accent"]
    acc_dim = d["accent_dim"]
    faint   = d["faint"]
    scroll  = d["scrollbar"]

    return f"""
* {{ font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 13px; color: {text}; }}
QMainWindow, QWidget {{ background: {bg}; }}
QDialog {{ background: {surf}; }}

/* ── Menu bar (native, hidden — only used as fallback) ─── */
QMenuBar {{
    background: {surf2};
    border: none;
    padding: 0;
    color: {muted};
    font-size: 12px;
}}
QMenuBar::item {{ padding: 0 10px; height: 42px; background: transparent; }}
QMenuBar::item:selected {{ background: {surf3}; color: {text}; }}
QMenuBar::item:pressed  {{ background: {surf3}; color: {accent}; }}
QMenu {{
    background: {surf};
    border: 1px solid {border};
    border-radius: 0;
    padding: 4px 0;
    color: {text};
}}
QMenu::item {{ padding: 5px 20px; }}
QMenu::item:selected {{ background: {surf3}; color: {accent}; }}
QMenu::separator {{ height: 1px; background: {border}; margin: 3px 10px; }}

/* ── Tab widget ───────────────────────────── */
QTabWidget {{
    background: {bg};
    border: none;
}}
QTabWidget::pane {{
    border: none;
    background: {bg};
    /* kill the default 1px frame Qt draws around the pane */
    top: 0px;
}}
/* The bar strip itself — must match header surface2 exactly */
QTabBar {{
    background: {surf2};
    border: none;
    qproperty-drawBase: 0;
}}
QTabBar::tab {{
    background: {surf2};
    color: {muted};
    padding: 9px 22px;
    border: none;
    border-bottom: 2px solid transparent;
    border-right: 1px solid {border};
    font-size: 13px;
    font-weight: 500;
    min-width: 100px;
}}
QTabBar::tab:selected {{
    background: {surf2};
    color: {text};
    border-bottom: 2px solid {accent};
    font-weight: 700;
}}
QTabBar::tab:hover:!selected {{
    background: {surf3};
    color: {text};
}}
/* Fill the empty space to the right of the last tab */
QTabBar::scroller {{ width: 0; }}

/* ── Scrollbars ───────────────────────────── */
QScrollBar:vertical {{ background: {surf}; width: 6px; border-radius: 3px; }}
QScrollBar::handle:vertical {{ background: {scroll}; border-radius: 3px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: {muted}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: {surf}; height: 6px; border-radius: 3px; }}
QScrollBar::handle:horizontal {{ background: {scroll}; border-radius: 3px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Common widgets ───────────────────────── */
QSplitter::handle {{ background: {border}; width: 1px; }}
QStatusBar {{
    background: {surf};
    color: {muted};
    border-top: 1px solid {border};
    font-size: 11px;
    padding: 2px 8px;
}}
QToolTip {{
    background: {surf2};
    color: {text};
    border: 1px solid {border};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}
QComboBox {{
    background: {surf2};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 5px 8px;
    color: {text};
    font-size: 12px;
    min-width: 140px;
}}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background: {surf2};
    border: 1px solid {border};
    selection-background-color: {accent};
    color: {text};
}}
QCheckBox {{ color: {muted}; font-size: 12px; spacing: 5px; }}
QCheckBox:hover {{ color: {text}; }}
QCheckBox::indicator {{
    width: 14px; height: 14px;
    border: 1px solid {border};
    border-radius: 3px;
    background: {surf2};
}}
QCheckBox::indicator:checked {{ background: {accent}; border-color: {accent}; }}
QLineEdit, QTextEdit {{
    background: {surf2};
    border: 1px solid {border};
    border-radius: 6px;
    color: {text};
    padding: 5px 8px;
    selection-background-color: {accent};
}}
QLineEdit:focus, QTextEdit:focus {{ border-color: {accent}; }}
QLabel {{ background: transparent; }}
QPushButton {{
    background: {surf2};
    border: 1px solid {border};
    border-radius: 6px;
    color: {text};
    padding: 5px 14px;
    font-size: 12px;
}}
QPushButton:hover {{ background: {surf3}; border-color: {muted}; }}
QPushButton:pressed {{ background: {faint}; }}
QPushButton:disabled {{ color: {muted}; background: {surf}; }}
QListWidget {{
    background: transparent;
    border: none;
    outline: none;
}}
QListWidget::item {{
    background: transparent;
    color: {text};
    padding: 7px 10px;
    border-radius: 6px;
    margin: 1px 2px;
    font-size: 12px;
}}
QListWidget::item:hover {{ background: {surf2}; }}
QListWidget::item:selected {{ background: {acc_dim}; color: #fff; }}
QGroupBox {{
    border: 1px solid {border};
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
    color: {muted};
    font-size: 11px;
    font-weight: 700;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
QSlider::groove:horizontal {{
    height: 4px;
    background: {border};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {accent};
    width: 14px; height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::sub-page:horizontal {{ background: {accent}; border-radius: 2px; }}
QSpinBox {{
    background: {surf2};
    border: 1px solid {border};
    border-radius: 6px;
    color: {text};
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
