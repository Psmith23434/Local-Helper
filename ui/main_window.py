"""Main application window — frameless with custom title bar."""

import os
import urllib.request
import tempfile

from PyQt5.QtWidgets import (
    QMainWindow, QStatusBar, QMessageBox, QApplication,
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPalette, QColor, QFont, QFontDatabase
from ui.theme import get as T, set_theme
from ui.styles import global_qss


# ── Font loader — downloads Cinzel TTF once, caches in temp dir ──────────────
_CINZEL_FONT_ID = None

# Direct TTF download from GitHub (no API, works offline after first run)
_CINZEL_TTF_URL = (
    "https://github.com/google/fonts/raw/main/ofl/cinzel/"
    "Cinzel%5Bwght%5D.ttf"
)


def _load_cinzel() -> str:
    """Download Cinzel TTF once, register with Qt. Returns family name."""
    global _CINZEL_FONT_ID
    if _CINZEL_FONT_ID is not None:
        return _CINZEL_FONT_ID

    cache_path = os.path.join(tempfile.gettempdir(), "cinzel_variable.ttf")
    try:
        if not os.path.exists(cache_path):
            urllib.request.urlretrieve(_CINZEL_TTF_URL, cache_path)
        fid = QFontDatabase.addApplicationFont(cache_path)
        if fid >= 0:
            families = QFontDatabase.applicationFontFamilies(fid)
            if families:
                _CINZEL_FONT_ID = families[0]
                return _CINZEL_FONT_ID
    except Exception:
        pass  # no internet / any error → fall through to system fonts

    # Static call (PyQt5 ≥5.15.8 made hasFamily a static method)
    for f in ("Palatino Linotype", "Book Antiqua", "Palatino",
              "Georgia", "Times New Roman"):
        try:
            if QFontDatabase.hasFamily(f):
                _CINZEL_FONT_ID = f
                return f
        except Exception:
            pass

    _CINZEL_FONT_ID = "Georgia"
    return "Georgia"


def apply_dark_palette(widget):
    d = T()
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
    p.setColor(QPalette.PlaceholderText, QColor(d["muted"]))
    widget.setPalette(p)


# ── Custom title bar ──────────────────────────────────────────────────────────

class TitleBar(QWidget):
    """Drag-able title bar with fancy centered app name + window controls."""

    HEIGHT = 42

    def __init__(self, parent: QMainWindow):
        super().__init__(parent)
        self._win = parent
        self._drag_pos = None
        self.setFixedHeight(self.HEIGHT)
        self._display_font = _load_cinzel()
        self._build()

    def _build(self):
        d = T()
        self.setStyleSheet(
            f"background:{d['surface2']};"
            "border-bottom:1px solid #111;"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 0, 4, 0)
        lay.setSpacing(0)

        # Left spacer mirrors the 3 right-side buttons so title is truly centred
        self._left_spacer = QWidget()
        self._left_spacer.setFixedWidth(128)
        lay.addWidget(self._left_spacer)

        lay.addStretch()

        # ── App title ─────────────────────────────────────────────────────
        self._title_lbl = QLabel("Local Helper")
        title_font = QFont(self._display_font, 13)
        title_font.setLetterSpacing(QFont.AbsoluteSpacing, 2.5)
        title_font.setWeight(QFont.Medium)
        self._title_lbl.setFont(title_font)
        self._title_lbl.setAlignment(Qt.AlignCenter)
        self._title_lbl.setStyleSheet(
            f"color:{d.get('accent', '#2dd4bf')};background:transparent;"
        )
        lay.addWidget(self._title_lbl)

        lay.addStretch()

        # ── Window controls ──────────────────────────────────────────────────
        btn_css = (
            "QPushButton{{"
            "background:transparent;color:{fg};"
            "border:none;font-size:14px;"
            "min-width:40px;min-height:" + str(self.HEIGHT) + "px;padding:0;}}"
            "QPushButton:hover{{background:{hover};}}"
        )
        self._btn_min = QPushButton("⎯")
        self._btn_min.setStyleSheet(btn_css.format(fg=d["muted"], hover="#2a2a2a"))
        self._btn_min.setToolTip("Minimize")
        self._btn_min.clicked.connect(self._win.showMinimized)

        self._btn_max = QPushButton("□")
        self._btn_max.setStyleSheet(btn_css.format(fg=d["muted"], hover="#2a2a2a"))
        self._btn_max.setToolTip("Maximize / Restore")
        self._btn_max.clicked.connect(self._toggle_max)

        self._btn_close = QPushButton("✕")
        self._btn_close.setStyleSheet(btn_css.format(fg="#f87171", hover="#c0392b"))
        self._btn_close.setToolTip("Close")
        self._btn_close.clicked.connect(self._win.close)

        for b in (self._btn_min, self._btn_max, self._btn_close):
            b.setCursor(Qt.PointingHandCursor)
            lay.addWidget(b)

    def _toggle_max(self):
        if self._win.isMaximized():
            self._win.showNormal()
            self._btn_max.setText("□")
        else:
            self._win.showMaximized()
            self._btn_max.setText("❐")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self._win.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            if self._win.isMaximized():
                self._win.showNormal()
                self._btn_max.setText("□")
                self._drag_pos = QPoint(self._win.width() // 2, self.HEIGHT // 2)
            self._win.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._toggle_max()

    def update_theme(self):
        d = T()
        self.setStyleSheet(
            f"background:{d['surface2']};"
            "border-bottom:1px solid #111;"
        )
        self._title_lbl.setStyleSheet(
            f"color:{d.get('accent', '#2dd4bf')};background:transparent;"
        )


# ── Main window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, layout: str = "Tabbed"):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setWindowTitle("Local Helper")
        self.resize(1320, 860)
        self._layout_name = layout
        self._apply_style()
        self._build_shell(layout)
        self._build_statusbar()

    def _apply_style(self):
        apply_dark_palette(self)
        self.setStyleSheet(global_qss())
        self.setFont(QFont("Segoe UI", 10))

    def _build_shell(self, layout_name: str):
        self._title_bar = TitleBar(self)

        if layout_name == "Sidebar":
            from ui.layout_sidebar import SidebarLayout
            self._layout_widget = SidebarLayout(self)
        else:
            from ui.layout_tabbed import TabbedLayout
            self._layout_widget = TabbedLayout(self)

        shell = QWidget()
        vbox = QVBoxLayout(shell)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(self._title_bar)
        vbox.addWidget(self._layout_widget)
        self.setCentralWidget(shell)

    def _build_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        label = "📌 Sidebar" if self._layout_name == "Sidebar" else "📌 Tabbed"
        self.status.showMessage(f"Ready  ·  {label}")

    # ── Edge resize ────────────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        self._resize_edge = self._get_edge(event.pos())
        if self._resize_edge:
            self._resize_start_global = event.globalPos()
            self._resize_start_geom   = self.geometry()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        edge = self._get_edge(event.pos())
        self.setCursor({
            "bottom":       Qt.SizeVerCursor,
            "right":        Qt.SizeHorCursor,
            "bottom-right": Qt.SizeFDiagCursor,
        }.get(edge, Qt.ArrowCursor))
        if getattr(self, "_resize_edge", None):
            delta = event.globalPos() - self._resize_start_global
            g     = self._resize_start_geom
            if "right"  in self._resize_edge:
                self.resize(max(800,  g.width()  + delta.x()), self.height())
            if "bottom" in self._resize_edge:
                self.resize(self.width(), max(500, g.height() + delta.y()))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._resize_edge = None
        super().mouseReleaseEvent(event)

    def _get_edge(self, pos, margin=6):
        on_right  = pos.x() >= self.width()  - margin
        on_bottom = pos.y() >= self.height() - margin
        if on_right and on_bottom: return "bottom-right"
        if on_bottom:               return "bottom"
        if on_right:                return "right"
        return None

    # ── Close ───────────────────────────────────────────────────────────────
    def closeEvent(self, event):
        try:
            from ui.tab_settings import _lt_process
            if _lt_process is not None and _lt_process.poll() is None:
                _lt_process.terminate()
        except Exception:
            pass
        event.accept()

    # ── Public API ───────────────────────────────────────────────────────────
    def set_status(self, msg: str):
        self.status.showMessage(msg)

    def switch_theme(self, name: str):
        set_theme(name)
        self.reapply_theme()

    def reapply_theme(self):
        self._apply_style()
        self.setStyleSheet(global_qss())
        apply_dark_palette(self)
        self._title_bar.update_theme()

    def on_layout_change_requested(self, new_layout: str):
        if new_layout == self._layout_name:
            return
        reply = QMessageBox.question(
            self, "Restart required",
            f"Switch to {new_layout} layout?\n\nThe app will close. Please relaunch it.",
            QMessageBox.Ok | QMessageBox.Cancel
        )
        if reply == QMessageBox.Ok:
            try:
                with open("config.py", "r", encoding="utf-8") as f:
                    lines = f.readlines()
                with open("config.py", "w", encoding="utf-8") as f:
                    for line in lines:
                        if line.strip().startswith("GUI_LAYOUT"):
                            f.write(f'GUI_LAYOUT = "{new_layout}"\n')
                        else:
                            f.write(line)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not save layout:\n{e}")
                return
            QApplication.instance().quit()

    def show_about(self):
        QMessageBox.about(
            self, "About Local Helper",
            "<b>Local Helper</b><br>"
            "A private AI assistant powered by your own proxy.<br><br>"
            "Features: Multi-agent chat, GitHub integration, "
            "web search, markdown rendering, code save &amp; commit.<br><br>"
            "<i>Built with PyQt5 + requests</i>"
        )
