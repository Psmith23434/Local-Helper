"""Right panel: chat interface with streaming support."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QComboBox, QLabel, QSizePolicy, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont
import database as db
import ai_client
import search
import file_context
import github_context
from config import DEFAULT_MODEL, AVAILABLE_MODELS


class WorkerSignals(QObject):
    chunk   = pyqtSignal(str)
    done    = pyqtSignal(str)
    error   = pyqtSignal(str)


class ChatWorker(QThread):
    """Runs AI request in background thread to keep UI responsive."""

    def __init__(self, messages, model, stream=True):
        super().__init__()
        self.messages = messages
        self.model    = model
        self.stream   = stream
        self.signals  = WorkerSignals()

    def run(self):
        try:
            if self.stream:
                full = ""
                # ai_client now yields plain str chunks
                for chunk in ai_client.chat(self.messages, self.model, stream=True):
                    full += chunk
                    self.signals.chunk.emit(chunk)
                self.signals.done.emit(full)
            else:
                reply = ai_client.chat(self.messages, self.model, stream=False)
                self.signals.done.emit(reply)
        except Exception as e:
            self.signals.error.emit(str(e))


class ChatPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_thread_id = None
        self.current_space_id  = None
        self.space_data        = None
        self._stream_buffer    = ""
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        # Top bar
        top = QHBoxLayout()
        top.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(AVAILABLE_MODELS)
        self.model_combo.setCurrentText(DEFAULT_MODEL)
        top.addWidget(self.model_combo)
        top.addStretch()
        self.web_search_check = QCheckBox("Web search")
        self.web_search_check.setChecked(True)
        top.addWidget(self.web_search_check)
        layout.addLayout(top)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.chat_display)

        # Input row
        input_row = QHBoxLayout()
        self.input_box = QTextEdit()
        self.input_box.setFixedHeight(80)
        self.input_box.setPlaceholderText("Type your message... (Ctrl+Enter to send)")
        self.input_box.installEventFilter(self)
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedWidth(80)
        self.send_btn.setFixedHeight(80)
        self.send_btn.clicked.connect(self._send)
        input_row.addWidget(self.input_box)
        input_row.addWidget(self.send_btn)
        layout.addLayout(input_row)

        # Status label
        self.status_label = QLabel("Select or create a Space and Thread to start chatting.")
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.status_label)

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if obj is self.input_box and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
                self._send()
                return True
        return super().eventFilter(obj, event)

    def set_space(self, space_id: int):
        self.current_space_id = space_id
        self.space_data = db.get_space(space_id)
        if self.space_data:
            model = self.space_data.get("model") or DEFAULT_MODEL
            idx = self.model_combo.findText(model)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
            self.web_search_check.setChecked(bool(self.space_data.get("web_search", True)))

    def load_thread(self, thread_id: int):
        self.current_thread_id = thread_id
        self.status_label.setText(f"Thread #{thread_id} active")
        self.chat_display.clear()
        for msg in db.get_messages(thread_id):
            self._append_message(msg["role"], msg["content"])

    def _append_message(self, role: str, content: str):
        color = "#1a73e8" if role == "user" else "#2d6a4f"
        label = "You" if role == "user" else "Assistant"
        self.chat_display.append(
            f'<b style="color:{color}">{label}:</b><br>{content}<br>'
        )

    def _send(self):
        # Guard: need a thread selected
        if not self.current_thread_id:
            self.status_label.setText("⚠️ Please select a Space and Thread from the sidebar first.")
            self.status_label.setStyleSheet("color: #cc0000; font-size: 11px;")
            return

        user_text = self.input_box.toPlainText().strip()
        if not user_text:
            return

        self.input_box.clear()
        self.send_btn.setEnabled(False)
        self.status_label.setText("Sending...")
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        db.add_message(self.current_thread_id, "user", user_text)
        self._append_message("user", user_text)

        # Build system prompt
        system = ""
        if self.space_data:
            system = self.space_data.get("instructions") or ""

        extra_context = ""

        # Web search context
        if self.web_search_check.isChecked():
            self._set_status("Searching the web...")
            web_ctx = search.web_search(user_text)
            if web_ctx:
                extra_context += f"\n\n--- Web Search Results ---\n{web_ctx}"

        # File context
        if self.space_data:
            files = db.get_space_files(self.current_space_id)
            if files:
                paths = [f["filepath"] for f in files]
                extra_context += "\n\n--- Attached Files ---\n" + file_context.build_file_context(paths)

            # GitHub context
            repo = self.space_data.get("github_repo", "")
            if repo:
                gh_files = github_context.list_repo_files(repo)
                if gh_files:
                    file_tree = "\n".join(gh_files[:50])
                    extra_context += f"\n\n--- GitHub Repo: {repo} ---\nFiles:\n{file_tree}"

        if extra_context:
            system = (system + "\n\n--- Context ---" + extra_context).strip()
        if not system:
            system = "You are a helpful assistant."

        # Build message history
        history = db.get_messages(self.current_thread_id)
        messages = [{"role": "system", "content": system}]
        for m in history:
            messages.append({"role": m["role"], "content": m["content"]})

        model = self.model_combo.currentText()
        self._set_status(f"Waiting for {model}...")

        # Placeholder for streaming reply
        self.chat_display.append('<b style="color:#2d6a4f">Assistant:</b><br>')
        self._stream_buffer = ""

        self.worker = ChatWorker(messages, model, stream=True)
        self.worker.signals.chunk.connect(self._on_chunk)
        self.worker.signals.done.connect(self._on_done)
        self.worker.signals.error.connect(self._on_error)
        self.worker.start()

    def _set_status(self, text: str):
        self.status_label.setText(text)
        try:
            self.window().set_status(text)
        except Exception:
            pass

    def _on_chunk(self, delta: str):
        self._stream_buffer += delta
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(delta)
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

    def _on_done(self, full_reply: str):
        self.chat_display.append("<br>")
        db.add_message(self.current_thread_id, "assistant", full_reply)
        self.send_btn.setEnabled(True)
        self._set_status("Ready")
        # Auto-rename thread on first reply
        threads = db.get_threads(self.current_space_id)
        current = next((t for t in threads if t["id"] == self.current_thread_id), None)
        if current and current["title"] == "New Thread":
            new_title = (full_reply[:40] + "...") if len(full_reply) > 40 else full_reply
            db.rename_thread(self.current_thread_id, new_title)

    def _on_error(self, error_msg: str):
        self.chat_display.append(f'<b style="color:red">Error: {error_msg}</b><br>')
        self.send_btn.setEnabled(True)
        self._set_status("Error")
        self.status_label.setStyleSheet("color: #cc0000; font-size: 11px;")
