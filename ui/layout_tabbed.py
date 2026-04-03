"""Tabbed layout — top QTabWidget navigation (original style)."""

from PyQt5.QtWidgets import (
    QWidget, QTabWidget, QStatusBar,
    QMenuBar, QAction, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.theme import get as T, set_theme
from ui.styles import global_qss
from ui.tab_general  import GeneralChatTab
from ui.tab_agents   import AgentsTab
from ui.tab_discover import DiscoverTab
from ui.tab_tips     import TipsTab
from ui.tab_settings import SettingsTab


class TabbedLayout(QWidget):
    """Drop-in content widget for MainWindow — top tab bar style."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self._mw = main_window   # reference to MainWindow for status bar access
        self._build_menu()
        self._build_ui()

    # ── Menu bar ─────────────────────────────────────────────────────
    def _build_menu(self):
        mb = self._mw.menuBar()
        mb.clear()
        d = T()

        file_menu = mb.addMenu("File")
        act_new_chat = QAction("New Chat", self._mw)
        act_new_chat.setShortcut("Ctrl+N")
        act_new_chat.triggered.connect(lambda: self._tabs.setCurrentIndex(0))
        file_menu.addAction(act_new_chat)
        act_new_agent = QAction("New Agent", self._mw)
        act_new_agent.triggered.connect(lambda: self._tabs.setCurrentIndex(1))
        file_menu.addAction(act_new_agent)
        file_menu.addSeparator()
        act_quit = QAction("Quit", self._mw)
        act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(QApplication.instance().quit)
        file_menu.addAction(act_quit)

        view_menu = mb.addMenu("View")
        for i, label in enumerate(["General Chat", "Agents", "Discover", "Tips", "Settings"]):
            a = QAction(label, self._mw)
            a.triggered.connect(lambda checked, x=i: self._tabs.setCurrentIndex(x))
            view_menu.addAction(a)
        view_menu.addSeparator()
        for theme_name in ["Dark", "VS Code", "Fire"]:
            a = QAction(f"Theme: {theme_name}", self._mw)
            a.triggered.connect(lambda checked, t=theme_name: self._mw.switch_theme(t))
            view_menu.addAction(a)

        help_menu = mb.addMenu("Help")
        act_tips = QAction("Tips & Examples", self._mw)
        act_tips.triggered.connect(lambda: self._tabs.setCurrentIndex(3))
        help_menu.addAction(act_tips)
        act_disc = QAction("Discover Features", self._mw)
        act_disc.triggered.connect(lambda: self._tabs.setCurrentIndex(2))
        help_menu.addAction(act_disc)
        help_menu.addSeparator()
        act_about = QAction("About Local Helper", self._mw)
        act_about.triggered.connect(self._mw.show_about)
        help_menu.addAction(act_about)

    # ── Tabs ───────────────────────────────────────────────────────
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
        self.tab_settings = SettingsTab()

        self._tabs.addTab(self.tab_general,  "💬  General Chat")
        self._tabs.addTab(self.tab_agents,   "🤖  Agents")
        self._tabs.addTab(self.tab_discover, "🔭  Discover")
        self._tabs.addTab(self.tab_tips,     "💡  Tips")
        self._tabs.addTab(self.tab_settings, "⚙️  Settings")

        self.tab_settings.theme_changed.connect(self._mw.reapply_theme)
        self.tab_settings.layout_changed.connect(self._mw.on_layout_change_requested)

        root.addWidget(self._tabs)

    def navigate(self, index: int):
        self._tabs.setCurrentIndex(index)
