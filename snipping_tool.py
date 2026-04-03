"""Integrated snipping tool — fully PyQt5, no tkinter dependency."""

import base64
import io

from PyQt5.QtWidgets import (
    QWidget, QApplication, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFileDialog,
    QButtonGroup, QRadioButton, QDialog, QRubberBand,
    QSizePolicy, QMessageBox
)
from PyQt5.QtCore import Qt, QRect, QSize, QPoint, pyqtSignal
from PyQt5.QtGui import (
    QPixmap, QPainter, QColor, QPen, QCursor, QImage, QIcon
)
from PIL import Image
import keyboard


# ── Helpers ──────────────────────────────────────────────────────────────────

def pil_to_qpixmap(img: Image.Image) -> QPixmap:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    qimg = QImage.fromData(buf.read())
    return QPixmap.fromImage(qimg)


def image_to_base64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ── Fullscreen snip overlay ───────────────────────────────────────────────────

class SnipOverlay(QWidget):
    """Fullscreen semi-transparent overlay — user drags to select a region."""

    snipped = pyqtSignal(object)   # emits PIL Image on completion

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(QCursor(Qt.CrossCursor))
        self.setWindowState(Qt.WindowFullScreen)

        # Grab the full desktop as a background reference
        screen = QApplication.primaryScreen()
        self._bg = screen.grabWindow(0)
        geo = QApplication.desktop().screenGeometry()
        self.setGeometry(geo)

        self._origin = QPoint()
        self._rubber = QRubberBand(QRubberBand.Rectangle, self)
        self.show()

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self._bg)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._rubber.hide()
            self.close()

    def mousePressEvent(self, event):
        self._origin = event.pos()
        self._rubber.setGeometry(QRect(self._origin, QSize()))
        self._rubber.show()

    def mouseMoveEvent(self, event):
        self._rubber.setGeometry(
            QRect(self._origin, event.pos()).normalized()
        )

    def mouseReleaseEvent(self, event):
        rect = QRect(self._origin, event.pos()).normalized()
        self._rubber.hide()
        self.close()
        QApplication.processEvents()

        if rect.width() < 5 or rect.height() < 5:
            return

        # Capture the selected region from the saved background pixmap
        cropped = self._bg.copy(rect)
        buf = io.BytesIO()
        qimg = cropped.toImage()
        w, h = qimg.width(), qimg.height()
        ptr = qimg.bits()
        ptr.setsize(qimg.byteCount())
        pil = Image.frombytes("RGBA", (w, h), bytes(ptr), "raw", "BGRA")
        self.snipped.emit(pil)


# ── Snip toolbar / result window ─────────────────────────────────────────────

SUGGESTED_PROMPTS = [
    "What does this say?",
    "Explain this",
    "Translate this to English",
    "Summarize this",
    "What is wrong with this?",
]

LANGUAGES = [
    ("Auto", "auto"),
    ("EN",   "eng"),
    ("DE",   "deu"),
    ("FR",   "fra"),
    ("ES",   "spa"),
    ("IT",   "ita"),
    ("NL",   "nld"),
    ("PT",   "por"),
    ("RU",   "rus"),
    ("PL",   "pol"),
    ("CS",   "ces"),
    ("SV",   "swe"),
]


