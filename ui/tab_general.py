"""General Chat tab — quick chats with thread history."""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QMenu, QInputDialog, QMessageBox, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal
import database as db
from ui.chat_widget import ChatWidget
from ui.theme import get as T
from ui.styles import accent_btn_qss

GENERAL_SPACE_NAME = "General Chat"


class GeneralChatTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.space_id = self._get_or_create_space()
        self._build_ui()
        self._load_threads()

    def _get_or_create_space(self) -> int:
        for s in db.get_spaces():
            if s["name"] == GENERAL_SPACE_NAME:
                return s["id"]
        return db.create_space(
            name=GENERAL_SPACE_NAME,
            instructions="You are a helpful, concise assistant.",
            model="", github_repo="", web_search=False,
        )

    def _build_ui(self):
        d = T()
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        # Left: thread list
        left = QWidget()
        left.setStyleSheet(f"background:{d['surface']};border-right:1px solid {d['border']};")
        left.setMinimumWidth(180)
        left.setMaximumWidth(260)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(8, 10, 8, 10)
        ll.setSpacing(6)

        self.btn_new = QPushButton("+ New Chat")
        self.btn_new.setStyleSheet(accent_btn_qss())
        self.btn_new.setFixedHeight(34)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.clicked.connect(self._new_thread)
        ll.addWidget(self.btn_new)

        lbl = QLabel("CHATS")
        lbl.setStyleSheet(f"color:{d['muted']};font-size:10px;font-weight:700;letter-spacing:1px;padding:4px 2px 0;")
        ll.addWidget(lbl)

        self.thread_list = QListWidget()
        self.thread_list.setCursor(Qt.PointingHandCursor)
        self.thread_list.itemClicked.connect(self._on_thread_click)
        self.thread_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.thread_list.customContextMenuRequested.connect(self._ctx_menu)
        ll.addWidget(self.thread_list)
        splitter.addWidget(left)

        # Right: chat widget
        self.chat = ChatWidget(
            space_id=self.space_id,
            system_prompt="You are a helpful, concise assistant.",
            web_search_default=False,
            on_thread_renamed=self._on_renamed,
        )
        splitter.addWidget(self.chat)
        splitter.setSizes([220, 900])
        root.addWidget(splitter)

    def _load_threads(self):
        self.thread_list.clear()
        threads = db.get_threads(self.space_id)
        for t in threads:
            item = QListWidgetItem("💬  " + t["title"])
            item.setData(Qt.UserRole, t["id"])
            self.thread_list.addItem(item)
        # Auto-select first
        if self.thread_list.count() > 0:
            first = self.thread_list.item(0)
            self.thread_list.setCurrentItem(first)
            self.chat.load_thread(first.data(Qt.UserRole), "General Chat")
        else:
            self._new_thread()

    def _new_thread(self):
        tid = db.create_thread(self.space_id)
        self._load_threads()
        self._select_thread(tid)
        self.chat.load_thread(tid, "General Chat")

    def _select_thread(self, tid: int):
        for i in range(self.thread_list.count()):
            item = self.thread_list.item(i)
            if item.data(Qt.UserRole) == tid:
                self.thread_list.setCurrentItem(item)
                break

    def _on_thread_click(self, item):
        tid = item.data(Qt.UserRole)
        self.chat.load_thread(tid, "General Chat")

    def _on_renamed(self, tid: int, title: str):
        for i in range(self.thread_list.count()):
            item = self.thread_list.item(i)
            if item.data(Qt.UserRole) == tid:
                item.setText("💬  " + title)
                break

    def _ctx_menu(self, pos):
        item = self.thread_list.itemAt(pos)
        if not item: return
        d = T()
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu{{background:{d['surface2']};border:1px solid {d['border']};border-radius:6px;padding:4px;}}"
            f"QMenu::item{{padding:6px 16px;border-radius:4px;}}"
            f"QMenu::item:selected{{background:{d['accent']};color:#fff;}}"
        )
        r = menu.addAction("✎  Rename")
        dl = menu.addAction("✕  Delete")
        action = menu.exec_(self.thread_list.mapToGlobal(pos))
        tid = item.data(Qt.UserRole)
        if action == r:
            title, ok = QInputDialog.getText(self, "Rename", "Title:", text=item.text().replace("💬  ",""))
            if ok and title.strip():
                db.rename_thread(tid, title.strip())
                item.setText("💬  " + title.strip())
        elif action == dl:
            if QMessageBox.question(self, "Delete", "Delete this chat?") == QMessageBox.Yes:
                db.delete_thread(tid)
                self._load_threads()
