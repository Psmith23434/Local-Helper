"""Agents tab — browser-style agent panel with per-agent thread lists."""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QMenu, QInputDialog, QMessageBox,
    QSplitter, QDialog, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import database as db
from ui.chat_widget import ChatWidget
from ui.space_dialog import SpaceDialog
from ui.theme import get as T
from ui.styles import accent_btn_qss


class AgentsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_agent_id  = None
        self.current_thread_id = None
        self._build_ui()
        self._load_agents()

    def _build_ui(self):
        d = T()
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        # ── Left panel: agent list ────────────────────────────────────────────
        left = QWidget()
        left.setStyleSheet(f"background:{d['surface']};border-right:1px solid {d['border']};")
        left.setMinimumWidth(170)
        left.setMaximumWidth(230)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(8, 10, 8, 10)
        ll.setSpacing(6)

        title_row = QHBoxLayout()
        lbl = QLabel("AGENTS")
        lbl.setStyleSheet(f"color:{d['muted']};font-size:10px;font-weight:700;letter-spacing:1px;")
        title_row.addWidget(lbl)
        title_row.addStretch()
        self.btn_new_agent = QPushButton("+ New")
        self.btn_new_agent.setFixedHeight(22)
        self.btn_new_agent.setCursor(Qt.PointingHandCursor)
        self.btn_new_agent.clicked.connect(self._new_agent)
        title_row.addWidget(self.btn_new_agent)
        ll.addLayout(title_row)

        self.agent_list = QListWidget()
        self.agent_list.setCursor(Qt.PointingHandCursor)
        self.agent_list.itemClicked.connect(self._on_agent_click)
        self.agent_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.agent_list.customContextMenuRequested.connect(self._agent_ctx_menu)
        ll.addWidget(self.agent_list)
        splitter.addWidget(left)

        # ── Middle panel: thread list ─────────────────────────────────────────
        mid = QWidget()
        mid.setStyleSheet(f"background:{d['surface']};border-right:1px solid {d['border']};")
        mid.setMinimumWidth(170)
        mid.setMaximumWidth(230)
        ml = QVBoxLayout(mid)
        ml.setContentsMargins(8, 10, 8, 10)
        ml.setSpacing(6)

        thread_row = QHBoxLayout()
        self.threads_label = QLabel("THREADS")
        self.threads_label.setStyleSheet(f"color:{d['muted']};font-size:10px;font-weight:700;letter-spacing:1px;")
        thread_row.addWidget(self.threads_label)
        thread_row.addStretch()
        self.btn_new_thread = QPushButton("+ New")
        self.btn_new_thread.setFixedHeight(22)
        self.btn_new_thread.setCursor(Qt.PointingHandCursor)
        self.btn_new_thread.clicked.connect(self._new_thread)
        thread_row.addWidget(self.btn_new_thread)
        ml.addLayout(thread_row)

        self.thread_list = QListWidget()
        self.thread_list.setCursor(Qt.PointingHandCursor)
        self.thread_list.itemClicked.connect(self._on_thread_click)
        self.thread_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.thread_list.customContextMenuRequested.connect(self._thread_ctx_menu)
        ml.addWidget(self.thread_list)
        splitter.addWidget(mid)

        # ── Right panel: chat ─────────────────────────────────────────────────
        self.chat = ChatWidget(
            space_id=None,
            system_prompt="You are a helpful assistant.",
            web_search_default=False,
            on_thread_renamed=self._on_renamed,
        )
        self.placeholder = QLabel("Select or create an Agent to start chatting.")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet(f"color:{d['muted']};font-size:14px;")

        self.right_stack = QWidget()
        rs_layout = QVBoxLayout(self.right_stack)
        rs_layout.setContentsMargins(0,0,0,0)
        rs_layout.addWidget(self.placeholder)
        rs_layout.addWidget(self.chat)
        self.chat.hide()

        splitter.addWidget(self.right_stack)
        splitter.setSizes([200, 200, 800])
        root.addWidget(splitter)

    # ── Agents ────────────────────────────────────────────────────────────────
    def _excluded_names(self):
        return {"General Chat", "Quick Chat", "🧑\u200d💻  Coding Assistant", "💬  General Chat"}

    def _load_agents(self):
        self.agent_list.clear()
        for s in db.get_spaces():
            if s["name"] in self._excluded_names(): continue
            item = QListWidgetItem("🤖  " + s["name"])
            item.setData(Qt.UserRole, s["id"])
            self.agent_list.addItem(item)
        if self.agent_list.count() > 0:
            first = self.agent_list.item(0)
            self.agent_list.setCurrentItem(first)
            self._on_agent_click(first)

    def _on_agent_click(self, item):
        self.current_agent_id = item.data(Qt.UserRole)
        space = db.get_space(self.current_agent_id)
        self.chat.space_id = self.current_agent_id
        self.chat.set_system_prompt(
            space.get("instructions") or "You are a helpful assistant."
        )
        self._load_threads()

    def _new_agent(self):
        d = T()
        dlg = SpaceDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            db.create_space(**data)
            self._load_agents()

    def _agent_ctx_menu(self, pos):
        item = self.agent_list.itemAt(pos)
        if not item: return
        d = T()
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu{{background:{d['surface2']};border:1px solid {d['border']};border-radius:6px;padding:4px;}}"
            f"QMenu::item{{padding:6px 16px;border-radius:4px;}}"
            f"QMenu::item:selected{{background:{d['accent']};color:#fff;}}"
        )
        edit   = menu.addAction("✎  Edit")
        delete = menu.addAction("✕  Delete")
        action = menu.exec_(self.agent_list.mapToGlobal(pos))
        aid = item.data(Qt.UserRole)
        if action == edit:
            dlg = SpaceDialog(self, db.get_space(aid))
            if dlg.exec_() == QDialog.Accepted:
                data = dlg.get_data()
                db.update_space(aid, **data)
                item.setText("🤖  " + data["name"])
        elif action == delete:
            if QMessageBox.question(self, "Delete Agent", "Delete this agent and all threads?") == QMessageBox.Yes:
                db.delete_space(aid)
                self._load_agents()
                self.thread_list.clear()
                self.chat.hide()
                self.placeholder.show()

    # ── Threads ───────────────────────────────────────────────────────────────
    def _load_threads(self):
        self.thread_list.clear()
        if not self.current_agent_id: return
        threads = db.get_threads(self.current_agent_id)
        for t in threads:
            item = QListWidgetItem("💬  " + t["title"])
            item.setData(Qt.UserRole, t["id"])
            self.thread_list.addItem(item)
        if threads:
            first = self.thread_list.item(0)
            self.thread_list.setCurrentItem(first)
            self._open_thread(first.data(Qt.UserRole))
        else:
            self._new_thread()

    def _new_thread(self):
        if not self.current_agent_id: return
        tid = db.create_thread(self.current_agent_id)
        self._load_threads()
        self._select_thread(tid)
        self._open_thread(tid)

    def _open_thread(self, tid: int):
        space = db.get_space(self.current_agent_id) if self.current_agent_id else None
        label = space["name"] if space else "Agent"
        self.placeholder.hide()
        self.chat.show()
        self.chat.load_thread(tid, f"🤖 {label}")

    def _select_thread(self, tid: int):
        for i in range(self.thread_list.count()):
            item = self.thread_list.item(i)
            if item.data(Qt.UserRole) == tid:
                self.thread_list.setCurrentItem(item)
                break

    def _on_thread_click(self, item):
        self._open_thread(item.data(Qt.UserRole))

    def _on_renamed(self, tid: int, title: str):
        for i in range(self.thread_list.count()):
            item = self.thread_list.item(i)
            if item.data(Qt.UserRole) == tid:
                item.setText("💬  " + title)
                break

    def _thread_ctx_menu(self, pos):
        item = self.thread_list.itemAt(pos)
        if not item: return
        d = T()
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu{{background:{d['surface2']};border:1px solid {d['border']};border-radius:6px;padding:4px;}}"
            f"QMenu::item{{padding:6px 16px;border-radius:4px;}}"
            f"QMenu::item:selected{{background:{d['accent']};color:#fff;}}"
        )
        r  = menu.addAction("✎  Rename")
        dl = menu.addAction("✕  Delete")
        action = menu.exec_(self.thread_list.mapToGlobal(pos))
        tid = item.data(Qt.UserRole)
        if action == r:
            title, ok = QInputDialog.getText(self, "Rename", "Title:", text=item.text().replace("💬  ",""))
            if ok and title.strip():
                db.rename_thread(tid, title.strip())
                item.setText("💬  " + title.strip())
        elif action == dl:
            if QMessageBox.question(self, "Delete", "Delete this thread?") == QMessageBox.Yes:
                db.delete_thread(tid)
                self._load_threads()
