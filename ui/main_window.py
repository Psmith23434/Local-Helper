"""Main application window."""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QAction, QMenuBar, QStatusBar
)
from PyQt5.QtCore import Qt
from ui.sidebar import Sidebar
from ui.chat_panel import ChatPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Local Helper")
        self.resize(1200, 800)

        # Central layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Splitter: sidebar | chat
        splitter = QSplitter(Qt.Horizontal)
        self.sidebar = Sidebar(self)
        self.chat_panel = ChatPanel(self)

        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.chat_panel)
        splitter.setSizes([260, 940])
        splitter.setHandleWidth(1)

        layout.addWidget(splitter)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

        # Wire up: selecting a thread loads it in chat panel
        self.sidebar.thread_selected.connect(self.chat_panel.load_thread)
        self.sidebar.space_changed.connect(self.chat_panel.set_space)

    def set_status(self, msg: str):
        self.status.showMessage(msg)
