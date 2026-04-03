"""Main application window — thin shell that loads a layout class."""

from PyQt5.QtWidgets import QMainWindow, QStatusBar, QMessageBox, QApplication
from PyQt5.QtCore import Qt
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


class MainWindow(QMainWindow):
    def __init__(self, layout: str = "Tabbed"):
        super().__init__()
        self.setWindowTitle("Local Helper")
        self.resize(1320, 860)
        self._layout_name = layout
        self._apply_style()
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

    # ── Public API used by layout widgets ─────────────────────────────
    def set_status(self, msg: str):
        self.status.showMessage(msg)

    def switch_theme(self, name: str):
        set_theme(name)
        self.reapply_theme()

    def reapply_theme(self):
        self._apply_style()
        self.setStyleSheet(global_qss())
        apply_dark_palette(self)

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
            # Save to config.py
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
