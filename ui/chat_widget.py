"""Reusable chat widget used by both General Chat and Agents tabs."""

import re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QTextEdit,
    QPushButton, QComboBox, QLabel, QCheckBox, QFileDialog, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QFont, QTextCursor
import database as db
import ai_client
import search
import file_context
import github_context
from config import DEFAULT_MODEL, AVAILABLE_MODELS
from ui.theme import get as T
from ui.styles import accent_btn_qss, code_btn_qss


# ── Markdown renderer ───────────────────────────────────────────
def markdown_to_html(text: str) -> str:
    lines = text.split("\n")
    out = []
    in_code = False
    code_lang = ""
    code_buf = []
    in_table = False
    in_ul = False
    in_ol = False

    def flush_lists():
        nonlocal in_ul, in_ol
        r = []
        if in_ul: r.append("</ul>"); in_ul = False
        if in_ol: r.append("</ol>"); in_ol = False
        return r

    def flush_table():
        nonlocal in_table
        r = []
        if in_table: r.append("</tbody></table>"); in_table = False
        return r

    def inline(s):
        d = T()
        s = re.sub(r'`([^`]+)`',
            rf'<code style="background:{d["code_bg"]};color:#e2c27d;padding:1px 5px;'
            r'border-radius:4px;font-family:Consolas,monospace;font-size:12px;">\1</code>', s)
        s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
        s = re.sub(r'__(.+?)__',      r'<b>\1</b>', s)
        s = re.sub(r'\*(.+?)\*',  r'<i>\1</i>', s)
        s = re.sub(r'_(.+?)_',    r'<i>\1</i>', s)
        s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
            rf'<a href="\2" style="color:{d["accent"]};">\1</a>', s)
        return s

    i = 0
    while i < len(lines):
        line = lines[i]
        d = T()

        if line.strip().startswith("```"):
            if not in_code:
                out.extend(flush_lists()); out.extend(flush_table())
                code_lang = line.strip()[3:].strip()
                in_code = True; code_buf = []
            else:
                in_code = False
                code = "\n".join(code_buf)
                esc = code.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                out.append(
                    f'<div style="background:{d["code_bg"]};border:1px solid {d["border"]};'
                    f'border-radius:8px;margin:10px 0;">'
                    f'<div style="background:{d["surface2"]};padding:5px 14px;font-size:10px;'
                    f'color:{d["muted"]};border-bottom:1px solid {d["border"]};'
                    f'font-family:Consolas,monospace;">'
                    f'{code_lang or "code"}</div>'
                    f'<pre style="margin:0;padding:14px;font-family:Consolas,monospace;'
                    f'font-size:12px;color:{d["text"]};white-space:pre-wrap;word-break:break-word;">'
                    f'{esc}</pre></div>'
                )
                code_buf = []; code_lang = ""
            i += 1; continue

        if in_code:
            code_buf.append(line); i += 1; continue

        if "|" in line and line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.match(r'^[-: ]+$', c) for c in cells if c):
                i += 1; continue
            if not in_table:
                out.extend(flush_lists())
                out.append(f'<table style="border-collapse:collapse;width:100%;margin:10px 0;font-size:12px;"><thead>')
                row = "".join(
                    f'<th style="padding:7px 12px;border:1px solid {d["border"]};'
                    f'background:{d["surface2"]};color:{d["accent"]};text-align:left;">{inline(c)}</th>'
                    for c in cells)
                out.append(f"<tr>{row}</tr></thead><tbody>")
                in_table = True
            else:
                row = "".join(
                    f'<td style="padding:6px 12px;border:1px solid {d["faint"]};color:{d["text"]};">'
                    f'{inline(c)}</td>' for c in cells)
                out.append(f"<tr>{row}</tr>")
            i += 1; continue
        else:
            out.extend(flush_table())

        m = re.match(r'^(#{1,4})\s+(.+)', line)
        if m:
            out.extend(flush_lists())
            lvl = len(m.group(1))
            sz = {1:"20px",2:"17px",3:"15px",4:"13px"}[lvl]
            fw = {1:"800",2:"700",3:"700",4:"600"}[lvl]
            out.append(f'<p style="font-size:{sz};font-weight:{fw};color:{d["text"]};margin:14px 0 6px 0;">{inline(m.group(2))}</p>')
            i += 1; continue

        m = re.match(r'^[-*+]\s+(.+)', line)
        if m:
            out.extend(flush_table())
            if not in_ul:
                out.extend(flush_lists())
                out.append(f'<ul style="margin:6px 0;padding-left:20px;">')
                in_ul = True
            out.append(f'<li style="margin:3px 0;color:{d["text"]}">{inline(m.group(1))}</li>')
            i += 1; continue

        m = re.match(r'^\d+\.\s+(.+)', line)
        if m:
            out.extend(flush_table())
            if not in_ol:
                out.extend(flush_lists())
                out.append(f'<ol style="margin:6px 0;padding-left:20px;">')
                in_ol = True
            out.append(f'<li style="margin:3px 0;color:{d["text"]}">{inline(m.group(1))}</li>')
            i += 1; continue

        if re.match(r'^[-*_]{3,}\s*$', line):
            out.extend(flush_lists()); out.extend(flush_table())
            out.append(f'<hr style="border:none;border-top:1px solid {d["border"]};margin:12px 0;">')
            i += 1; continue

        if not line.strip():
            out.extend(flush_lists()); out.extend(flush_table())
            out.append('<div style="height:5px;"></div>')
            i += 1; continue

        out.extend(flush_lists()); out.extend(flush_table())
        out.append(f'<p style="margin:3px 0;line-height:1.65;">{inline(line)}</p>')
        i += 1

    out.extend(flush_lists()); out.extend(flush_table())
    return "\n".join(out)


