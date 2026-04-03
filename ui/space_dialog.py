"""Dialog for creating / editing an Agent."""

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox,
    QPushButton, QFileDialog, QListWidget, QListWidgetItem,
    QDialogButtonBox, QGroupBox, QTabWidget, QWidget,
    QInputDialog, QMessageBox, QProgressDialog
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
        self.resize(580, 560)
        self._build_ui()
        if space:
            self._populate(space)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # ── Tab 1: General ────────────────────────────────
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

        # ── Tab 2: Dropbox Files ──────────────────────────
        dropbox_tab = QWidget()
        dl = QVBoxLayout(dropbox_tab)
        dl.setSpacing(8)

        info = QLabel(
            "Select files from your Dropbox /local_helper/ folder to use as context for this agent.\n"
            "Supported: .txt, .py, .md — content is read and injected into the system prompt."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #888; font-size: 11px;")
        dl.addWidget(info)

        btn_row = QHBoxLayout()
        self.btn_fetch_dropbox = QPushButton("☁️  Fetch from Dropbox")
        self.btn_fetch_dropbox.setFixedHeight(28)
        self.btn_fetch_dropbox.clicked.connect(self._fetch_dropbox_files)
        self.dropbox_status = QLabel("")
        self.dropbox_status.setStyleSheet("color: #888; font-size: 11px;")
        btn_row.addWidget(self.btn_fetch_dropbox)
        btn_row.addWidget(self.dropbox_status)
        btn_row.addStretch()
        dl.addLayout(btn_row)

        self.dropbox_file_list = QListWidget()
        self.dropbox_file_list.setToolTip("Check files to use as AI context for this agent")
        dl.addWidget(self.dropbox_file_list)

        dl.addWidget(QLabel("Checked files will be downloaded and read every time you send a message."))

        tabs.addTab(dropbox_tab, "☁️  Dropbox")

        # ── Tab 3: Local Files ───────────────────────────
        files_tab = QWidget()
        fl = QVBoxLayout(files_tab)
        self.file_list = QListWidget()
        btn_row2 = QHBoxLayout()
        self.btn_add_file = QPushButton("Add File")
        self.btn_remove_file = QPushButton("Remove")
        btn_row2.addWidget(self.btn_add_file)
        btn_row2.addWidget(self.btn_remove_file)
        fl.addWidget(QLabel("Local files attached as AI context:"))
        fl.addWidget(self.file_list)
        fl.addLayout(btn_row2)
        self.btn_add_file.clicked.connect(self._add_file)
        self.btn_remove_file.clicked.connect(self._remove_file)
        tabs.addTab(files_tab, "Local Files")

        # ── Tab 4: Scheduled Tasks ────────────────────────
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
            # Load previously saved Dropbox file selections
            saved = db.get_space_dropbox_files(self.space_id)
            if saved:
                for fname in saved:
                    item = QListWidgetItem(fname)
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    item.setCheckState(Qt.Checked)
                    self.dropbox_file_list.addItem(item)
                self.dropbox_status.setText(f"{len(saved)} file(s) saved — click Fetch to refresh")

    # ── Dropbox ─────────────────────────────────────────────
    def _fetch_dropbox_files(self):
        """List .txt/.py/.md files from Dropbox /local_helper/ and show as checkboxes."""
        try:
            import dropbox_sync
            if not dropbox_sync.is_configured():
                QMessageBox.warning(
                    self, "Dropbox not configured",
                    "Fill in DROPBOX_APP_KEY, DROPBOX_APP_SECRET and DROPBOX_REFRESH_TOKEN in config.py first."
                )
                return
            self.dropbox_status.setText("Fetching...")
            self.btn_fetch_dropbox.setEnabled(False)
            self.repaint()

            all_files = dropbox_sync.list_remote_files("/local_helper")
            # Filter to supported text formats only
            valid_exts = {".txt", ".py", ".md"}
            files = [f for f in all_files if os.path.splitext(f)[1].lower() in valid_exts]

            # Remember which were already checked
            previously_checked = set()
            for i in range(self.dropbox_file_list.count()):
                it = self.dropbox_file_list.item(i)
                if it.checkState() == Qt.Checked:
                    previously_checked.add(it.text())

            self.dropbox_file_list.clear()
            for fname in sorted(files):
                item = QListWidgetItem(fname)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(
                    Qt.Checked if fname in previously_checked else Qt.Unchecked
                )
                self.dropbox_file_list.addItem(item)

            self.dropbox_status.setText(
                f"{len(files)} file(s) found" if files else "No .txt/.py/.md files found"
            )
        except Exception as e:
            self.dropbox_status.setText(f"Error: {e}")
        finally:
            self.btn_fetch_dropbox.setEnabled(True)

    def _get_checked_dropbox_files(self) -> list:
        checked = []
        for i in range(self.dropbox_file_list.count()):
            it = self.dropbox_file_list.item(i)
            if it.checkState() == Qt.Checked:
                checked.append(it.text())
        return checked

    # ── Local Files ─────────────────────────────────────────
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

    # ── Scheduled Tasks ──────────────────────────────────────
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
            "name":         self.name_edit.text().strip() or "Unnamed Agent",
            "instructions": self.instructions_edit.toPlainText().strip(),
            "model":        self.model_combo.currentText(),
            "github_repo":  self.github_repo_edit.text().strip(),
            "web_search":   self.web_search_check.isChecked(),
            "dropbox_files": self._get_checked_dropbox_files(),
        }
