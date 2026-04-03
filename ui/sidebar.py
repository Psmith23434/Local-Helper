"""Left sidebar — dark premium redesign."""

import json
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QLabel, QMenu, QInputDialog, QMessageBox,
    QComboBox, QDialog, QFrame
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor
import database as db
from config import TEMPLATES_DIR
from ui.space_dialog import SpaceDialog

QUICK_CHAT_SPACE_NAME = "Quick Chat"

D = {
    "bg":         "#0d0d0d",
    "surface":    "#141414",
    "surface2":   "#1a1a1a",
    "border":     "#2a2a2a",
    "accent":     "#7c6af7",
    "accent_dim": "#5a4fd1",
    "text":       "#e8e8e8",
    "muted":      "#666666",
    "hover":      "#222222",
    "selected":   "#1e1b3a",
}

SIDEBAR_QSS = f"""
QWidget#Sidebar {{
    background: {D['surface']};
    border-right: 1px solid {D['border']};
}}

/* New Chat button */
QPushButton#btnQuickChat {{
    background: {D['accent']};
    color: #ffffff;
    font-weight: 700;
    font-size: 13px;
    border: none;
    border-radius: 8px;
    padding: 10px 0;
}}
QPushButton#btnQuickChat:hover {{
    background: {D['accent_dim']};
}}
QPushButton#btnQuickChat:pressed {{
    background: #4a3faa;
}}

/* Space combo */
QComboBox {{
    background: {D['surface2']};
    border: 1px solid {D['border']};
    border-radius: 6px;
    padding: 5px 8px;
    color: {D['text']};
    font-size: 12px;
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background: {D['surface2']};
    border: 1px solid {D['border']};
    selection-background-color: {D['accent']};
    color: {D['text']};
}}

/* Section labels */
QLabel#sectionLabel {{
    color: {D['muted']};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 0 4px;
}}

/* Small icon buttons */
QPushButton#iconBtn {{
    background: transparent;
    color: {D['muted']};
    border: 1px solid {D['border']};
    border-radius: 5px;
    font-size: 11px;
    padding: 3px 7px;
}}
QPushButton#iconBtn:hover {{
    background: {D['hover']};
    color: {D['text']};
    border-color: #444;
}}

/* Thread list */
QListWidget {{
    background: transparent;
    border: none;
    outline: none;
}}
QListWidget::item {{
    background: transparent;
    color: {D['text']};
    padding: 8px 10px;
    border-radius: 6px;
    margin: 1px 4px;
    font-size: 12px;
}}
QListWidget::item:hover {{
    background: {D['hover']};
}}
QListWidget::item:selected {{
    background: {D['selected']};
    color: #c4baff;
}}

/* Divider */
QFrame#divider {{
    background: {D['border']};
    max-height: 1px;
    border: none;
}}
"""


