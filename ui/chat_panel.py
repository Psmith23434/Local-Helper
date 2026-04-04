"""Chat panel — dark premium redesign with markdown + code block actions."""

import re
import os
import io
import base64
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QTextBrowser,
    QPushButton, QComboBox, QLabel, QCheckBox, QFrame,
    QFileDialog, QApplication, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QTextCursor, QColor
import database as db
import ai_client
import search
import file_context
import github_context
from config import DEFAULT_MODEL, AVAILABLE_MODELS

D = {
    "bg":          "#0d0d0d",
    "surface":     "#141414",
    "surface2":    "#1a1a1a",
    "surface3":    "#1f1f1f",
    "border":      "#2a2a2a",
    "accent":      "#7c6af7",
    "accent_dim":  "#5a4fd1",
    "text":        "#e8e8e8",
    "muted":       "#666666",
    "user_color":  "#7c6af7",
    "ai_color":    "#4ade80",
    "code_bg":     "#111111",
    "code_border": "#2a2a2a",
    "btn_hover":   "#222222",
    "red":         "#f87171",
    "yellow":      "#fbbf24",
    "snip_fg":     "#60c090",
    "snip_bg":     "#1a3a2a",
    "snip_bd":     "#2a5a3a",
    "ocr_fg":      "#60a8e0",
    "ocr_bg":      "#1a2a3a",
    "ocr_bd":      "#2a4a6a",
}

PANEL_QSS = f"""
QWidget#ChatPanel {{
    background: {D['bg']};
}}

/* Top bar */
QWidget#TopBar {{
    background: {D['surface']};
    border-bottom: 1px solid {D['border']};
}}
QComboBox {{
    background: {D['surface2']};
    border: 1px solid {D['border']};
    border-radius: 6px;
    padding: 4px 8px;
    color: {D['text']};
    font-size: 12px;
    min-width: 160px;
}}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background: {D['surface2']};
    border: 1px solid {D['border']};
    selection-background-color: {D['accent']};
    color: {D['text']};
}}
QCheckBox {{
    color: {D['muted']};
    font-size: 12px;
    spacing: 5px;
}}
QCheckBox:hover {{ color: {D['text']}; }}
QCheckBox::indicator {{
    width: 14px; height: 14px;
    border: 1px solid {D['border']};
    border-radius: 3px;
    background: {D['surface2']};
}}
QCheckBox::indicator:checked {{
    background: {D['accent']};
    border-color: {D['accent']};
}}

/* Chat display */
QTextBrowser {{
    background: {D['bg']};
    border: none;
    color: {D['text']};
    font-size: 13px;
    line-height: 1.6;
    padding: 8px 16px;
    selection-background-color: {D['accent']};
}}

/* Input area */
QWidget#InputArea {{
    background: {D['surface']};
    border-top: 1px solid {D['border']};
}}
QTextEdit#InputBox {{
    background: {D['surface2']};
    border: 1px solid {D['border']};
    border-radius: 10px;
    color: {D['text']};
    font-size: 13px;
    padding: 10px 14px;
    selection-background-color: {D['accent']};
}}
QTextEdit#InputBox:focus {{
    border-color: {D['accent']};
}}

/* Send button */
QPushButton#SendBtn {{
    background: {D['accent']};
    color: #ffffff;
    font-weight: 700;
    font-size: 13px;
    border: none;
    border-radius: 10px;
    padding: 0 20px;
}}
QPushButton#SendBtn:hover {{ background: {D['accent_dim']}; }}
QPushButton#SendBtn:pressed {{ background: #4a3faa; }}
QPushButton#SendBtn:disabled {{
    background: #2a2a3a;
    color: {D['muted']};
}}

/* Status bar */
QLabel#StatusLabel {{
    color: {D['muted']};
    font-size: 11px;
    padding: 2px 4px;
}}

/* Code action buttons */
QPushButton#CodeBtn {{
    background: {D['surface3']};
    color: {D['muted']};
    border: 1px solid {D['border']};
    border-radius: 5px;
    font-size: 11px;
    padding: 3px 10px;
}}
QPushButton#CodeBtn:hover {{
    background: {D['btn_hover']};
    color: {D['text']};
    border-color: #444;
}}

/* OCR / Snip input toolbar buttons */
QPushButton#OcrBtn {{
    background: {D['ocr_bg']};
    color: {D['ocr_fg']};
    border: 1px solid {D['ocr_bd']};
    border-radius: 7px;
    font-size: 11px;
    padding: 3px 10px;
}}
QPushButton#OcrBtn:hover {{
    background: #1e3a4a;
    border-color: #3a6a9a;
    color: #80c8ff;
}}
QPushButton#SnipBtn {{
    background: {D['snip_bg']};
    color: {D['snip_fg']};
    border: 1px solid {D['snip_bd']};
    border-radius: 7px;
    font-size: 11px;
    padding: 3px 10px;
}}
QPushButton#SnipBtn:hover {{
    background: #1e4a30;
    border-color: #3a7a50;
    color: #80e0a0;
}}
"""


