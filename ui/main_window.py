"""Main application window — frameless with custom title bar."""

import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QStatusBar, QMessageBox, QApplication,
    QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPalette, QColor, QFont
from ui.theme import get as T, set_theme
from ui.styles import global_qss


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
    """Frameless drag-able title bar with minimize / maximize / close."""

    HEIGHT = 38

    def __init__(self, parent: QMainWindow):
        super().__init__(parent)
        self._win = parent
        self._drag_pos = None
        self._maximized = False
        self.setFixedHeight(self.HEIGHT)
        self._build()

    def _build(self):
        d = T()
        self.setStyleSheet(
            f"background:{d['surface2']};"
            "border-bottom:1px solid #1a1a1a;"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 4, 0)
        lay.setSpacing(0)

        # App icon + title
        self._title_lbl = QLabel("Local Helper")
        self._title_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._title_lbl.setStyleSheet(f"color:{d['text']};background:transparent;")
        lay.addWidget(self._title_lbl)
        lay.addStretch()

        # Window controls
        btn_style = (
            "QPushButton{{"
            "  background:transparent;color:{fg};"
            "  border:none;font-size:15px;"
            "  min-width:40px;min-height:{h}px;"
            "  padding:0;"
            "}}"
            "QPushButton:hover{{background:{hover};}}"
        )
        h = self.HEIGHT

        self._btn_min = QPushButton("⎯")
        self._btn_min.setStyleSheet(
            btn_style.format(fg=d["muted"], hover="#333333", h=h)
        )
        self._btn_min.setToolTip("Minimize")
        self._btn_min.clicked.connect(self._win.showMinimized)

        self._btn_max = QPushButton("□")
        self._btn_max.setStyleSheet(
            btn_style.format(fg=d["muted"], hover="#333333", h=h)
        )
        self._btn_max.setToolTip("Maximize / Restore")
        self._btn_max.clicked.connect(self._toggle_max)

        self._btn_close = QPushButton("✕")
        self._btn_close.setStyleSheet(
            btn_style.format(fg="#f87171", hover="#c0392b", h=h)
        )
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

    # ── Drag to move ─────────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self._win.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            if self._win.isMaximized():
                # Unmaximize and warp to mouse
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
        self._title_lbl.setStyleSheet(f"color:{d['text']};background:transparent;")
        self.setStyleSheet(
            f"background:{d['surface2']};"
            "border-bottom:1px solid #1a1a1a;"
        )


# ── Main window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, layout: str = "Tabbed"):
        super().__init__()
        # Remove native OS title bar
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        self.setWindowTitle("Local Helper")
        self.resize(1320, 860)
        self._layout_name = layout
        self._apply_style()

        # Custom title bar injected as a menu-bar replacement
        self._title_bar = TitleBar(self)
        self.setMenuWidget(self._title_bar)

        self._load_layout(layout)
        self._build_statusbar()

    def _apply_style(self):
        apply_dark_palette(self)
        self.setStyleSheet(global_qss())
        self.setFont(QFont("Segoe UI", 10))

    def _load_layout(self, layout_name: str):
        if layout_name == "Sidebar":
            from ui.layout_sidebar import SidebarLayout
            self._layout_widget = SidebarLayout(self)
        else:
            from ui.layout_tabbed import TabbedLayout
            self._layout_widget = TabbedLayout(self)
        self.setCentralWidget(self._layout_widget)

    def _build_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        layout_label = "📌 Sidebar" if self._layout_name == "Sidebar" else "📌 Tabbed"
        self.status.showMessage(f"Ready  ·  {layout_label}")

    # ── Resize from edges (frameless windows lose native resize handles) ───────
    def mousePressEvent(self, event):
        """Store position for edge-resize tracking."""
        self._resize_edge = self._get_edge(event.pos())
        if self._resize_edge:
            self._resize_start_global = event.globalPos()
            self._resize_start_geom   = self.geometry()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        edge = self._get_edge(event.pos())
        cursors = {
            "bottom":       Qt.SizeVerCursor,
            "right":        Qt.SizeHorCursor,
            "bottom-right": Qt.SizeFDiagCursor,
        }
        self.setCursor(cursors.get(edge, Qt.ArrowCursor))

        if hasattr(self, "_resize_edge") and self._resize_edge:
            delta = event.globalPos() - self._resize_start_global
            g = self._resize_start_geom
            if "right"  in self._resize_edge:
                self.resize(max(800, g.width()  + delta.x()), self.height())
            if "bottom" in self._resize_edge:
                self.resize(self.width(), max(500, g.height() + delta.y()))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._resize_edge = None
        super().mouseReleaseEvent(event)

    def _get_edge(self, pos, margin=6):
        r, b = self.width(), self.height()
        on_right  = pos.x() >= r - margin
        on_bottom = pos.y() >= b - margin
        if on_right and on_bottom: return "bottom-right"
        if on_bottom:               return "bottom"
        if on_right:                return "right"
        return None

    # ── App close — kill LibreTranslate subprocess ────────────────────────────
    def closeEvent(self, event):
        """Terminate LibreTranslate (if running) before the app exits."""
        try:
            from ui.tab_settings import _lt_process
            if _lt_process is not None and _lt_process.poll() is None:
                _lt_process.terminate()
        except Exception:
            pass
        event.accept()

    # ── Public API used by layout widgets ─────────────────────────────────────
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
        """Called by SettingsTab when user picks a different layout."""
        if new_layout == self._layout_name:
            return
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Restart required",
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
            self,
            "About Local Helper",
            "<b>Local Helper</b><br>"
            "A private AI assistant powered by your own proxy.<br><br>"
            "Features: Multi-agent chat, GitHub integration, "
            "web search, markdown rendering, code save &amp; commit.<br><br>"
            "<i>Built with PyQt5 + requests</i>"
        )
