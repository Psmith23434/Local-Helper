"""Main application window — dark premium redesign."""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter, QStatusBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QFont
from ui.sidebar import Sidebar
from ui.chat_panel import ChatPanel


DARK = {
    "bg":          "#0d0d0d",
    "surface":     "#141414",
    "surface2":    "#1a1a1a",
    "border":      "#2a2a2a",
    "accent":      "#7c6af7",
    "accent_dim":  "#5a4fd1",
    "text":        "#e8e8e8",
    "text_muted":  "#888888",
    "green":       "#4ade80",
    "red":         "#f87171",
    "yellow":      "#fbbf24",
}


def apply_dark_palette(app_or_widget, d=DARK):
    p = QPalette()
    p.setColor(QPalette.Window,          QColor(d["bg"]))
    p.setColor(QPalette.WindowText,      QColor(d["text"]))
    p.setColor(QPalette.Base,            QColor(d["surface"]))
    p.setColor(QPalette.AlternateBase,   QColor(d["surface2"]))
    p.setColor(QPalette.Text,            QColor(d["text"]))
    p.setColor(QPalette.Button,          QColor(d["surface2"]))
    p.setColor(QPalette.ButtonText,      QColor(d["text"]))
    p.setColor(QPalette.Highlight,       QColor(d["accent"]))
    p.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    p.setColor(QPalette.ToolTipBase,     QColor(d["surface2"]))
    p.setColor(QPalette.ToolTipText,     QColor(d["text"]))
    p.setColor(QPalette.PlaceholderText, QColor(d["text_muted"]))
    app_or_widget.setPalette(p)


GLOBAL_QSS = f"""
* {{
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
    color: {DARK['text']};
}}
QMainWindow, QWidget {{
    background: {DARK['bg']};
}}
QSplitter::handle {{
    background: {DARK['border']};
    width: 1px;
}}
QStatusBar {{
    background: {DARK['surface']};
    color: {DARK['text_muted']};
    border-top: 1px solid {DARK['border']};
    font-size: 11px;
    padding: 2px 8px;
}}
QScrollBar:vertical {{
    background: {DARK['surface']};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {DARK['border']};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: #3a3a3a;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {DARK['surface']};
    height: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {DARK['border']};
    border-radius: 3px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
QToolTip {{
    background: {DARK['surface2']};
    color: {DARK['text']};
    border: 1px solid {DARK['border']};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Local Helper")
        self.resize(1280, 820)
        apply_dark_palette(self)
        self.setStyleSheet(GLOBAL_QSS)
        self.setFont(QFont("Segoe UI", 10))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        self.sidebar    = Sidebar(self)
        self.chat_panel = ChatPanel(self)
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.chat_panel)
        splitter.setSizes([260, 1020])
        layout.addWidget(splitter)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

        self.sidebar.thread_selected.connect(self.chat_panel.load_thread)
        self.sidebar.space_changed.connect(self.chat_panel.set_space)

    def set_status(self, msg: str):
        self.status.showMessage(msg)
