"""Main application window — tabbed layout with menu bar."""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QStatusBar,
    QMenuBar, QAction, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QFont
from ui.theme import get as T, set_theme
from ui.styles import global_qss
from ui.tab_general  import GeneralChatTab
from ui.tab_agents   import AgentsTab
from ui.tab_discover import DiscoverTab
from ui.tab_tips     import TipsTab
from ui.tab_settings import SettingsTab


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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Local Helper")
        self.resize(1320, 860)
        self._apply_style()
        self._build_menu()
        self._build_ui()

    def _apply_style(self):
        apply_dark_palette(self)
        self.setStyleSheet(global_qss())
        self.setFont(QFont("Segoe UI", 10))

    # ── Menu bar ──────────────────────────────────────────────────────────────
    def _build_menu(self):
        mb = self.menuBar()

        # File
        file_menu = mb.addMenu("File")
        act_new_chat = QAction("New Chat", self)
        act_new_chat.setShortcut("Ctrl+N")
        act_new_chat.triggered.connect(lambda: self._tabs.setCurrentIndex(0))
        file_menu.addAction(act_new_chat)

        act_new_agent = QAction("New Agent", self)
        act_new_agent.triggered.connect(lambda: self._tabs.setCurrentIndex(1))
        file_menu.addAction(act_new_agent)
        file_menu.addSeparator()

        act_quit = QAction("Quit", self)
        act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(QApplication.instance().quit)
        file_menu.addAction(act_quit)

        # View
        view_menu = mb.addMenu("View")
        for i, label in enumerate(["General Chat", "Agents", "Discover", "Tips", "Settings"]):
            a = QAction(label, self)
            idx = i
            a.triggered.connect(lambda checked, x=idx: self._tabs.setCurrentIndex(x))
            view_menu.addAction(a)
        view_menu.addSeparator()

        act_dark = QAction("Theme: Dark", self)
        act_dark.triggered.connect(lambda: self._switch_theme("Dark"))
        view_menu.addAction(act_dark)

        act_vsc = QAction("Theme: VS Code", self)
        act_vsc.triggered.connect(lambda: self._switch_theme("VS Code"))
        view_menu.addAction(act_vsc)

        # Help
        help_menu = mb.addMenu("Help")
        act_tips = QAction("Tips & Examples", self)
        act_tips.triggered.connect(lambda: self._tabs.setCurrentIndex(3))
        help_menu.addAction(act_tips)

        act_discover = QAction("Discover Features", self)
        act_discover.triggered.connect(lambda: self._tabs.setCurrentIndex(2))
        help_menu.addAction(act_discover)
        help_menu.addSeparator()

        act_about = QAction("About Local Helper", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self.setCentralWidget(self._tabs)

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

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

        # Wire up theme change from settings tab
        self.tab_settings.theme_changed.connect(self._reapply_theme)

    def set_status(self, msg: str):
        self.status.showMessage(msg)

    def _switch_theme(self, name: str):
        set_theme(name)
        self._reapply_theme()

    def _reapply_theme(self):
        self._apply_style()
        # Rebuild tabs to pick up new theme colors
        # Simple approach: just re-apply QSS; widgets with hardcoded colors need rebuild
        self.setStyleSheet(global_qss())
        apply_dark_palette(self)

    def _show_about(self):
        QMessageBox.about(
            self,
            "About Local Helper",
            "<b>Local Helper</b><br>"
            "A private AI assistant powered by your own proxy.<br><br>"
            "Features: Multi-agent chat, GitHub integration, "
            "web search, markdown rendering, code save &amp; commit.<br><br>"
            "<i>Built with PyQt5 + requests</i>"
        )
