"""Left sidebar: Space selector + Thread list."""

import json
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QLabel, QMenu, QInputDialog, QMessageBox,
    QComboBox, QDialog
)
from PyQt5.QtCore import pyqtSignal, Qt
import database as db
from config import TEMPLATES_DIR
from ui.space_dialog import SpaceDialog


class Sidebar(QWidget):
    thread_selected = pyqtSignal(int)   # thread_id
    space_changed   = pyqtSignal(int)   # space_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(200)
        self.setMaximumWidth(320)
        self.current_space_id = None
        self._build_ui()
        self._load_spaces()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Space selector row
        lbl = QLabel("Space")
        lbl.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(lbl)

        self.space_combo = QComboBox()
        self.space_combo.currentIndexChanged.connect(self._on_space_changed)
        layout.addWidget(self.space_combo)

        # Space action buttons
        btn_row = QHBoxLayout()
        self.btn_new_space    = QPushButton("+ New")
        self.btn_from_template = QPushButton("Template")
        self.btn_edit_space   = QPushButton("Edit")
        self.btn_del_space    = QPushButton("Delete")
        for b in [self.btn_new_space, self.btn_from_template, self.btn_edit_space, self.btn_del_space]:
            b.setFixedHeight(26)
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        self.btn_new_space.clicked.connect(self._new_space)
        self.btn_from_template.clicked.connect(self._new_from_template)
        self.btn_edit_space.clicked.connect(self._edit_space)
        self.btn_del_space.clicked.connect(self._delete_space)

        # Thread list
        lbl2 = QLabel("Threads")
        lbl2.setStyleSheet("font-weight: bold; font-size: 13px; margin-top: 8px;")
        layout.addWidget(lbl2)

        self.thread_list = QListWidget()
        self.thread_list.itemClicked.connect(self._on_thread_clicked)
        self.thread_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.thread_list.customContextMenuRequested.connect(self._thread_context_menu)
        layout.addWidget(self.thread_list)

        self.btn_new_thread = QPushButton("+ New Thread")
        self.btn_new_thread.clicked.connect(self._new_thread)
        layout.addWidget(self.btn_new_thread)

    def _load_spaces(self):
        self.space_combo.blockSignals(True)
        self.space_combo.clear()
        spaces = db.get_spaces()
        for s in spaces:
            self.space_combo.addItem(s["name"], s["id"])
        self.space_combo.blockSignals(False)
        if spaces:
            self.space_combo.setCurrentIndex(0)
            self._on_space_changed(0)

    def _on_space_changed(self, index):
        if index < 0:
            return
        self.current_space_id = self.space_combo.currentData()
        self._load_threads()
        if self.current_space_id:
            self.space_changed.emit(self.current_space_id)

    def _load_threads(self):
        self.thread_list.clear()
        if not self.current_space_id:
            return
        for t in db.get_threads(self.current_space_id):
            item = QListWidgetItem(t["title"])
            item.setData(Qt.UserRole, t["id"])
            self.thread_list.addItem(item)

    def _on_thread_clicked(self, item):
        thread_id = item.data(Qt.UserRole)
        self.thread_selected.emit(thread_id)

    def _thread_context_menu(self, pos):
        item = self.thread_list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        rename = menu.addAction("Rename")
        delete = menu.addAction("Delete")
        action = menu.exec_(self.thread_list.mapToGlobal(pos))
        thread_id = item.data(Qt.UserRole)
        if action == rename:
            new_title, ok = QInputDialog.getText(self, "Rename Thread", "New title:", text=item.text())
            if ok and new_title.strip():
                db.rename_thread(thread_id, new_title.strip())
                item.setText(new_title.strip())
        elif action == delete:
            if QMessageBox.question(self, "Delete Thread", "Delete this thread?") == QMessageBox.Yes:
                db.delete_thread(thread_id)
                self._load_threads()

    def _new_thread(self):
        if not self.current_space_id:
            return
        thread_id = db.create_thread(self.current_space_id)
        self._load_threads()
        self.thread_selected.emit(thread_id)

    def _new_space(self):
        dlg = SpaceDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            db.create_space(**data)
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
        space = db.get_space(self.current_space_id)
        dlg = SpaceDialog(self, space)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            db.update_space(self.current_space_id, **data)
            idx = self.space_combo.currentIndex()
            self.space_combo.setItemText(idx, data["name"])

    def _delete_space(self):
        if not self.current_space_id:
            return
        if QMessageBox.question(self, "Delete Space", "Delete this space and all its threads?") == QMessageBox.Yes:
            db.delete_space(self.current_space_id)
            self._load_spaces()
            self.thread_list.clear()