class Sidebar(QWidget):
    thread_selected = pyqtSignal(int)
    space_changed   = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setMinimumWidth(200)
        self.setMaximumWidth(300)
        self.current_space_id = None
        self.setStyleSheet(SIDEBAR_QSS)
        self._build_ui()
        self._load_spaces()

    def _mk_icon_btn(self, text, tooltip=""):
        b = QPushButton(text)
        b.setObjectName("iconBtn")
        b.setFixedHeight(24)
        if tooltip:
            b.setToolTip(tooltip)
        return b

    def _mk_label(self, text):
        l = QLabel(text.upper())
        l.setObjectName("sectionLabel")
        return l

    def _divider(self):
        f = QFrame()
        f.setObjectName("divider")
        f.setFrameShape(QFrame.HLine)
        return f

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 12, 10, 12)
        layout.setSpacing(6)

        # App title
        title = QLabel("Local Helper")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet(f"color: {D['text']}; padding: 0 2px 4px 2px;")
        layout.addWidget(title)

        # New Chat button
        self.btn_quick_chat = QPushButton("+ New Chat")
        self.btn_quick_chat.setObjectName("btnQuickChat")
        self.btn_quick_chat.setFixedHeight(38)
        self.btn_quick_chat.setCursor(Qt.PointingHandCursor)
        self.btn_quick_chat.clicked.connect(self._quick_chat)
        layout.addWidget(self.btn_quick_chat)

        layout.addWidget(self._divider())

        # Space section
        space_hdr = QHBoxLayout()
        space_hdr.addWidget(self._mk_label("Space"))
        space_hdr.addStretch()
        self.btn_new_space = self._mk_icon_btn("+ New", "Create new space")
        self.btn_edit_space = self._mk_icon_btn("✎", "Edit space")
        self.btn_del_space  = self._mk_icon_btn("✕", "Delete space")
        for b in [self.btn_new_space, self.btn_edit_space, self.btn_del_space]:
            space_hdr.addWidget(b)
        layout.addLayout(space_hdr)

        self.space_combo = QComboBox()
        self.space_combo.setCursor(Qt.PointingHandCursor)
        self.space_combo.currentIndexChanged.connect(self._on_space_changed)
        layout.addWidget(self.space_combo)

        self.btn_from_template = self._mk_icon_btn("📋  From template")
        self.btn_from_template.setFixedHeight(26)
        layout.addWidget(self.btn_from_template)

        self.btn_new_space.clicked.connect(self._new_space)
        self.btn_from_template.clicked.connect(self._new_from_template)
        self.btn_edit_space.clicked.connect(self._edit_space)
        self.btn_del_space.clicked.connect(self._delete_space)

        layout.addWidget(self._divider())

        # Threads section
        thread_hdr = QHBoxLayout()
        thread_hdr.addWidget(self._mk_label("Threads"))
        thread_hdr.addStretch()
        self.btn_new_thread = self._mk_icon_btn("+ New", "New thread")
        self.btn_new_thread.clicked.connect(self._new_thread)
        thread_hdr.addWidget(self.btn_new_thread)
        layout.addLayout(thread_hdr)

        self.thread_list = QListWidget()
        self.thread_list.setCursor(Qt.PointingHandCursor)
        self.thread_list.itemClicked.connect(self._on_thread_clicked)
        self.thread_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.thread_list.customContextMenuRequested.connect(self._thread_context_menu)
        layout.addWidget(self.thread_list)

    # ── Quick Chat ──────────────────────────────────────────────────
    def _quick_chat(self):
        space_id = self._get_or_create_quick_chat_space()
        for i in range(self.space_combo.count()):
            if self.space_combo.itemData(i) == space_id:
                self.space_combo.setCurrentIndex(i)
                break
        thread_id = db.create_thread(space_id)
        self._load_threads()
        self._select_thread_item(thread_id)
        self.thread_selected.emit(thread_id)

    def _get_or_create_quick_chat_space(self) -> int:
        for s in db.get_spaces():
            if s["name"] == QUICK_CHAT_SPACE_NAME:
                return s["id"]
        db.create_space(
            name=QUICK_CHAT_SPACE_NAME,
            instructions="You are a helpful assistant.",
            model="", github_repo="", web_search=True,
        )
        self._load_spaces()
        for s in db.get_spaces():
            if s["name"] == QUICK_CHAT_SPACE_NAME:
                return s["id"]

    # ── Spaces ───────────────────────────────────────────────────────
    def _load_spaces(self):
        self.space_combo.blockSignals(True)
        self.space_combo.clear()
        for s in db.get_spaces():
            self.space_combo.addItem(s["name"], s["id"])
        self.space_combo.blockSignals(False)
        if self.space_combo.count():
            self.space_combo.setCurrentIndex(0)
            self._on_space_changed(0)

    def _on_space_changed(self, index):
        if index < 0:
            return
        self.current_space_id = self.space_combo.currentData()
        self._load_threads()
        if self.current_space_id:
            self.space_changed.emit(self.current_space_id)
            if self.thread_list.count() > 0:
                first = self.thread_list.item(0)
                self.thread_list.setCurrentItem(first)
                self.thread_selected.emit(first.data(Qt.UserRole))
            else:
                tid = db.create_thread(self.current_space_id)
                self._load_threads()
                self._select_thread_item(tid)
                self.thread_selected.emit(tid)

    def _load_threads(self):
        self.thread_list.clear()
        if not self.current_space_id:
            return
        for t in db.get_threads(self.current_space_id):
            item = QListWidgetItem("💬  " + t["title"])
            item.setData(Qt.UserRole, t["id"])
            self.thread_list.addItem(item)

    def _select_thread_item(self, thread_id: int):
        for i in range(self.thread_list.count()):
            item = self.thread_list.item(i)
            if item.data(Qt.UserRole) == thread_id:
                self.thread_list.setCurrentItem(item)
                break

    def _on_thread_clicked(self, item):
        self.thread_selected.emit(item.data(Qt.UserRole))

    def _thread_context_menu(self, pos):
        item = self.thread_list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background:{D['surface2']}; border:1px solid {D['border']}; border-radius:6px; padding:4px; }}
            QMenu::item {{ padding:6px 16px; border-radius:4px; }}
            QMenu::item:selected {{ background:{D['accent']}; color:#fff; }}
        """)
        rename = menu.addAction("✎  Rename")
        delete = menu.addAction("✕  Delete")
        action = menu.exec_(self.thread_list.mapToGlobal(pos))
        tid = item.data(Qt.UserRole)
        if action == rename:
            new_title, ok = QInputDialog.getText(self, "Rename Thread", "New title:", text=item.text().replace("💬  ", ""))
            if ok and new_title.strip():
                db.rename_thread(tid, new_title.strip())
                item.setText("💬  " + new_title.strip())
        elif action == delete:
            if QMessageBox.question(self, "Delete", "Delete this thread?") == QMessageBox.Yes:
                db.delete_thread(tid)
                self._load_threads()
                if self.thread_list.count() > 0:
                    first = self.thread_list.item(0)
                    self.thread_list.setCurrentItem(first)
                    self.thread_selected.emit(first.data(Qt.UserRole))

    def _new_thread(self):
        if not self.current_space_id:
            return
        tid = db.create_thread(self.current_space_id)
        self._load_threads()
        self._select_thread_item(tid)
        self.thread_selected.emit(tid)

    def _new_space(self):
        dlg = SpaceDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            db.create_space(**dlg.get_data())
            self._load_spaces()

    def _new_from_template(self):
        if not os.path.exists(TEMPLATES_DIR):
            QMessageBox.information(self, "Templates", "No templates folder found.")
            return
        files = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".json")]
        if not files:
            QMessageBox.information(self, "Templates", "No templates found.")
            return
        name, ok = QInputDialog.getItem(self, "Choose Template", "Template:", files, 0, False)
        if ok:
            with open(os.path.join(TEMPLATES_DIR, name)) as f:
                tpl = json.load(f)
            db.create_space(
                name=tpl.get("name", "New Space"),
                instructions=tpl.get("instructions", ""),
                model=tpl.get("model", ""),
                github_repo=tpl.get("github_repo", ""),
                web_search=tpl.get("web_search", True),
            )
            self._load_spaces()

    def _edit_space(self):
        if not self.current_space_id:
            return
        dlg = SpaceDialog(self, db.get_space(self.current_space_id))
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            db.update_space(self.current_space_id, **data)
            self.space_combo.setItemText(self.space_combo.currentIndex(), data["name"])

    def _delete_space(self):
        if not self.current_space_id:
            return
        if QMessageBox.question(self, "Delete Space", "Delete this space and all threads?") == QMessageBox.Yes:
            db.delete_space(self.current_space_id)
            self._load_spaces()
            self.thread_list.clear()