class SnipToolbar(QDialog):
    """Post-snip action dialog — Send to AI / OCR / Save / Edit."""

    def __init__(self, image: Image.Image, send_to_chat_callback, parent=None):
        super().__init__(parent, Qt.WindowStaysOnTopHint)
        self.image = image
        self.send_to_chat_callback = send_to_chat_callback
        self._selected_lang = "auto"
        self._ocr_mode = "quick"
        self.setWindowTitle("Snip Toolbar")
        self.setMinimumWidth(520)
        self._build_ui()

    def _build_ui(self):
        from ui.theme import get as T
        from ui.styles import accent_btn_qss
        d = T()
        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(14, 14, 14, 14)

        # Preview
        preview_pix = pil_to_qpixmap(self.image).scaledToWidth(
            490, Qt.SmoothTransformation
        )
        lbl_preview = QLabel()
        lbl_preview.setPixmap(preview_pix)
        lbl_preview.setAlignment(Qt.AlignCenter)
        lbl_preview.setStyleSheet(
            f"border:1px solid {d['border']};border-radius:6px;padding:2px;"
        )
        root.addWidget(lbl_preview)

        # OCR mode toggle
        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)
        mode_lbl = QLabel("OCR Mode:")
        mode_lbl.setStyleSheet(f"color:{d['muted']};font-size:11px;")
        mode_row.addWidget(mode_lbl)
        self.rb_quick = QRadioButton("⚡ Quick (Tesseract)")
        self.rb_ai    = QRadioButton("🤖 AI OCR")
        self.rb_quick.setChecked(True)
        self.rb_quick.toggled.connect(self._toggle_lang_bar)
        mode_group = QButtonGroup(self)
        mode_group.addButton(self.rb_quick)
        mode_group.addButton(self.rb_ai)
        mode_row.addWidget(self.rb_quick)
        mode_row.addWidget(self.rb_ai)
        mode_row.addStretch()
        root.addLayout(mode_row)

        # Language bar
        self.lang_widget = QWidget()
        lang_row = QHBoxLayout(self.lang_widget)
        lang_row.setContentsMargins(0, 0, 0, 0)
        lang_row.setSpacing(4)
        lang_lbl = QLabel("Language:")
        lang_lbl.setStyleSheet(f"color:{d['muted']};font-size:11px;")
        lang_row.addWidget(lang_lbl)
        self._lang_btns = {}
        for label, code in LANGUAGES:
            btn = QPushButton(label)
            btn.setFixedHeight(24)
            btn.setCheckable(True)
            btn.setChecked(code == "auto")
            btn.setStyleSheet(
                f"QPushButton{{background:{d['surface2']};color:{d['muted']};"
                f"border:1px solid {d['border']};border-radius:4px;"
                f"font-size:10px;padding:0 6px;}}"
                f"QPushButton:checked{{background:{d['accent']};color:#fff;border-color:{d['accent']};}}"
                f"QPushButton:hover{{background:{d['surface3']};color:{d['text']};}}"
            )
            btn.clicked.connect(lambda _, c=code: self._select_lang(c))
            lang_row.addWidget(btn)
            self._lang_btns[code] = btn
        lang_row.addStretch()
        root.addWidget(self.lang_widget)

        # Prompt selector
        prompt_row = QHBoxLayout()
        prompt_lbl = QLabel("Prompt:")
        prompt_lbl.setStyleSheet(f"color:{d['muted']};font-size:11px;")
        prompt_row.addWidget(prompt_lbl)
        from PyQt5.QtWidgets import QComboBox
        self.prompt_combo = QComboBox()
        self.prompt_combo.addItems(SUGGESTED_PROMPTS)
        self.prompt_combo.setEditable(True)
        self.prompt_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        prompt_row.addWidget(self.prompt_combo)
        root.addLayout(prompt_row)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        actions = [
            ("📤 Send to AI",    self._send_to_ai),
            ("📝 Extract Text",  self._extract_text),
            ("💾 Save",          self._save),
            ("📋 Copy",          self._copy),
        ]
        for text, fn in actions:
            b = QPushButton(text)
            b.setStyleSheet(accent_btn_qss() if "Send" in text else
                f"QPushButton{{background:{d['surface2']};color:{d['text']};"
                f"border:1px solid {d['border']};border-radius:6px;"
                f"padding:6px 12px;font-size:11px;}}"
                f"QPushButton:hover{{background:{d['surface3']};}}"
            )
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(fn)
            btn_row.addWidget(b)
        btn_row.addStretch()
        root.addLayout(btn_row)

        # OCR result box (hidden until Extract Text is run)
        self.result_lbl = QLabel("")
        self.result_lbl.setStyleSheet(f"color:{d['muted']};font-size:11px;")
        self.result_lbl.hide()
        root.addWidget(self.result_lbl)

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(False)
        self.result_box.setFixedHeight(110)
        self.result_box.setStyleSheet(
            f"QTextEdit{{background:{d['surface2']};color:{d['text']};"
            f"border:1px solid {d['border']};border-radius:6px;"
            f"font-family:Consolas,monospace;font-size:11px;padding:6px;}}"
        )
        self.result_box.hide()
        root.addWidget(self.result_box)

    def _toggle_lang_bar(self, quick_checked: bool):
        self.lang_widget.setVisible(quick_checked)
        self._ocr_mode = "quick" if quick_checked else "ai"

    def _select_lang(self, code: str):
        self._selected_lang = code
        for c, btn in self._lang_btns.items():
            btn.setChecked(c == code)

    def _send_to_ai(self):
        b64 = image_to_base64(self.image)
        prompt = self.prompt_combo.currentText()
        self.send_to_chat_callback(b64, prompt)
        self.accept()

    def _extract_text(self):
        from ocr_tool import run_ocr
        lang = None if self._selected_lang == "auto" else self._selected_lang
        self.result_lbl.setText("Extracting text...")
        self.result_lbl.show()
        self.result_box.hide()
        QApplication.processEvents()
        text = run_ocr(self.image, mode=self._ocr_mode, lang_override=lang)
        self.result_box.setPlainText(text)
        self.result_lbl.setText("Extracted Text (editable):")
        self.result_box.show()
        self.adjustSize()

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Snip", "snip.png",
            "PNG Image (*.png);;JPEG Image (*.jpg)"
        )
        if path:
            self.image.save(path)
            self.result_lbl.setText(f"Saved to {path}")
            self.result_lbl.show()

    def _copy(self):
        pix = pil_to_qpixmap(self.image)
        QApplication.clipboard().setPixmap(pix)
        self.result_lbl.setText("Image copied to clipboard.")
        self.result_lbl.show()


# ── Public API ────────────────────────────────────────────────────────────────

def trigger_snip(parent_widget, send_to_chat_callback):
    """Launch the snip overlay. Called from button click or hotkey."""
    overlay = SnipOverlay()

    def on_snipped(image: Image.Image):
        toolbar = SnipToolbar(image, send_to_chat_callback, parent=parent_widget)
        toolbar.exec_()

    overlay.snipped.connect(on_snipped)


def register_snip_hotkey(root, send_to_chat_callback):
    """Register Ctrl+Shift+C as a global hotkey to trigger the snip overlay."""
    def _trigger():
        from PyQt5.QtCore import QMetaObject, Qt as _Qt
        QMetaObject.invokeMethod(
            root, "_trigger_snip", _Qt.QueuedConnection
        )

    import types
    def _trigger_snip(self):
        trigger_snip(self, getattr(self, "attach_image", lambda b64, p: None))

    root._trigger_snip = types.MethodType(_trigger_snip, root)
    keyboard.add_hotkey("ctrl+shift+c", _trigger)