# ───────────────────────────────────────────────────────────────────
class _GPUAvailable:
    """Tiny singleton — probes torch ONCE and caches the result."""
    _checked = False
    _result  = False

    @classmethod
    def get(cls) -> bool:
        if not cls._checked:
            try:
                import torch
                cls._result = torch.cuda.is_available()
            except Exception:
                cls._result = False
            cls._checked = True
        return cls._result


# ───────────────────────────────────────────────────────────────────
# Markdown → HTML converter (tables, bullets, bold, italic, code, emoji)
# ───────────────────────────────────────────────────────────────────
def markdown_to_html(text: str) -> str:
    lines = text.split("\n")
    html_lines = []
    in_code = False
    code_lang = ""
    code_buf = []
    in_table = False
    in_ul = False
    in_ol = False
    ol_idx = 0

    def flush_list():
        nonlocal in_ul, in_ol, ol_idx
        result = []
        if in_ul:
            result.append("</ul>")
            in_ul = False
        if in_ol:
            result.append("</ol>")
            in_ol = False
            ol_idx = 0
        return result

    def flush_table():
        nonlocal in_table
        result = []
        if in_table:
            result.append("</tbody></table>")
            in_table = False
        return result

    def inline(s):
        s = re.sub(r'`([^`]+)`',
            r'<code style="background:#111;color:#e2c27d;padding:1px 5px;border-radius:4px;font-family:Consolas,monospace;font-size:12px;">\1</code>', s)
        s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
        s = re.sub(r'__(.+?)__',      r'<b>\1</b>', s)
        s = re.sub(r'\*(.+?)\*', r'<i>\1</i>', s)
        s = re.sub(r'_(.+?)_',   r'<i>\1</i>', s)
        s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
            r'<a href="\2" style="color:#7c6af7;">\1</a>', s)
        return s

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.strip().startswith("```"):
            if not in_code:
                html_lines.extend(flush_list())
                html_lines.extend(flush_table())
                code_lang = line.strip()[3:].strip()
                in_code = True
                code_buf = []
            else:
                in_code = False
                code_text = "\n".join(code_buf)
                escaped = code_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                lang_label = f'<span style="color:#666;font-size:10px;float:right;">{code_lang}</span>' if code_lang else ""
                html_lines.append(
                    f'<div style="background:#0a0a0a;border:1px solid #2a2a2a;border-radius:8px;'
                    f'margin:10px 0;overflow:hidden;">'
                    f'<div style="background:#141414;padding:6px 14px;font-size:11px;color:#666;'
                    f'border-bottom:1px solid #2a2a2a;">'
                    f'<span>{code_lang or "code"}</span>{lang_label}</div>'
                    f'<pre style="margin:0;padding:14px;font-family:Consolas,monospace;'
                    f'font-size:12px;color:#e8e8e8;white-space:pre-wrap;word-break:break-word;">'
                    f'{escaped}</pre>'
                    f'<div class="code-actions" data-code="{escaped}" style="padding:6px 14px;'
                    f'border-top:1px solid #1a1a1a;">'
                    f'</div></div>'
                )
                code_buf = []
                code_lang = ""
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        if "|" in line and line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.match(r'^[-: ]+$', c) for c in cells if c):
                i += 1
                continue
            if not in_table:
                html_lines.extend(flush_list())
                html_lines.append(
                    '<table style="border-collapse:collapse;width:100%;margin:10px 0;'
                    'font-size:12px;"><thead>'
                )
                row = "".join(
                    f'<th style="padding:8px 12px;border:1px solid #2a2a2a;'
                    f'background:#1a1a1a;color:#c4baff;text-align:left;">{inline(c)}</th>'
                    for c in cells
                )
                html_lines.append(f"<tr>{row}</tr></thead><tbody>")
                in_table = True
            else:
                row = "".join(
                    f'<td style="padding:7px 12px;border:1px solid #1e1e1e;color:#e8e8e8;">{inline(c)}</td>'
                    for c in cells
                )
                html_lines.append(f"<tr>{row}</tr>")
            i += 1
            continue
        else:
            html_lines.extend(flush_table())

        m = re.match(r'^(#{1,4})\s+(.+)', line)
        if m:
            html_lines.extend(flush_list())
            level = len(m.group(1))
            sizes = {1:"20px", 2:"17px", 3:"15px", 4:"13px"}
            weights = {1:"800", 2:"700", 3:"700", 4:"600"}
            html_lines.append(
                f'<p style="font-size:{sizes[level]};font-weight:{weights[level]};'
                f'color:#e8e8e8;margin:14px 0 6px 0;">{inline(m.group(2))}</p>'
            )
            i += 1
            continue

        m = re.match(r'^[-*+]\s+(.+)', line)
        if m:
            html_lines.extend(flush_table())
            if not in_ul:
                if in_ol: html_lines.extend(flush_list())
                html_lines.append('<ul style="margin:6px 0;padding-left:20px;">')
                in_ul = True
            html_lines.append(f'<li style="margin:3px 0;color:#e8e8e8;">{inline(m.group(1))}</li>')
            i += 1
            continue

        m = re.match(r'^\d+\.\s+(.+)', line)
        if m:
            html_lines.extend(flush_table())
            if not in_ol:
                if in_ul: html_lines.extend(flush_list())
                html_lines.append('<ol style="margin:6px 0;padding-left:20px;">')
                in_ol = True
            html_lines.append(f'<li style="margin:3px 0;color:#e8e8e8;">{inline(m.group(1))}</li>')
            i += 1
            continue

        if re.match(r'^[-*_]{3,}\s*$', line):
            html_lines.extend(flush_list())
            html_lines.extend(flush_table())
            html_lines.append('<hr style="border:none;border-top:1px solid #2a2a2a;margin:12px 0;">')
            i += 1
            continue

        if not line.strip():
            html_lines.extend(flush_list())
            html_lines.extend(flush_table())
            html_lines.append('<div style="height:6px;"></div>')
            i += 1
            continue

        html_lines.extend(flush_list())
        html_lines.extend(flush_table())
        html_lines.append(f'<p style="margin:3px 0;line-height:1.65;">{inline(line)}</p>')
        i += 1

    html_lines.extend(flush_list())
    html_lines.extend(flush_table())
    return "\n".join(html_lines)


