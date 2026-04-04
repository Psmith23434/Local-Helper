"""TranslateWidget — reusable collapsible translation panel.

Emits `text_ready(str)` when the user clicks "Insert into Chat".

Usage:
    widget = TranslateWidget(parent=self)
    widget.set_source_text(ocr_result)   # pre-fill from OCR
    widget.text_ready.connect(chat_panel.insert_text)
"""

from __future__ import annotations

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QComboBox, QFrame, QApplication, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer

import translator as TR


# ── Colour tokens ──────────────────────────────────────────────────────────────
D = {
    "bg":        "#0d0d0d",
    "surface":   "#141414",
    "surface2":  "#1a1a1a",
    "border":    "#2a2a2a",
    "accent":    "#7c6af7",
    "accent2":   "#5a4fd1",
    "text":      "#e8e8e8",
    "muted":     "#666666",
    "green":     "#4ade80",
    "red":       "#f87171",
    "teal":      "#2dd4bf",
    "teal_bg":   "#0d2420",
    "teal_bd":   "#1a4a40",
    "orange":    "#fb923c",
    "orange_bg": "#1e0f00",
}

TRANS_QSS = f"""
QFrame#TransCard {{
    background: {D['surface']};
    border: 1px solid {D['border']};
    border-radius: 10px;
}}
QPushButton#TransBtn {{
    background: {D['teal_bg']};
    color: {D['teal']};
    border: 1px solid {D['teal_bd']};
    border-radius: 7px;
    font-weight: 700;
    padding: 7px 18px;
}}
QPushButton#TransBtn:hover  {{ background: #0f2e28; border-color: #2a6a58; }}
QPushButton#TransBtn:pressed{{ background: #0a2018; }}
QPushButton#TransBtn:disabled{{ color: #444; border-color: #222; background: #111; }}
QPushButton#SmallBtn {{
    background: {D['surface2']};
    color: {D['muted']};
    border: 1px solid {D['border']};
    border-radius: 5px;
    font-size: 11px;
    padding: 3px 10px;
}}
QPushButton#SmallBtn:hover {{ background: #222; color: {D['text']}; }}
QPushButton#InsertBtn {{
    background: #1a2a3a;
    color: #60a8e0;
    border: 1px solid #2a4a6a;
    border-radius: 5px;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
}}
QPushButton#InsertBtn:hover {{ background: #1e3a4a; }}
QComboBox {{
    background: {D['surface2']};
    color: {D['text']};
    border: 1px solid {D['border']};
    border-radius: 5px;
    padding: 3px 8px;
    font-size: 12px;
    min-width: 160px;
}}
QComboBox::drop-down {{ border: none; }}
QComboBox QAbstractItemView {{
    background: {D['surface2']};
    color: {D['text']};
    selection-background-color: {D['accent']};
    border: 1px solid {D['border']};
}}
QTextEdit {{
    background: {D['surface2']};
    color: {D['text']};
    border: 1px solid {D['border']};
    border-radius: 7px;
    padding: 8px;
    font-family: Consolas, monospace;
    font-size: 12px;
}}
"""

# Backend badge styles
_BADGE_LIBRE = (
    f"background:{D['teal_bg']};color:{D['teal']};border:1px solid {D['teal_bd']};"
    "border-radius:4px;padding:1px 7px;font-size:10px;font-weight:700;"
)
_BADGE_GOOGLE = (
    f"background:{D['orange_bg']};color:{D['orange']};border:1px solid #4a2a00;"
    "border-radius:4px;padding:1px 7px;font-size:10px;font-weight:700;"
)
_BADGE_ERROR = (
    f"background:#1a0000;color:{D['red']};border:1px solid #4a0000;"
    "border-radius:4px;padding:1px 7px;font-size:10px;font-weight:700;"
)


# ── Worker thread ─────────────────────────────────────────────────────────────

class _TranslateWorker(QThread):
    finished = pyqtSignal(str, str)   # (translated_text, backend_name)
    error    = pyqtSignal(str, str)

    def __init__(self, text: str, source: str, target: str):
        super().__init__()
        self.text   = text
        self.source = source
        self.target = target

    def run(self):
        try:
            result, backend = TR.translate(self.text, self.source, self.target)
            if result.startswith("[Error]"):
                self.error.emit(result, backend)
            else:
                self.finished.emit(result, backend)
        except Exception as e:
            self.error.emit(f"[Error] {e}", "error")


# ── Main widget ───────────────────────────────────────────────────────────────

