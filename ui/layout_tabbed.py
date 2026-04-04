"""Tabbed layout — top QTabWidget navigation."""

from PyQt5.QtWidgets import (
    QWidget, QTabWidget, QAction, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.theme import get as T
from ui.tab_general  import GeneralChatTab
from ui.tab_agents   import AgentsTab
from ui.tab_discover import DiscoverTab
from ui.tab_tips     import TipsTab
from ui.tab_settings import SettingsTab
from ui.tab_ocr      import OCRTab


class TabbedLayout(QWidget):
    """Drop-in content widget for MainWindow — top tab bar style."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self._mw = main_window
        self._build_ui()
        self._build_menu()   # after tabs exist so actions can reference them
        self._wire_ocr()

    # ── Tabs ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        from PyQt5.QtWidgets import QVBoxLayout
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)

        self.tab_general  = GeneralChatTab()
        self.tab_agents   = AgentsTab()
        self.tab_discover = DiscoverTab()
        self.tab_tips     = TipsTab()
        self.tab_ocr      = OCRTab()
        self.tab_settings = SettingsTab()

        self._tabs.addTab(self.tab_general,  "💬  General Chat")
        self._tabs.addTab(self.tab_agents,   "🤖  Agents")
        self._tabs.addTab(self.tab_discover, "🔭  Discover")
        self._tabs.addTab(self.tab_tips,     "💡  Tips")
        self._tabs.addTab(self.tab_ocr,      "🔍  OCR")
        self._tabs.addTab(self.tab_settings, "⚙️  Settings")

        self.tab_settings.theme_changed.connect(self._mw.reapply_theme)
        self.tab_settings.layout_changed.connect(self._mw.on_layout_change_requested)

        root.addWidget(self._tabs)

    # ── Menu bar — populated into the TitleBar’s embedded QMenuBar ────────────
    def _build_menu(self):
        mb = self._mw._title_bar.menu_bar()
        mb.clear()

        # File
        file_menu = mb.addMenu("File")
        a = QAction("New Chat", self._mw)
        a.setShortcut("Ctrl+N")
        a.triggered.connect(lambda: self._tabs.setCurrentIndex(0))
        file_menu.addAction(a)
        a = QAction("New Agent", self._mw)
        a.triggered.connect(lambda: self._tabs.setCurrentIndex(1))
        file_menu.addAction(a)
        file_menu.addSeparator()
        a = QAction("Quit", self._mw)
        a.setShortcut("Ctrl+Q")
        a.triggered.connect(QApplication.instance().quit)
        file_menu.addAction(a)

        # View
        view_menu = mb.addMenu("View")
        for i, label in enumerate(["General Chat", "Agents", "Discover",
                                    "Tips", "OCR", "Settings"]):
            a = QAction(label, self._mw)
            a.triggered.connect(lambda checked, x=i: self._tabs.setCurrentIndex(x))
            view_menu.addAction(a)
        view_menu.addSeparator()
        for theme_name in ["Dark", "VS Code", "Fire"]:
            a = QAction(f"Theme: {theme_name}", self._mw)
            a.triggered.connect(lambda checked, t=theme_name: self._mw.switch_theme(t))
            view_menu.addAction(a)

        # Help
        help_menu = mb.addMenu("Help")
        a = QAction("Tips & Examples", self._mw)
        a.triggered.connect(lambda: self._tabs.setCurrentIndex(3))
        help_menu.addAction(a)
        a = QAction("Discover Features", self._mw)
        a.triggered.connect(lambda: self._tabs.setCurrentIndex(2))
        help_menu.addAction(a)
        help_menu.addSeparator()
        a = QAction("About Local Helper", self._mw)
        a.triggered.connect(self._mw.show_about)
        help_menu.addAction(a)

    # ── OCR wiring ────────────────────────────────────────────────────────────
    def _wire_ocr(self):
        try:
            chat_panel = self.tab_general.chat_panel
            self.tab_ocr.ocr_widget.text_ready.connect(chat_panel.insert_ocr_text)
            self.tab_ocr.ocr_widget.text_ready.connect(
                lambda _: self._tabs.setCurrentIndex(0)
            )
        except Exception:
            pass

    def navigate(self, index: int):
        self._tabs.setCurrentIndex(index)
