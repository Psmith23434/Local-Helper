"""Dialog for creating / editing an Agent."""

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox,
    QPushButton, QFileDialog, QListWidget, QListWidgetItem,
    QDialogButtonBox, QGroupBox, QTabWidget, QWidget,
    QInputDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from config import AVAILABLE_MODELS
import database as db
import scheduler


class SpaceDialog(QDialog):
    def __init__(self, parent=None, space: dict = None):
        super().__init__(parent)
        self.space = space
        self.space_id = space["id"] if space else None
        self.setWindowTitle("Edit Agent" if space else "New Agent")
        self.resize(560, 520)
        self._build_ui()
        if space:
            self._populate(space)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # ── Tab 1: General ──────────────────────────
        general = QWidget()
        form = QFormLayout(general)
        self.name_edit = QLineEdit()
        self.model_combo = QComboBox()
        self.model_combo.addItems(AVAILABLE_MODELS)
        self.instructions_edit = QTextEdit()
        self.instructions_edit.setPlaceholderText("System instructions for the AI in this agent...")
        self.web_search_check = QCheckBox("Enable web search")
        self.web_search_check.setChecked(True)
        self.github_repo_edit = QLineEdit()
        self.github_repo_edit.setPlaceholderText("owner/repo  (optional)")
        form.addRow("Name:", self.name_edit)
        form.addRow("Model:", self.model_combo)
        form.addRow("Instructions:", self.instructions_edit)
        form.addRow("", self.web_search_check)
        form.addRow("GitHub Repo:", self.github_repo_edit)
        tabs.addTab(general, "General")

        # ── Tab 2: Files ────────────────────────────
        files_tab = QWidget()
        fl = QVBoxLayout(files_tab)
        self.file_list = QListWidget()
        btn_row = QHBoxLayout()
        self.btn_add_file = QPushButton("Add File")
        self.btn_remove_file = QPushButton("Remove")
        btn_row.addWidget(self.btn_add_file)
        btn_row.addWidget(self.btn_remove_file)
        fl.addWidget(QLabel("Attached files (used as AI context):"))
        fl.addWidget(self.file_list)
        fl.addLayout(btn_row)
        self.btn_add_file.clicked.connect(self._add_file)
        self.btn_remove_file.clicked.connect(self._remove_file)
        tabs.addTab(files_tab, "Files")

        # ── Tab 3: Scheduled Tasks ──────────────────
        tasks_tab = QWidget()
        tl = QVBoxLayout(tasks_tab)
        self.task_list = QListWidget()
        task_btn_row = QHBoxLayout()
        self.btn_add_task   = QPushButton("Add Task")
        self.btn_del_task   = QPushButton("Remove")
        task_btn_row.addWidget(self.btn_add_task)
        task_btn_row.addWidget(self.btn_del_task)
        tl.addWidget(QLabel("Scheduled AI tasks for this agent:"))
        tl.addWidget(self.task_list)
        tl.addLayout(task_btn_row)
        self.btn_add_task.clicked.connect(self._add_task)
        self.btn_del_task.clicked.connect(self._remove_task)
        tabs.addTab(tasks_tab, "Scheduled Tasks")

        layout.addWidget(tabs)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate(self, space):
        self.name_edit.setText(space["name"])
        idx = self.model_combo.findText(space["model"])
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        self.instructions_edit.setPlainText(space["instructions"])
        self.web_search_check.setChecked(bool(space["web_search"]))
        self.github_repo_edit.setText(space["github_repo"] or "")
        if self.space_id:
            for f in db.get_space_files(self.space_id):
                item = QListWidgetItem(f["filepath"])
                item.setData(Qt.UserRole, f["id"])
                self.file_list.addItem(item)
            for t in db.get_scheduled_tasks(self.space_id):
                item = QListWidgetItem(f"{t['name']} [{t['trigger']}]")
                item.setData(Qt.UserRole, t["id"])
                self.task_list.addItem(item)

    def _add_file(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Files", "",
            "Supported Files (*.txt *.py *.md *.json *.yaml *.yml *.toml *.csv);;All Files (*)"
        )
        for p in paths:
            if self.space_id:
                db.add_space_file(self.space_id, p)
            item = QListWidgetItem(p)
            item.setData(Qt.UserRole, None)
            self.file_list.addItem(item)

    def _remove_file(self):
        item = self.file_list.currentItem()
        if not item:
            return
        file_id = item.data(Qt.UserRole)
        if file_id:
            db.remove_space_file(file_id)
        self.file_list.takeItem(self.file_list.row(item))

    def _add_task(self):
        if not self.space_id:
            QMessageBox.information(self, "Tasks", "Save the agent first before adding tasks.")
            return
        name, ok = QInputDialog.getText(self, "Task Name", "Task name:")
        if not ok or not name.strip():
            return
        prompt, ok = QInputDialog.getText(self, "Task Prompt", "Prompt to run:")
        if not ok or not prompt.strip():
            return
        trigger, ok = QInputDialog.getItem(self, "Trigger Type", "Trigger:", ["cron", "interval"], 0, False)
        if not ok:
            return
        if trigger == "cron":
            hour, ok = QInputDialog.getInt(self, "Cron Hour", "Run at hour (0-23):", 8, 0, 23)
            if not ok:
                return
            trigger_args = {"hour": hour, "minute": 0}
        else:
            hours, ok = QInputDialog.getInt(self, "Interval", "Run every N hours:", 1, 1, 168)
            if not ok:
                return
            trigger_args = {"hours": hours}
        task_id = db.add_scheduled_task(self.space_id, name.strip(), prompt.strip(), trigger, trigger_args)
        scheduler.register_task(task_id, self.space_id, prompt.strip(), trigger, trigger_args)
        item = QListWidgetItem(f"{name.strip()} [{trigger}]")
        item.setData(Qt.UserRole, task_id)
        self.task_list.addItem(item)

    def _remove_task(self):
        item = self.task_list.currentItem()
        if not item:
            return
        task_id = item.data(Qt.UserRole)
        if task_id:
            db.delete_scheduled_task(task_id)
            scheduler.remove_task(task_id)
        self.task_list.takeItem(self.task_list.row(item))

    def get_data(self) -> dict:
        return {
            "name":        self.name_edit.text().strip() or "Unnamed Agent",
            "instructions": self.instructions_edit.toPlainText().strip(),
            "model":       self.model_combo.currentText(),
            "github_repo": self.github_repo_edit.text().strip(),
            "web_search":  self.web_search_check.isChecked(),
        }