class TranslateWidget(QWidget):
    """Collapsible translate panel. Drop anywhere in a QVBoxLayout."""

    text_ready = pyqtSignal(str)

    def __init__(self, parent=None, collapsed: bool = True):
        super().__init__(parent)
        self._worker = None
        self._collapsed = collapsed
        self.setStyleSheet(TRANS_QSS)
        self._build_ui()
        self._load_defaults()
        QTimer.singleShot(500, self._probe_backend)

    def _load_defaults(self):
        default_target = TR.get_default_target()
        name = TR.code_to_name(default_target)
        idx  = self.target_combo.findText(name)
        if idx >= 0:
            self.target_combo.setCurrentIndex(idx)

    def _probe_backend(self):
        """On startup: show which backend will be used based on config + availability."""
        backend_cfg = TR.get_configured_backend()
        if backend_cfg == TR.BACKEND_GOOGLE:
            self._set_backend_badge(TR.BACKEND_GOOGLE, idle=True)
        else:
            available = TR.libretranslate_available()
            if available:
                self._set_backend_badge(TR.BACKEND_LIBRETRANSLATE, idle=True)
            else:
                self._set_backend_badge(TR.BACKEND_GOOGLE, idle=True, lt_offline=True)

    # ── UI ───────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 4, 0, 0)
        root.setSpacing(0)

        # Toggle header
        self._toggle_btn = QPushButton("🌐  Translate  ▸")
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.setChecked(not self._collapsed)
        self._toggle_btn.setStyleSheet(
            f"QPushButton{{background:{D['surface']};color:{D['muted']};"
            f"border:1px solid {D['border']};border-radius:8px;"
            f"padding:6px 14px;font-size:12px;font-weight:600;text-align:left;}}"
            f"QPushButton:checked{{color:{D['teal']};border-color:{D['teal_bd']};}}"
            f"QPushButton:hover{{background:#1e1e1e;color:{D['text']};}}"
        )
        self._toggle_btn.clicked.connect(self._toggle)
        root.addWidget(self._toggle_btn)

        # Body card
        self._card = QFrame()
        self._card.setObjectName("TransCard")
        card_lay = QVBoxLayout(self._card)
        card_lay.setContentsMargins(14, 10, 14, 10)
        card_lay.setSpacing(6)

        # Lang row
        lang_row = QHBoxLayout()
        lang_row.setSpacing(8)
        src_lbl = QLabel("From:")
        src_lbl.setStyleSheet(f"color:{D['muted']};font-size:11px;")
        lang_row.addWidget(src_lbl)
        self.source_combo = QComboBox()
        self.source_combo.addItems(TR.LANG_NAMES)
        self.source_combo.setCurrentText("Auto-detect")
        lang_row.addWidget(self.source_combo)
        arrow = QLabel("→")
        arrow.setStyleSheet(f"color:{D['muted']};font-size:14px;")
        lang_row.addWidget(arrow)
        tgt_lbl = QLabel("To:")
        tgt_lbl.setStyleSheet(f"color:{D['muted']};font-size:11px;")
        lang_row.addWidget(tgt_lbl)
        self.target_combo = QComboBox()
        self.target_combo.addItems(TR.LANG_NAMES[1:])
        lang_row.addStretch()
        card_lay.addLayout(lang_row)
        lang_row.insertWidget(5, self.target_combo)

        # Source text header
        src_hdr = QHBoxLayout()
        src_hdr_lbl = QLabel("Source text:")
        src_hdr_lbl.setStyleSheet(f"color:{D['muted']};font-size:11px;")
        src_hdr.addWidget(src_hdr_lbl)
        src_hdr.addStretch()
        clr_btn = QPushButton("✕ Clear")
        clr_btn.setObjectName("SmallBtn")
        clr_btn.setFixedHeight(22)
        clr_btn.clicked.connect(self._clear_source)
        src_hdr.addWidget(clr_btn)
        card_lay.addLayout(src_hdr)

        # Source text box — compact height, scrollable
        self.source_box = QTextEdit()
        self.source_box.setPlaceholderText(
            "Paste or type text here, or use 'Fill from OCR' after extracting text above…"
        )
        self.source_box.setFixedHeight(72)   # ~4 lines, no large minimum
        card_lay.addWidget(self.source_box)

        # Translate button + backend badge
        action_row = QHBoxLayout()
        self.translate_btn = QPushButton("🌐  Translate")
        self.translate_btn.setObjectName("TransBtn")
        self.translate_btn.setFixedHeight(32)
        self.translate_btn.clicked.connect(self._run_translate)
        action_row.addWidget(self.translate_btn)

        self._backend_lbl = QLabel("checking…")
        self._backend_lbl.setStyleSheet(
            f"color:{D['muted']};font-size:10px;padding:1px 7px;"
        )
        action_row.addWidget(self._backend_lbl)
        action_row.addStretch()
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet(f"color:{D['muted']};font-size:11px;")
        action_row.addWidget(self._status_lbl)
        card_lay.addLayout(action_row)

        # Result header
        res_hdr = QHBoxLayout()
        res_lbl = QLabel("Translation:")
        res_lbl.setStyleSheet(f"color:{D['muted']};font-size:11px;font-weight:600;")
        res_hdr.addWidget(res_lbl)
        res_hdr.addStretch()
        self._copy_btn = QPushButton("📋 Copy")
        self._copy_btn.setObjectName("SmallBtn")
        self._copy_btn.setFixedHeight(22)
        self._copy_btn.clicked.connect(self._copy)
        res_hdr.addWidget(self._copy_btn)
        self._insert_btn = QPushButton("➡  Insert into Chat")
        self._insert_btn.setObjectName("InsertBtn")
        self._insert_btn.setFixedHeight(22)
        self._insert_btn.clicked.connect(self._insert)
        res_hdr.addWidget(self._insert_btn)
        card_lay.addLayout(res_hdr)

        # Result box — compact fixed height, scrollable
        self.result_box = QTextEdit()
        self.result_box.setPlaceholderText("Translation will appear here…")
        self.result_box.setReadOnly(True)
        self.result_box.setFixedHeight(72)   # matches source box height
        card_lay.addWidget(self.result_box)

        root.addWidget(self._card)
        self._card.setVisible(not self._collapsed)

    # ── Backend badge ─────────────────────────────────────────────────────────
    def _set_backend_badge(self, backend: str, idle: bool = False, lt_offline: bool = False):
        if backend == TR.BACKEND_LIBRETRANSLATE:
            label = "● LibreTranslate" + ("  ready" if idle else "  used")
            self._backend_lbl.setStyleSheet(_BADGE_LIBRE)
        elif backend == TR.BACKEND_GOOGLE:
            if idle and lt_offline:
                label = "● Google (fallback)  — start LibreTranslate in Settings"
            elif idle:
                label = "● Google Translate  (configured)"
            else:
                label = "● Google Translate  used"
            self._backend_lbl.setStyleSheet(_BADGE_GOOGLE)
        else:
            label = "● Error"
            self._backend_lbl.setStyleSheet(_BADGE_ERROR)
        self._backend_lbl.setText(label)

    # ── Toggle ────────────────────────────────────────────────────────────────
    def _toggle(self, checked: bool):
        self._card.setVisible(checked)
        arrow = "▾" if checked else "▸"
        self._toggle_btn.setText(f"🌐  Translate  {arrow}")

    # ── Public API ───────────────────────────────────────────────────────────
    def set_source_text(self, text: str):
        """Pre-fill the source box (called after OCR completes)."""
        self.source_box.setPlainText(text)
        if not self._toggle_btn.isChecked():
            self._toggle_btn.setChecked(True)
            self._toggle(True)

    # ── Actions ───────────────────────────────────────────────────────────────
    def _clear_source(self):
        self.source_box.clear()
        self.result_box.clear()
        self._status_lbl.setText("")

    def _run_translate(self):
        text = self.source_box.toPlainText().strip()
        if not text:
            self._status_lbl.setText("⚠ No text to translate.")
            return
        if self._worker and self._worker.isRunning():
            return
        src_name = self.source_combo.currentText()
        tgt_name = self.target_combo.currentText()
        src = TR.name_to_code(src_name)
        tgt = TR.name_to_code(tgt_name)
        self.translate_btn.setEnabled(False)
        self.result_box.clear()
        self._status_lbl.setText("Translating…")
        self._backend_lbl.setText("…")
        self._backend_lbl.setStyleSheet(f"color:{D['muted']};font-size:10px;padding:1px 7px;")
        self._worker = _TranslateWorker(text, src, tgt)
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_done(self, text: str, backend: str):
        self.result_box.setPlainText(text)
        self._status_lbl.setText("✓ Done")
        self._set_backend_badge(backend, idle=False)
        self.translate_btn.setEnabled(True)

    def _on_error(self, msg: str, backend: str):
        self.result_box.setPlainText(msg)
        self._status_lbl.setText("✗ Error")
        self._set_backend_badge("error", idle=False)
        self.translate_btn.setEnabled(True)

    def _copy(self):
        txt = self.result_box.toPlainText()
        if txt:
            QApplication.clipboard().setText(txt)
            self._copy_btn.setText("✅ Copied!")
            QTimer.singleShot(1500, lambda: self._copy_btn.setText("📋 Copy"))

    def _insert(self):
        txt = self.result_box.toPlainText().strip()
        if txt:
            self.text_ready.emit(txt)
            self._status_lbl.setText("✓ Sent to chat.")