def extract_code_blocks(text: str) -> list:
    return [
        {"lang": m.group(1).strip() or "txt", "code": m.group(2)}
        for m in re.finditer(r'```(\w*)\n([\s\S]*?)```', text)
    ]


# ───────────────────────────────────────────────────────────────────
# OCR worker (inline — for image-attach in chat)
# ───────────────────────────────────────────────────────────────────
class _OCRWorker(QThread):
    finished = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, source, langs, use_gpu=False):
        super().__init__()
        self.source  = source
        self.langs   = langs
        self.use_gpu = use_gpu

    def run(self):
        try:
            import numpy as np
            import easyocr
            from PIL import Image
            reader = easyocr.Reader(self.langs, gpu=self.use_gpu)
            if isinstance(self.source, str):
                img = np.array(Image.open(self.source).convert("RGB"))
            else:
                img = np.array(self.source.convert("RGB"))
            results = reader.readtext(img, detail=0, paragraph=True)
            self.finished.emit("\n".join(results) if results else "[No text detected]")
        except Exception as e:
            self.error.emit(str(e))


# ───────────────────────────────────────────────────────────────────
# Worker thread
# ───────────────────────────────────────────────────────────────────
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


# ───────────────────────────────────────────────────────────────────
# Chat Panel
# ───────────────────────────────────────────────────────────────────
class ChatPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ChatPanel")
        self.current_thread_id = None
        self.current_space_id  = None
        self.space_data        = None
        self._stream_buffer    = ""
        self._streaming        = False
        self._pending_image    = None
        self.setStyleSheet(PANEL_QSS)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar
        top_bar = QWidget()
        top_bar.setObjectName("TopBar")
        top_bar.setFixedHeight(46)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(14, 0, 14, 0)
        top_layout.setSpacing(10)

        self.space_label = QLabel("No space selected")
        self.space_label.setStyleSheet(f"color:{D['muted']};font-size:12px;")
        top_layout.addWidget(self.space_label)
        top_layout.addStretch()

        top_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(AVAILABLE_MODELS)
        self.model_combo.setCurrentText(DEFAULT_MODEL)
        self.model_combo.setCursor(Qt.PointingHandCursor)
        top_layout.addWidget(self.model_combo)

        self.web_search_check = QCheckBox("🔍 Web search")
        self.web_search_check.setChecked(True)
        top_layout.addWidget(self.web_search_check)

        root.addWidget(top_bar)

        # ── Chat display
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(True)
        self.chat_display.setFont(QFont("Segoe UI", 10))
        self.chat_display.document().setDefaultStyleSheet(
            f"body{{background:{D['bg']};color:{D['text']};font-family:'Segoe UI';font-size:13px;}}"
            f"pre{{font-family:Consolas,monospace;font-size:12px;}}"
            f"code{{font-family:Consolas,monospace;font-size:12px;}}"
            f"a{{color:{D['accent']};}}"
            f"table{{border-collapse:collapse;}}"
        )
        root.addWidget(self.chat_display)

        # ── Code action bar
        self.code_bar = QWidget()
        self.code_bar.setObjectName("CodeBar")
        self.code_bar.setStyleSheet(
            f"QWidget#CodeBar{{background:{D['surface']};border-top:1px solid {D['border']};padding:4px 14px;}}"
        )
        code_bar_layout = QHBoxLayout(self.code_bar)
        code_bar_layout.setContentsMargins(6, 4, 6, 4)
        code_bar_layout.setSpacing(6)

        lbl = QLabel("Code detected:")
        lbl.setStyleSheet(f"color:{D['muted']};font-size:11px;")
        code_bar_layout.addWidget(lbl)

        self.btn_copy_code = QPushButton("📋 Copy")
        self.btn_copy_code.setObjectName("CodeBtn")
        self.btn_copy_code.setCursor(Qt.PointingHandCursor)
        self.btn_copy_code.clicked.connect(self._copy_code)
        code_bar_layout.addWidget(self.btn_copy_code)

        self.btn_save_code = QPushButton("💾 Save file")
        self.btn_save_code.setObjectName("CodeBtn")
        self.btn_save_code.setCursor(Qt.PointingHandCursor)
        self.btn_save_code.clicked.connect(self._save_code)
        code_bar_layout.addWidget(self.btn_save_code)

        self.btn_commit_code = QPushButton("🚀 Commit to GitHub")
        self.btn_commit_code.setObjectName("CodeBtn")
        self.btn_commit_code.setCursor(Qt.PointingHandCursor)
        self.btn_commit_code.clicked.connect(self._commit_code)
        code_bar_layout.addWidget(self.btn_commit_code)

        code_bar_layout.addStretch()
        self.code_bar.hide()
        root.addWidget(self.code_bar)

        # ── OCR toolbar (shown when a pending image is attached)
        self._ocr_bar = QWidget()
        self._ocr_bar.setStyleSheet(
            f"QWidget{{background:{D['surface']};border-top:1px solid {D['border']};}}"
        )
        ocr_bar_lay = QHBoxLayout(self._ocr_bar)
        ocr_bar_lay.setContentsMargins(12, 4, 12, 4)
        ocr_bar_lay.setSpacing(8)
        self._ocr_preview_lbl = QLabel("🖼  Image attached")
        self._ocr_preview_lbl.setStyleSheet(f"color:{D['ocr_fg']};font-size:11px;")
        ocr_bar_lay.addWidget(self._ocr_preview_lbl)
        ocr_bar_lay.addStretch()
        self._ocr_clear_btn = QPushButton("✕ Remove")
        self._ocr_clear_btn.setObjectName("CodeBtn")
        self._ocr_clear_btn.setFixedHeight(22)
        self._ocr_clear_btn.clicked.connect(self._clear_pending_image)
        ocr_bar_lay.addWidget(self._ocr_clear_btn)
        self._ocr_bar.hide()
        root.addWidget(self._ocr_bar)

        # ── Input area
        input_area = QWidget()
        input_area.setObjectName("InputArea")
        input_layout = QVBoxLayout(input_area)
        input_layout.setContentsMargins(12, 8, 12, 8)
        input_layout.setSpacing(6)

        # OCR/Snip toolbar row
        toolbar_row = QHBoxLayout()
        toolbar_row.setSpacing(6)

        self._ocr_file_btn = QPushButton("📷 OCR Image")
        self._ocr_file_btn.setObjectName("OcrBtn")
        self._ocr_file_btn.setFixedHeight(26)
        self._ocr_file_btn.setToolTip("Browse an image → EasyOCR extracts text → inserts into chat")
        self._ocr_file_btn.setCursor(Qt.PointingHandCursor)
        self._ocr_file_btn.clicked.connect(self._ocr_browse_and_insert)
        toolbar_row.addWidget(self._ocr_file_btn)

        self._snip_btn = QPushButton("✂️ Snip")
        self._snip_btn.setObjectName("SnipBtn")
        self._snip_btn.setFixedHeight(26)
        self._snip_btn.setToolTip("Draw a rectangle on screen → EasyOCR extracts text → inserts into chat")
        self._snip_btn.setCursor(Qt.PointingHandCursor)
        self._snip_btn.clicked.connect(self._snip_and_insert)
        toolbar_row.addWidget(self._snip_btn)

        self._ocr_status = QLabel("")
        self._ocr_status.setStyleSheet(f"color:{D['muted']};font-size:11px;")
        toolbar_row.addWidget(self._ocr_status)
        toolbar_row.addStretch()
        input_layout.addLayout(toolbar_row)

        # Input row
        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        self.input_box = QTextEdit()
        self.input_box.setObjectName("InputBox")
        self.input_box.setPlaceholderText("Ask anything… (Ctrl+Enter to send)")
        self.input_box.setFixedHeight(72)
        self.input_box.installEventFilter(self)
        input_row.addWidget(self.input_box)

        self.send_btn = QPushButton("Send ↑")
        self.send_btn.setObjectName("SendBtn")
        self.send_btn.setFixedWidth(80)
        self.send_btn.setFixedHeight(72)
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.clicked.connect(self._send)
        input_row.addWidget(self.send_btn)
        input_layout.addLayout(input_row)

        root.addWidget(input_area)

        self.status_label = QLabel("Select a space or click + New Chat to start.")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setContentsMargins(14, 0, 14, 4)
        root.addWidget(self.status_label)

        self._last_code_blocks: list = []
        self._ocr_worker = None

    # ── Helpers
    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if obj is self.input_box and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
                self._send()
                return True
        return super().eventFilter(obj, event)

    def _set_status(self, text: str, color: str = D["muted"]):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color:{color};font-size:11px;padding:2px 14px;")
        try:
            self.window().set_status(text)
        except Exception:
            pass

    def set_space(self, space_id: int):
        self.current_space_id = space_id
        self.space_data = db.get_space(space_id)
        if self.space_data:
            self.space_label.setText(f"Space: {self.space_data.get('name', '')}")
            self.space_label.setStyleSheet(f"color:{D['accent']};font-size:12px;font-weight:600;")
            model = self.space_data.get("model") or DEFAULT_MODEL
            idx = self.model_combo.findText(model)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
            self.web_search_check.setChecked(bool(self.space_data.get("web_search", True)))

    def load_thread(self, thread_id: int):
        self.current_thread_id = thread_id
        self._set_status(f"Thread #{thread_id}")
        self.chat_display.clear()
        self.code_bar.hide()
        self._last_code_blocks = []
        self._clear_pending_image()
        for msg in db.get_messages(thread_id):
            self._render_message(msg["role"], msg["content"])

    # ── Rendering
    def _render_message(self, role: str, content: str):
        if role == "user":
            avatar = f'<span style="color:{D["user_color"]};font-weight:700;">You</span>'
            bg = D["surface"]
        else:
            avatar = f'<span style="color:{D["ai_color"]};font-weight:700;">Assistant</span>'
            bg = D["bg"]
        body = markdown_to_html(content)
        html = (
            f'<div style="padding:12px 16px;border-bottom:1px solid {D["border"]};'
            f'background:{bg};margin-bottom:2px;">'
            f'<div style="margin-bottom:6px;font-size:11px;color:{D["muted"]};">'
            f'{avatar}</div>'
            f'<div style="color:{D["text"]};">{body}</div>'
            f'</div>'
        )
        self.chat_display.append(html)

    # ── OCR / Snip integration
    def _ocr_browse_and_insert(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image for OCR", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.tiff)"
        )
        if path:
            self._run_ocr_on(path)

    def _snip_and_insert(self):
        """Screen snip using the shared SnipOverlay → OCR → paste into input."""
        from ui.ocr_widget import SnipOverlay, _qpixmap_to_pil
        top = self.window()
        top.hide()
        QApplication.processEvents()
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        dpr = screen.devicePixelRatio()
        self._snip_overlay = SnipOverlay(screenshot, dpr)
        self._ocr_status.setText("Snipping…")

        def _got(pil_img):
            top.show()
            self._run_ocr_on(pil_img)

        def _cancel():
            top.show()
            self._ocr_status.setText("")

        self._snip_overlay.snipped.connect(_got)
        self._snip_overlay.cancelled.connect(_cancel)

    def _run_ocr_on(self, source):
        """source: file path str OR PIL Image.  Auto-uses GPU when available."""
        if self._ocr_worker and self._ocr_worker.isRunning():
            return
        use_gpu = _GPUAvailable.get()
        mode    = "GPU" if use_gpu else "CPU"
        self._ocr_file_btn.setEnabled(False)
        self._snip_btn.setEnabled(False)
        self._ocr_status.setText(f"Running OCR [{mode}]…")
        self._ocr_worker = _OCRWorker(source, ["en", "de"], use_gpu=use_gpu)
        self._ocr_worker.finished.connect(self._on_ocr_done)
        self._ocr_worker.error.connect(self._on_ocr_error)
        self._ocr_worker.start()

    def _on_ocr_done(self, text: str):
        current = self.input_box.toPlainText().strip()
        self.input_box.setPlainText((current + "\n\n" + text) if current else text)
        cursor = self.input_box.textCursor()
        cursor.movePosition(cursor.End)
        self.input_box.setTextCursor(cursor)
        self._ocr_status.setText(f"✓ OCR: {len(text.split())} words inserted")
        self._ocr_file_btn.setEnabled(True)
        self._snip_btn.setEnabled(True)

    def _on_ocr_error(self, msg: str):
        self._ocr_status.setText(f"OCR error: {msg[:60]}")
        self._ocr_file_btn.setEnabled(True)
        self._snip_btn.setEnabled(True)

    # ── Pending image attachment (for vision models)
    def _set_pending_image(self, pil_img):
        self._pending_image = pil_img
        w, h = pil_img.size
        self._ocr_preview_lbl.setText(f"🖼  Image attached  ({w}×{h}px)")
        self._ocr_bar.show()

    def _clear_pending_image(self):
        self._pending_image = None
        self._ocr_bar.hide()

    # ── Send
    def _send(self):
        if not self.current_thread_id:
            self._set_status("⚠ Select a Space and Thread first.", D["red"])
            return

        user_text = self.input_box.toPlainText().strip()
        if not user_text or self._streaming:
            return

        self.input_box.clear()
        self.send_btn.setEnabled(False)
        self.code_bar.hide()
        self._last_code_blocks = []
        self._set_status("Sending...")

        db.add_message(self.current_thread_id, "user", user_text)
        self._render_message("user", user_text)

        system = (self.space_data or {}).get("instructions") or ""
        extra  = ""

        if self.web_search_check.isChecked():
            self._set_status("Searching the web...")
            web_ctx = search.web_search(user_text)
            if web_ctx:
                extra += f"\n\n--- Web Search Results ---\n{web_ctx}"

        if self.space_data:
            files = db.get_space_files(self.current_space_id)
            if files:
                extra += "\n\n--- Attached Files ---\n" + file_context.build_file_context(
                    [f["filepath"] for f in files]
                )
            repo = self.space_data.get("github_repo", "")
            if repo:
                gh_files = github_context.list_repo_files(repo)
                if gh_files:
                    extra += f"\n\n--- GitHub Repo: {repo} ---\nFiles:\n" + "\n".join(gh_files[:50])

        system = ((system + "\n\n--- Context ---" + extra).strip() if extra else system) or "You are a helpful assistant."
        history = db.get_messages(self.current_thread_id)

        if self._pending_image is not None:
            buf = io.BytesIO()
            self._pending_image.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            user_msg = {
                "role": "user",
                "content": [
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/png;base64,{b64}"}},
                    {"type": "text", "text": user_text},
                ]
            }
            self._clear_pending_image()
        else:
            user_msg = {"role": "user", "content": user_text}

        messages = [{"role": "system", "content": system}]
        for m in history[:-1]:
            messages.append({"role": m["role"], "content": m["content"]})
        messages.append(user_msg)

        model = self.model_combo.currentText()
        self._set_status(f"Waiting for {model}...")

        self.chat_display.append(
            f'<div id="streaming" style="padding:12px 16px;border-bottom:1px solid {D["border"]};background:{D["bg"]};margin-bottom:2px;">'
            f'<div style="margin-bottom:6px;font-size:11px;color:{D["muted"]};">'  
            f'<span style="color:{D["ai_color"]};font-weight:700;">Assistant</span></div>'
            f'<div id="stream-content" style="color:{D["text"]};white-space:pre-wrap;">'
            f'<span style="color:{D["muted"]}">\u25cf\u25cf\u25cf</span></div></div>'
        )
        self._stream_buffer = ""
        self._streaming = True
        self._stream_started = False

        self.worker = ChatWorker(messages, model, stream=True)
        self.worker.signals.chunk.connect(self._on_chunk)
        self.worker.signals.done.connect(self._on_done)
        self.worker.signals.error.connect(self._on_error)
        self.worker.start()

    def _on_chunk(self, delta: str):
        self._stream_buffer += delta
        if not self._stream_started:
            self._stream_started = True
            self.chat_display.moveCursor(QTextCursor.End)
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(delta)
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

    def _on_done(self, full_reply: str):
        self._streaming = False
        self.chat_display.clear()
        for msg in db.get_messages(self.current_thread_id):
            self._render_message(msg["role"], msg["content"])
        db.add_message(self.current_thread_id, "assistant", full_reply)
        self._render_message("assistant", full_reply)

        blocks = extract_code_blocks(full_reply)
        if blocks:
            self._last_code_blocks = blocks
            lang = blocks[0]["lang"]
            self.btn_copy_code.setText(f"📋 Copy ({lang})")
            self.btn_save_code.setText(f"💾 Save .{lang}")
            repo = (self.space_data or {}).get("github_repo", "")
            self.btn_commit_code.setVisible(bool(repo))
            self.code_bar.show()

        self.send_btn.setEnabled(True)
        self._set_status("Ready", D["muted"])

        if self.current_space_id:
            threads = db.get_threads(self.current_space_id)
            current = next((t for t in threads if t["id"] == self.current_thread_id), None)
            if current and current["title"] == "New Thread":
                new_title = (full_reply[:42] + "…") if len(full_reply) > 42 else full_reply
                db.rename_thread(self.current_thread_id, new_title)

    def _on_error(self, error_msg: str):
        self._streaming = False
        self.chat_display.append(
            f'<div style="padding:12px 16px;background:#1a0a0a;border-left:3px solid {D["red"]};margin:4px 0;">'
            f'<span style="color:{D["red"]};font-weight:600;">Error:</span> '
            f'<span style="color:#ffaaaa;">{error_msg}</span></div>'
        )
        self.send_btn.setEnabled(True)
        self._set_status(f"Error: {error_msg}", D["red"])

    # ── Code actions
    def _first_code(self) -> str:
        return self._last_code_blocks[0]["code"] if self._last_code_blocks else ""

    def _copy_code(self):
        QApplication.clipboard().setText(self._first_code())
        self.btn_copy_code.setText("✅ Copied!")
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self.btn_copy_code.setText(
            f"📋 Copy ({self._last_code_blocks[0]['lang'] if self._last_code_blocks else ''})"
        ))

    def _save_code(self):
        code = self._first_code()
        if not code: return
        lang = self._last_code_blocks[0]["lang"] if self._last_code_blocks else "txt"
        ext_map = {"python":"py","py":"py","javascript":"js","js":"js",
                   "typescript":"ts","ts":"ts","html":"html","css":"css",
                   "json":"json","bash":"sh","sh":"sh","sql":"sql"}
        ext = ext_map.get(lang.lower(), lang.lower() or "txt")
        path, _ = QFileDialog.getSaveFileName(
            self, "Save code file", f"code.{ext}", f"*.{ext};;All files (*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)
            self.btn_save_code.setText("✅ Saved!")
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1500, lambda: self.btn_save_code.setText(f"💾 Save .{ext}"))

    def _commit_code(self):
        code = self._first_code()
        if not code or not self.space_data: return
        repo = self.space_data.get("github_repo", "")
        if not repo: return
        lang = self._last_code_blocks[0]["lang"] if self._last_code_blocks else "txt"
        ext_map = {"python":"py","py":"py","javascript":"js","js":"js",
                   "typescript":"ts","html":"html","css":"css","bash":"sh"}
        ext = ext_map.get(lang.lower(), "txt")
        from PyQt5.QtWidgets import QInputDialog
        path, ok1 = QInputDialog.getText(self, "Commit to GitHub", "File path in repo:", text=f"output.{ext}")
        if not ok1 or not path.strip(): return
        msg, ok2 = QInputDialog.getText(self, "Commit message", "Commit message:", text="Add AI-generated code")
        if not ok2: return
        try:
            github_context.commit_file(repo, path.strip(), code, msg.strip())
            self.btn_commit_code.setText("✅ Committed!")
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(2000, lambda: self.btn_commit_code.setText("🚀 Commit to GitHub"))
        except Exception as e:
            self._set_status(f"Commit failed: {e}", D["red"])

    # ── Public: receive text from OCR tab “Insert into Chat” button
    def insert_ocr_text(self, text: str):
        current = self.input_box.toPlainText().strip()
        self.input_box.setPlainText((current + "\n\n" + text) if current else text)
        cursor = self.input_box.textCursor()
        cursor.movePosition(cursor.End)
        self.input_box.setTextCursor(cursor)
        self.input_box.setFocus()
