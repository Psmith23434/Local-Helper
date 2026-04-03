"""Sidebar layout — left icon-rail navigation, VS Code / Discord style."""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QPushButton, QLabel, QAction, QApplication, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QFont
from ui.theme import get as T
from ui.styles import global_qss
from ui.tab_general  import GeneralChatTab
from ui.tab_agents   import AgentsTab
from ui.tab_discover import DiscoverTab
from ui.tab_tips     import TipsTab
from ui.tab_settings import SettingsTab


NAV_ITEMS = [
    ("💬", "General Chat"),
    ("🤖", "Agents"),
    ("🔭", "Discover"),
    ("💡", "Tips"),
    ("⚙️", "Settings"),
]


class NavButton(QPushButton):
    """Single sidebar nav button with icon + optional label."""

    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(parent)
        self._icon  = icon
        self._label = label
        self._expanded = False
        self._active   = False
        self._refresh()
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(52)

    def set_expanded(self, expanded: bool):
        self._expanded = expanded
        self._refresh()

    def set_active(self, active: bool):
        self._active = active
        self.setChecked(active)
        self._refresh()

    def _refresh(self):
        d = T()
        if self._expanded:
            self.setText(f"  {self._icon}  {self._label}")
            self.setFixedWidth(200)
            self.setStyleSheet(
                f"QPushButton{{"
                f"background:{''+d['accent_dim'] if self._active else d['surface2']};"
                f"color:{'#fff' if self._active else d['text']};"
                f"border:none;border-radius:8px;"
                f"font-size:13px;font-weight:{'700' if self._active else '400'};"
                f"text-align:left;padding:0 14px;"
                f"}}"
                f"QPushButton:hover{{background:{d['accent_dim']};color:#fff;}}"
            )
        else:
            self.setText(self._icon)
            self.setFixedWidth(60)
            self.setStyleSheet(
                f"QPushButton{{"
                f"background:{''+d['accent_dim'] if self._active else 'transparent'};"
                f"color:{'#fff' if self._active else d['muted']};"
                f"border:none;border-radius:8px;"
                f"font-size:20px;font-weight:400;"
                f"text-align:center;padding:0;"
                f"}}"
                f"QPushButton:hover{{background:{d['surface2']};color:{d['text']};}}"
            )


class Sidebar(QWidget):
    """Collapsible left rail. Collapsed = 60px icons only. Expanded = 200px with labels."""
    page_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._expanded = False
        self._buttons: list[NavButton] = []
        self._build_ui()
        self._select(0)

    def _build_ui(self):
        d = T()
        self.setFixedWidth(60)
        self.setStyleSheet(f"background:{d['surface']};border-right:1px solid {d['border']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 10, 6, 10)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignTop)

        # Toggle expand button at top
        self.btn_toggle = QPushButton("☰")
        self.btn_toggle.setFixedSize(48, 36)
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.setToolTip("Expand / collapse sidebar")
        self.btn_toggle.setStyleSheet(
            f"QPushButton{{background:transparent;color:{d['muted']};border:none;"
            f"font-size:16px;border-radius:6px;}}"
            f"QPushButton:hover{{background:{d['surface2']};color:{d['text']};}}"
        )
        self.btn_toggle.clicked.connect(self._toggle_expand)
        layout.addWidget(self.btn_toggle)

        # Divider
        div = QWidget()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background:{d['border']};")
        layout.addWidget(div)
        layout.addSpacing(4)

        # Nav buttons
        for i, (icon, label) in enumerate(NAV_ITEMS):
            btn = NavButton(icon, label)
            btn.clicked.connect(lambda checked, idx=i: self._select(idx))
            self._buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

    def _select(self, index: int):
        for i, btn in enumerate(self._buttons):
            btn.set_active(i == index)
        self.page_changed.emit(index)

    def _toggle_expand(self):
        self._expanded = not self._expanded
        new_width = 212 if self._expanded else 60
        self.setFixedWidth(new_width)
        for btn in self._buttons:
            btn.set_expanded(self._expanded)
        self.btn_toggle.setText("✕" if self._expanded else "☰")

    def navigate(self, index: int):
        self._select(index)


class SidebarLayout(QWidget):
    """Drop-in content widget for MainWindow — sidebar nav style."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self._mw = main_window
        self._build_menu()
        self._build_ui()

    # ── Menu bar ──────────────────────────────────────────────────
    def _build_menu(self):
        mb = self._mw.menuBar()
        mb.clear()

        file_menu = mb.addMenu("File")
        act_new_chat = QAction("New Chat", self._mw)
        act_new_chat.setShortcut("Ctrl+N")
        act_new_chat.triggered.connect(lambda: self.navigate(0))
        file_menu.addAction(act_new_chat)
        act_new_agent = QAction("New Agent", self._mw)
        act_new_agent.triggered.connect(lambda: self.navigate(1))
        file_menu.addAction(act_new_agent)
        file_menu.addSeparator()
        act_quit = QAction("Quit", self._mw)
        act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(QApplication.instance().quit)
        file_menu.addAction(act_quit)

        view_menu = mb.addMenu("View")
        for i, (_, label) in enumerate(NAV_ITEMS):
            a = QAction(label, self._mw)
            a.triggered.connect(lambda checked, x=i: self.navigate(x))
            view_menu.addAction(a)
        view_menu.addSeparator()
        for theme_name in ["Dark", "VS Code", "Fire"]:
            a = QAction(f"Theme: {theme_name}", self._mw)
            a.triggered.connect(lambda checked, t=theme_name: self._mw.switch_theme(t))
            view_menu.addAction(a)

        help_menu = mb.addMenu("Help")
        act_tips = QAction("Tips & Examples", self._mw)
        act_tips.triggered.connect(lambda: self.navigate(3))
        help_menu.addAction(act_tips)
        act_disc = QAction("Discover Features", self._mw)
        act_disc.triggered.connect(lambda: self.navigate(2))
        help_menu.addAction(act_disc)
        help_menu.addSeparator()
        act_about = QAction("About Local Helper", self._mw)
        act_about.triggered.connect(self._mw.show_about)
        help_menu.addAction(act_about)

    # ── UI ──────────────────────────────────────────────────────
    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar rail
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._on_page_changed)
        root.addWidget(self.sidebar)

        # Stacked pages
        self.stack = QStackedWidget()

        self.tab_general  = GeneralChatTab()
        self.tab_agents   = AgentsTab()
        self.tab_discover = DiscoverTab()
        self.tab_tips     = TipsTab()
        self.tab_settings = SettingsTab()

        self.stack.addWidget(self.tab_general)
        self.stack.addWidget(self.tab_agents)
        self.stack.addWidget(self.tab_discover)
        self.stack.addWidget(self.tab_tips)
        self.stack.addWidget(self.tab_settings)

        self.tab_settings.theme_changed.connect(self._mw.reapply_theme)
        self.tab_settings.layout_changed.connect(self._mw.on_layout_change_requested)

        root.addWidget(self.stack)

    def _on_page_changed(self, index: int):
        self.stack.setCurrentIndex(index)

    def navigate(self, index: int):
        self.sidebar.navigate(index)
        self.stack.setCurrentIndex(index)