def extract_code_blocks(text: str) -> list[dict]:
    return [
        {"lang": m.group(1).strip() or "txt", "code": m.group(2)}
        for m in re.finditer(r'```(\w*)\n([\s\S]*?)```', text)
    ]


# ── Worker ────────────────────────────────────────────────
class WorkerSignals(QObject):
    chunk = pyqtSignal(str)
    done  = pyqtSignal(str)
    error = pyqtSignal(str)


class ChatWorker(QThread):
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
                for chunk in ai_client.chat(self.messages, self.model, stream=True):
                    full += chunk
                    self.signals.chunk.emit(chunk)
                self.signals.done.emit(full)
            else:
                reply = ai_client.chat(self.messages, self.model, stream=False)
                self.signals.done.emit(reply)
        except Exception as e:
            self.signals.error.emit(str(e))


# ── Chat Widget ───────────────────────────────────────────────
class ChatWidget(QWidget):
    """
    Self-contained chat UI.
    Pass space_id to bind it to an agent/space, or leave None for general chat.
    Pass on_thread_renamed callback(thread_id, new_title) to notify parent.
    """
    status_changed = pyqtSignal(str)

    def __init__(self, space_id: int | None = None,
                 system_prompt: str = "You are a helpful assistant.",
                 web_search_default: bool = False,
                 on_thread_renamed=None,
                 parent=None):
        super().__init__(parent)
        self.space_id          = space_id
        self.system_prompt     = system_prompt
        self._dropbox_context  = ""   # injected between instructions and user message
        self.current_thread_id = None
        self._stream_buffer    = ""
        self._streaming        = False
        self._stream_started   = False
        self._last_code_blocks: list[dict] = []
        self._on_thread_renamed = on_thread_renamed
        self._web_search_default = web_search_default
        self._msg_count        = 0
        self._build_ui()

    def _build_ui(self):
        d = T()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Top bar
        top = QWidget()
        top.setFixedHeight(44)
        top.setStyleSheet(f"background:{d['surface']};border-bottom:1px solid {d['border']};")
        tl = QHBoxLayout(top)
        tl.setContentsMargins(14, 0, 14, 0)
        tl.setSpacing(10)
        self.context_label = QLabel("")
        self.context_label.setStyleSheet(f"color:{d['accent']};font-size:12px;font-weight:600;")
        tl.addWidget(self.context_label)
        tl.addStretch()

        # Re-sync Dropbox button (only visible when Dropbox context is loaded)
        self.btn_resync = QPushButton("☁️ Re-sync")
        self.btn_resync.setFixedHeight(26)
        self.btn_resync.setFixedWidth(90)
        self.btn_resync.setCursor(Qt.PointingHandCursor)
        self.btn_resync.setToolTip("Re-download Dropbox context files for this agent")
        self.btn_resync.setStyleSheet(
            f"QPushButton{{background:{d['surface2']};color:{d['muted']};border:1px solid {d['border']};"
            f"border-radius:5px;font-size:11px;padding:0 8px;}}"
            f"QPushButton:hover{{background:{d['surface3']};color:{d['text']};}}"
        )
        self.btn_resync.clicked.connect(self._on_resync_clicked)
        self.btn_resync.hide()  # hidden until Dropbox context is set
        tl.addWidget(self.btn_resync)

        tl.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(AVAILABLE_MODELS)
        self.model_combo.setCurrentText(DEFAULT_MODEL)
        self.model_combo.setCursor(Qt.PointingHandCursor)
        self.model_combo.setToolTip("Switch model — takes effect on the next message")
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        tl.addWidget(self.model_combo)
        self.web_check = QCheckBox("🔍 Web")
        self.web_check.setChecked(self._web_search_default)
        tl.addWidget(self.web_check)
        root.addWidget(top)

        # Chat display
        self.display = QTextBrowser()
        self.display.setOpenExternalLinks(True)
        self.display.setFont(QFont("Segoe UI", 10))
        d2 = T()
        self.display.document().setDefaultStyleSheet(
            f"body{{background:{d2['bg']};color:{d2['text']};font-family:'Segoe UI';font-size:13px;}}"
            f"pre,code{{font-family:Consolas,monospace;font-size:12px;}}"
            f"a{{color:{d2['accent']};}}"
        )
        self.display.setStyleSheet(
            f"QTextBrowser{{background:{d2['bg']};border:none;padding:4px 10px;}}"
        )
        root.addWidget(self.display)

        # Code action bar
        self.code_bar = QWidget()
        self.code_bar.setStyleSheet(
            f"background:{d['surface']};border-top:1px solid {d['border']};"
        )
        cbl = QHBoxLayout(self.code_bar)
        cbl.setContentsMargins(10, 4, 10, 4)
        cbl.setSpacing(6)
        lbl = QLabel("Code detected:")
        lbl.setStyleSheet(f"color:{d['muted']};font-size:11px;")
        cbl.addWidget(lbl)
        self.btn_copy  = QPushButton("📋 Copy")
        self.btn_save  = QPushButton("💾 Save")
        self.btn_commit= QPushButton("🚀 Commit")
        for b in [self.btn_copy, self.btn_save, self.btn_commit]:
            b.setStyleSheet(code_btn_qss())
            b.setCursor(Qt.PointingHandCursor)
            cbl.addWidget(b)
        cbl.addStretch()
        self.btn_copy.clicked.connect(self._copy_code)
        self.btn_save.clicked.connect(self._save_code)
        self.btn_commit.clicked.connect(self._commit_code)
        self.code_bar.hide()
        root.addWidget(self.code_bar)

        # Input area
        inp = QWidget()
        inp.setFixedHeight(90)
        inp.setStyleSheet(f"background:{d['surface']};border-top:1px solid {d['border']};")
        il = QHBoxLayout(inp)
        il.setContentsMargins(12, 8, 12, 8)
        il.setSpacing(8)
        self.input_box = QTextEdit()
        self.input_box.setObjectName("InputBox")
        self.input_box.setPlaceholderText("Ask anything... (Ctrl+Enter to send)")
        self.input_box.setStyleSheet(
            f"QTextEdit{{background:{d['surface2']};border:1px solid {d['border']};"
            f"border-radius:10px;color:{d['text']};padding:8px 12px;}}"
            f"QTextEdit:focus{{border-color:{d['accent']};}}"
        )
        self.input_box.installEventFilter(self)
        il.addWidget(self.input_box)
        self.send_btn = QPushButton("Send ↑")
        self.send_btn.setFixedWidth(74)
        self.send_btn.setFixedHeight(74)
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setStyleSheet(accent_btn_qss())
        self.send_btn.clicked.connect(self._send)
        il.addWidget(self.send_btn)
        root.addWidget(inp)

        # Smart status bar
        self.status_lbl = QLabel("Ready")
        self.status_lbl.setStyleSheet(f"color:{d['muted']};font-size:11px;padding:2px 14px 4px;")
        root.addWidget(self.status_lbl)

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if obj is self.input_box and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
                self._send(); return True
        return super().eventFilter(obj, event)

    # ── Public API ──────────────────────────────────────────────
    def load_thread(self, thread_id: int, context_label: str = ""):
        self.current_thread_id = thread_id
        self.context_label.setText(context_label)
        self.display.clear()
        self.code_bar.hide()
        self._last_code_blocks = []
        msgs = db.get_messages(thread_id)
        self._msg_count = len(msgs)
        for msg in msgs:
            self._render_msg(msg["role"], msg["content"])
        self._update_status_idle()

    def set_system_prompt(self, prompt: str):
        self.system_prompt = prompt

    def set_dropbox_context(self, context_text: str):
        """Set Dropbox file content injected between agent instructions and user message."""
        self._dropbox_context = context_text
        if context_text:
            self.btn_resync.show()
        else:
            self.btn_resync.hide()

    def _on_resync_clicked(self):
        """Signal the parent AgentsTab to re-download Dropbox files."""
        # Walk up to find AgentsTab and call its resync method
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, '_load_dropbox_context') and hasattr(parent, 'current_agent_id'):
                if parent.current_agent_id:
                    parent._load_dropbox_context(parent.current_agent_id)
                return
            parent = parent.parent()

    # ── Smart status helpers ────────────────────────────────────
    def _update_status_idle(self):
        model = self.model_combo.currentText()
        web   = " · 🔍 Web on" if self.web_check.isChecked() else ""
        db_ctx = " · ☁️ Dropbox" if self._dropbox_context else ""
        count = self._msg_count
        if count == 0:
            msg_info = "No messages yet"
        elif count == 1:
            msg_info = "1 message"
        else:
            msg_info = f"{count} messages"
        self._set_status(f"🧠 {model}  ·  {msg_info}{web}{db_ctx}")

    def _on_model_changed(self, model_name: str):
        if not self._streaming:
            self._set_status(f"ℹ️ Model switched to {model_name} — takes effect on next message")
            QTimer.singleShot(3000, self._update_status_idle)

    # ── Rendering ───────────────────────────────────────────────
    def _render_msg(self, role: str, content: str):
        d = T()
        if role == "user":
            avatar = f'<span style="color:{d["user_color"]};font-weight:700;">You</span>'
            bg = d["surface"]
        else:
            avatar = f'<span style="color:{d["ai_color"]};font-weight:700;">Assistant</span>'
            bg = d["bg"]
        body = markdown_to_html(content)
        self.display.append(
            f'<div style="padding:10px 14px;border-bottom:1px solid {d["border"]};background:{bg};margin-bottom:1px;">'
            f'<div style="margin-bottom:5px;font-size:11px;color:{d["muted"]};">{avatar}</div>'
            f'<div style="color:{d["text"]}">{body}</div></div>'
        )

    # ── Send ──────────────────────────────────────────────────
    def _send(self):
        if not self.current_thread_id:
            self._set_status("⚠ No thread selected.", error=True); return
        user_text = self.input_box.toPlainText().strip()
        if not user_text or self._streaming: return

        self.input_box.clear()
        self.send_btn.setEnabled(False)
        self.code_bar.hide()
        self._last_code_blocks = []
        db.add_message(self.current_thread_id, "user", user_text)
        self._msg_count += 1
        self._render_msg("user", user_text)

        # ── Build system prompt: instructions → Dropbox context → (other context appended below)
        system = self.system_prompt
        if self._dropbox_context:
            system = (
                system.rstrip() +
                "\n\n--- Dropbox Context Files ---\n" +
                self._dropbox_context
            )

        extra = ""
        if self.web_check.isChecked():
            self._set_status("🔍 Searching the web...")
            ctx = search.web_search(user_text)
            if ctx: extra += f"\n\n--- Web Results ---\n{ctx}"

        if self.space_id:
            files = db.get_space_files(self.space_id)
            if files:
                extra += "\n\n--- Local Files ---\n" + file_context.build_file_context(
                    [f["filepath"] for f in files])
            space = db.get_space(self.space_id)
            if space:
                repo = space.get("github_repo", "")
                if repo:
                    gh = github_context.list_repo_files(repo)
                    if gh: extra += f"\n\n--- GitHub: {repo} ---\n" + "\n".join(gh[:50])

        if extra:
            system = (system + "\n\n--- Additional Context ---" + extra).strip()

        history  = db.get_messages(self.current_thread_id)
        messages = [{"role": "system", "content": system}]
        for m in history:
            messages.append({"role": m["role"], "content": m["content"]})

        model = self.model_combo.currentText()
        self._set_status(f"⏳ Waiting for {model}...")
        self._stream_buffer  = ""
        self._streaming      = True
        self._stream_started = False

        d = T()
        self.display.append(
            f'<div style="padding:10px 14px;border-bottom:1px solid {d["border"]};'
            f'background:{d["bg"]};margin-bottom:1px;">'
            f'<div style="margin-bottom:5px;font-size:11px;color:{d["muted"]};font-weight:700;'
            f'color:{d["ai_color"]}">Assistant</div>'
            f'<div style="color:{d["muted"]};">●●●</div></div>'
        )

        self.worker = ChatWorker(messages, model, stream=True)
        self.worker.signals.chunk.connect(self._on_chunk)
        self.worker.signals.done.connect(self._on_done)
        self.worker.signals.error.connect(self._on_error)
        self.worker.start()

    def _on_chunk(self, delta: str):
        self._stream_buffer += delta
        if not self._stream_started:
            self._stream_started = True
        cursor = self.display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(delta)
        self.display.setTextCursor(cursor)
        self.display.ensureCursorVisible()

    def _on_done(self, full_reply: str):
        self._streaming = False
        self._msg_count += 1
        db.add_message(self.current_thread_id, "assistant", full_reply)
        self.display.clear()
        for msg in db.get_messages(self.current_thread_id):
            self._render_msg(msg["role"], msg["content"])

        blocks = extract_code_blocks(full_reply)
        if blocks:
            self._last_code_blocks = blocks
            lang = blocks[0]["lang"]
            self.btn_copy.setText(f"📋 Copy ({lang})")
            self.btn_save.setText(f"💾 Save .{lang}")
            space = db.get_space(self.space_id) if self.space_id else None
            self.btn_commit.setVisible(bool(space and space.get("github_repo")))
            self.code_bar.show()

        self.send_btn.setEnabled(True)
        self._update_status_idle()
        self.status_changed.emit("Ready")

        model = self.model_combo.currentText()
        short_model = model.split("/")[-1] if "/" in model else model

        if self.space_id:
            threads = db.get_threads(self.space_id)
            t = next((x for x in threads if x["id"] == self.current_thread_id), None)
            if t and t["title"] == "New Thread":
                title = (full_reply[:38] + "…") if len(full_reply) > 38 else full_reply
                title = f"{title}  [{short_model}]"
                db.rename_thread(self.current_thread_id, title)
                if self._on_thread_renamed:
                    self._on_thread_renamed(self.current_thread_id, title)
        else:
            msgs = db.get_messages(self.current_thread_id)
            first_user = next((m["content"] for m in msgs if m["role"] == "user"), "")
            base = (first_user[:38] + "…") if len(first_user) > 38 else first_user
            title = f"{base}  [{short_model}]"
            db.rename_thread(self.current_thread_id, title)
            if self._on_thread_renamed:
                self._on_thread_renamed(self.current_thread_id, title)

    def _on_error(self, err: str):
        self._streaming = False
        d = T()
        self.display.append(
            f'<div style="padding:10px 14px;background:#1a0a0a;border-left:3px solid {d["red"]};margin:4px 0;">'
            f'<span style="color:{d["red"]};font-weight:600;">Error:</span> '
            f'<span style="color:#ffaaaa;">{err}</span></div>'
        )
        self.send_btn.setEnabled(True)
        self._set_status(f"❌ {err}", error=True)

    # ── Code actions ────────────────────────────────────────────
    def _first_code(self):
        return self._last_code_blocks[0]["code"] if self._last_code_blocks else ""

    def _copy_code(self):
        QApplication.clipboard().setText(self._first_code())
        self.btn_copy.setText("✅ Copied!")
        lang = self._last_code_blocks[0]["lang"] if self._last_code_blocks else ""
        QTimer.singleShot(1500, lambda: self.btn_copy.setText(f"📋 Copy ({lang})"))

    def _save_code(self):
        code = self._first_code()
        if not code: return
        lang = self._last_code_blocks[0]["lang"] if self._last_code_blocks else "txt"
        ext  = {"python":"py","py":"py","javascript":"js","js":"js",
                "typescript":"ts","html":"html","css":"css","json":"json",
                "bash":"sh","sh":"sh","sql":"sql"}.get(lang.lower(), lang.lower() or "txt")
        path, _ = QFileDialog.getSaveFileName(self, "Save", f"code.{ext}", f"*.{ext};;*")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)
            self.btn_save.setText("✅ Saved!")
            QTimer.singleShot(1500, lambda: self.btn_save.setText(f"💾 Save .{ext}"))

    def _commit_code(self):
        code = self._first_code()
        if not code or not self.space_id: return
        space = db.get_space(self.space_id)
        repo  = (space or {}).get("github_repo", "")
        if not repo: return
        lang = self._last_code_blocks[0]["lang"] if self._last_code_blocks else "txt"
        ext  = {"python":"py","py":"py","javascript":"js","html":"html"}.get(lang.lower(),"txt")
        from PyQt5.QtWidgets import QInputDialog
        path, ok1 = QInputDialog.getText(self, "Commit", "File path in repo:", text=f"output.{ext}")
        if not ok1 or not path.strip(): return
        msg, ok2 = QInputDialog.getText(self, "Commit message", "Message:", text="Add AI-generated code")
        if not ok2: return
        try:
            github_context.commit_file(repo, path.strip(), code, msg.strip())
            self.btn_commit.setText("✅ Committed!")
            QTimer.singleShot(2000, lambda: self.btn_commit.setText("🚀 Commit"))
        except Exception as e:
            self._set_status(f"Commit failed: {e}", error=True)

    def _set_status(self, text: str, error: bool = False):
        d = T()
        color = d["red"] if error else d["muted"]
        self.status_lbl.setText(text)
        self.status_lbl.setStyleSheet(f"color:{color};font-size:11px;padding:2px 14px 4px;")
        self.status_changed.emit(text)
