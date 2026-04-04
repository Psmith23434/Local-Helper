"""OCR Widget — EasyOCR + screen-snip panel for the main app.

Can be embedded as a standalone tab (OCRWidget) or opened as a dialog.
The `text_ready` signal emits the extracted text so chat_panel can
insert it directly into the input box.
"""

# ── CRITICAL: pre-load torch c10.dll at module import time ───────────────────
import platform as _plt
if _plt.system() == "Windows":
    import ctypes as _ct, os as _os
    from importlib.util import find_spec as _fs
    try:
        _spec = _fs("torch")
        if _spec and _spec.origin:
            _dll = _os.path.join(_os.path.dirname(_spec.origin), "lib", "c10.dll")
            if _os.path.exists(_dll):
                _ct.CDLL(_os.path.normpath(_dll))
    except Exception:
        pass
# ─────────────────────────────────────────────────────────────────────────────

import os
import io

import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QFileDialog, QApplication, QProgressBar,
    QFrame, QCheckBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRect, QPoint, QSize, QTimer
from PyQt5.QtGui  import QPixmap, QColor, QPainter, QPen, QScreen

# ── Colour tokens (match chat_panel dark theme) ─────────────────────────────
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
    "snip_bg":   "#1a3a2a",
    "snip_fg":   "#60c090",
    "snip_bd":   "#2a5a3a",
}

OCR_QSS = f"""
QWidget#OCRWidget, QWidget#OCRWidget * {{
    background: {D['bg']};
    color: {D['text']};
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}}
QFrame#Card {{
    background: {D['surface']};
    border: 1px solid {D['border']};
    border-radius: 10px;
}}
QPushButton {{
    background: {D['surface2']};
    color: {D['text']};
    border: 1px solid {D['border']};
    border-radius: 7px;
    padding: 7px 16px;
}}
QPushButton:hover  {{ background: #222; border-color: #444; }}
QPushButton:pressed{{ background: #2a2a2a; }}
QPushButton#Primary {{
    background: {D['accent']};
    color: #fff;
    border: none;
    font-weight: 700;
}}
QPushButton#Primary:hover  {{ background: {D['accent2']}; }}
QPushButton#Primary:pressed{{ background: #4a3faa; }}
QPushButton#Snip {{
    background: {D['snip_bg']};
    color: {D['snip_fg']};
    border: 1px solid {D['snip_bd']};
    font-weight: 600;
}}
QPushButton#Snip:hover  {{ background: #1e4a30; border-color: #3a7a50; }}
QPushButton#Snip:pressed{{ background: #163020; }}
QPushButton#Danger {{
    background: #3a1a1a;
    color: {D['red']};
    border: 1px solid #5a2a2a;
}}
QPushButton#Danger:hover {{ background: #4a2020; }}
QPushButton#InsertBtn {{
    background: #1a2a3a;
    color: #60a8e0;
    border: 1px solid #2a4a6a;
    font-weight: 600;
}}
QPushButton#InsertBtn:hover {{ background: #1e3a4a; border-color: #3a6a9a; }}
QTextEdit {{
    background: {D['surface2']};
    color: {D['text']};
    border: 1px solid {D['border']};
    border-radius: 7px;
    padding: 8px;
    font-family: Consolas, monospace;
    font-size: 12px;
}}
QCheckBox {{
    color: {D['muted']};
    font-size: 12px;
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 15px; height: 15px;
    border: 1px solid {D['border']};
    border-radius: 4px;
    background: {D['surface2']};
}}
QCheckBox::indicator:checked {{ background: {D['accent']}; border-color: {D['accent']}; }}
QProgressBar {{
    background: {D['surface2']};
    border: none;
    border-radius: 4px;
    height: 6px;
}}
QProgressBar::chunk {{ background: {D['accent']}; border-radius: 4px; }}
"""

# ── Language definitions ─────────────────────────────────────────────────────
LANGS = [
    ("Auto",   ["en", "de"]),
    ("EN",     ["en"]),
    ("DE",     ["de"]),
    ("FR",     ["fr"]),
    ("ES",     ["es"]),
    ("IT",     ["it"]),
    ("NL",     ["nl"]),
    ("PT",     ["pt"]),
    ("PL",     ["pl"]),
    ("CS",     ["cs"]),
    ("SV",     ["sv"]),
    ("RU ⚠",   ["ru", "en"]),
]


# ── OCR worker ───────────────────────────────────────────────────────────────
class OCRWorker(QThread):
    finished = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, source, langs, use_gpu):
        super().__init__()
        self.source  = source
        self.langs   = langs
        self.use_gpu = use_gpu

    def run(self):
        try:
            import easyocr
            from PIL import Image
            reader  = easyocr.Reader(self.langs, gpu=self.use_gpu)
            if isinstance(self.source, str):
                img = np.array(Image.open(self.source).convert("RGB"))
            else:
                img = np.array(self.source.convert("RGB"))
            results = reader.readtext(img, detail=0, paragraph=True)
            self.finished.emit("\n".join(results) if results else "[No text detected]")
        except ImportError:
            self.error.emit("easyocr not installed.\nRun: pip install easyocr")
        except Exception as e:
            self.error.emit(str(e))


# ── HiDPI-safe QPixmap → PIL ────────────────────────────────────────────────
def _qpixmap_to_pil(pixmap):
    from PIL import Image
    qimg   = pixmap.toImage().convertToFormat(pixmap.toImage().Format_RGB888)
    w, h   = qimg.width(), qimg.height()
    stride = qimg.bytesPerLine()
    ptr    = qimg.bits()
    ptr.setsize(h * stride)
    arr = np.frombuffer(ptr, dtype=np.uint8).reshape((h, stride))
    arr = arr[:, : w * 3].reshape((h, w, 3)).copy()
    return Image.fromarray(arr, "RGB")


# ── Screen-snip overlay ─────────────────────────────────────────────────────
class SnipOverlay(QWidget):
    snipped   = pyqtSignal(object)   # PIL Image
    cancelled = pyqtSignal()

    def __init__(self, screenshot: QPixmap, dpr: float):
        super().__init__()
        self._screenshot = screenshot
        self._dpr        = dpr
        self._origin     = QPoint()
        self._rect       = QRect()
        self._drawing    = False

        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setCursor(Qt.CrossCursor)

        desktop = QApplication.desktop()
        self.setGeometry(desktop.geometry())
        self.show()
        self.raise_()
        self.activateWindow()

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 120))
        if not self._rect.isNull():
            p.setCompositionMode(QPainter.CompositionMode_Clear)
            p.fillRect(self._rect.normalized(), QColor(0, 0, 0, 0))
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)
            p.setPen(QPen(QColor(124, 106, 247), 2))
            p.drawRect(self._rect.normalized())
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        p.setPen(QColor(200, 200, 200))
        p.drawText(
            self.rect().adjusted(0, 20, 0, 0),
            Qt.AlignHCenter | Qt.AlignTop,
            "Draw a rectangle to snip  —  Esc to cancel",
        )

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
            self.cancelled.emit()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._origin  = e.pos()
            self._rect    = QRect(self._origin, QSize())
            self._drawing = True

    def mouseMoveEvent(self, e):
        if self._drawing:
            self._rect = QRect(self._origin, e.pos()).normalized()
            self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self._drawing:
            self._drawing = False
            logical_rect  = QRect(self._origin, e.pos()).normalized()
            self.close()
            if logical_rect.width() < 4 or logical_rect.height() < 4:
                self.cancelled.emit()
                return
            dpr = self._dpr
            phys = QRect(
                int(logical_rect.x()      * dpr),
                int(logical_rect.y()      * dpr),
                int(logical_rect.width()  * dpr),
                int(logical_rect.height() * dpr),
            )
            self.snipped.emit(_qpixmap_to_pil(self._screenshot.copy(phys)))


# ── Drop zone label ─────────────────────────────────────────────────────────
class _DropZone(QLabel):
    file_dropped = pyqtSignal(str)
    EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff"}

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(120)
        self._idle()

    def _idle(self):
        self.setPixmap(QPixmap())
        self.setText("\n\U0001f5bc  Drop image here  /  Browse  /  Snip\n")
        self.setStyleSheet(
            f"QLabel{{border:2px dashed {D['border']};border-radius:10px;"
            f"background:{D['surface2']};color:{D['muted']};font-size:12px;}}"
        )

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.setStyleSheet(
                f"QLabel{{border:2px dashed {D['accent']};border-radius:10px;"
                f"background:#221a33;color:#a080e0;font-size:12px;}}"
            )

    def dragLeaveEvent(self, _): self._idle()

    def dropEvent(self, e):
        self._idle()
        urls = e.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if any(path.lower().endswith(x) for x in self.EXTS):
                self.file_dropped.emit(path)

    def show_file(self, path):
        pix = QPixmap(path).scaledToWidth(360, Qt.SmoothTransformation)
        if pix.height() > 120: pix = pix.scaledToHeight(120, Qt.SmoothTransformation)
        self.setText("")
        self.setStyleSheet(
            f"QLabel{{border:1px solid {D['border']};border-radius:10px;"
            f"background:{D['surface2']};padding:4px;}}"
        )
        self.setPixmap(pix)

    def show_pil(self, pil_img):
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        pix = QPixmap()
        pix.loadFromData(buf.getvalue())
        pix = pix.scaledToWidth(360, Qt.SmoothTransformation)
        if pix.height() > 120: pix = pix.scaledToHeight(120, Qt.SmoothTransformation)
        self.setText("")
        self.setStyleSheet(
            f"QLabel{{border:1px solid {D['snip_bd']};border-radius:10px;"
            f"background:{D['snip_bg']};padding:4px;}}"
        )
        self.setPixmap(pix)

    def reset(self): self._idle()


# ── Language bar ────────────────────────────────────────────────────────────
class _LangBar(QWidget):
    def __init__(self):
        super().__init__()
        self._selected = ["en", "de"]
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lbl = QLabel("Lang:")
        lbl.setStyleSheet(f"color:{D['muted']};font-size:11px;min-width:34px;")
        lay.addWidget(lbl)
        self._btns = {}
        for label, codes in LANGS:
            b = QPushButton(label)
            b.setCheckable(True)
            b.setChecked(label == "Auto")
            b.setFixedHeight(22)
            ru = label.startswith("RU")
            b.setStyleSheet(
                f"QPushButton{{background:{D['surface2']};color:{'#c07040' if ru else D['muted']};"
                f"border:1px solid {'#5a3a20' if ru else D['border']};"
                f"border-radius:5px;font-size:10px;padding:0 7px;}}"
                f"QPushButton:checked{{background:{'#9a5020' if ru else D['accent']};"
                f"color:#fff;border-color:{'#9a5020' if ru else D['accent']};}}"
                f"QPushButton:hover{{background:#333;color:{D['text']};}}"
            )
            b.clicked.connect(lambda _, c=codes, btn=b: self._pick(c, btn))
            lay.addWidget(b)
            self._btns[label] = b
        lay.addStretch()

    def _pick(self, codes, btn):
        self._selected = codes
        for b in self._btns.values(): b.setChecked(False)
        btn.setChecked(True)

    def get(self): return self._selected


# ═════════════════════════════════════════════════════════════════════════════
# Main OCRWidget — embed as a tab or instantiate directly
# ═════════════════════════════════════════════════════════════════════════════
class OCRWidget(QWidget):
    """Full OCR panel.  `text_ready` emits extracted text (for chat integration)."""
    text_ready = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("OCRWidget")
        self.setStyleSheet(OCR_QSS)
        self._image_path = None
        self._snip_image = None
        self._worker     = None
        self._overlay    = None
        self._build_ui()
        self._detect_gpu()

    # ── GPU probe ───────────────────────────────────────────────────────────
    def _detect_gpu(self):
        try:
            import torch
            if torch.cuda.is_available():
                name = torch.cuda.get_device_name(0)
                self.gpu_check.setText(f"Use GPU  —  {name}")
                self.gpu_check.setEnabled(True)
                self.gpu_check.setChecked(True)
                self.gpu_check.setStyleSheet(
                    f"color:{D['green']};font-size:12px;spacing:6px;"
                )
            else:
                self.gpu_check.setText("GPU not available (CUDA not found)")
                self.gpu_check.setEnabled(False)
        except Exception:
            self.gpu_check.setText("GPU N/A (torch not installed)")
            self.gpu_check.setEnabled(False)

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        hdr = QHBoxLayout()
        title = QLabel("🔍  OCR — Extract Text from Images")
        title.setStyleSheet(f"color:{D['text']};font-size:14px;font-weight:700;")
        hdr.addWidget(title)
        hdr.addStretch()
        root.addLayout(hdr)

        hint = QLabel(
            "Drop an image, browse a file, or snip the screen.  "
            "Extracted text can be inserted directly into the chat."
        )
        hint.setStyleSheet(f"color:{D['muted']};font-size:11px;")
        hint.setWordWrap(True)
        root.addWidget(hint)

        drop_card = QFrame()
        drop_card.setObjectName("Card")
        dc = QVBoxLayout(drop_card)
        dc.setContentsMargins(12, 12, 12, 12)
        dc.setSpacing(8)

        self.drop_zone = _DropZone()
        self.drop_zone.file_dropped.connect(self._load_file)
        dc.addWidget(self.drop_zone)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        self._browse_btn = QPushButton("📂  Browse")
        self._browse_btn.clicked.connect(self._browse)
        self._snip_btn   = QPushButton("✂️  Snip Screen")
        self._snip_btn.setObjectName("Snip")
        self._snip_btn.clicked.connect(self._start_snip)
        self._clear_btn  = QPushButton("✕  Clear")
        self._clear_btn.setObjectName("Danger")
        self._clear_btn.clicked.connect(self._clear)
        for w in (self._browse_btn, self._snip_btn, self._clear_btn):
            w.setFixedHeight(30)
            btns.addWidget(w)
        btns.addStretch()
        dc.addLayout(btns)
        root.addWidget(drop_card)

        self.lang_bar = _LangBar()
        root.addWidget(self.lang_bar)

        gpu_row = QHBoxLayout()
        self.gpu_check = QCheckBox("Use GPU  —  detecting…")
        self.gpu_check.setChecked(False)
        self.gpu_check.setEnabled(False)
        gpu_row.addWidget(self.gpu_check)
        gpu_row.addStretch()
        root.addLayout(gpu_row)

        self._run_btn = QPushButton("⚡  Extract Text")
        self._run_btn.setObjectName("Primary")
        self._run_btn.setFixedHeight(38)
        self._run_btn.clicked.connect(self._run)
        root.addWidget(self._run_btn)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setFixedHeight(6)
        self._progress.hide()
        root.addWidget(self._progress)

        self._status = QLabel("No image loaded.")
        self._status.setStyleSheet(f"color:{D['muted']};font-size:11px;")
        root.addWidget(self._status)

        result_card = QFrame()
        result_card.setObjectName("Card")
        rc = QVBoxLayout(result_card)
        rc.setContentsMargins(12, 10, 12, 10)
        rc.setSpacing(6)

        res_hdr = QHBoxLayout()
        res_lbl = QLabel("Extracted Text")
        res_lbl.setStyleSheet(f"color:{D['muted']};font-size:11px;font-weight:600;")
        res_hdr.addWidget(res_lbl)
        res_hdr.addStretch()

        self._copy_btn = QPushButton("📋 Copy")
        self._copy_btn.setFixedHeight(26)
        self._copy_btn.setStyleSheet(
            f"QPushButton{{background:{D['surface2']};color:{D['muted']};"
            f"border:1px solid {D['border']};border-radius:5px;font-size:11px;padding:0 10px;}}"
            f"QPushButton:hover{{background:#333;color:{D['text']};}}"
        )
        self._copy_btn.clicked.connect(self._copy)
        res_hdr.addWidget(self._copy_btn)

        self._insert_btn = QPushButton("➡  Insert into Chat")
        self._insert_btn.setObjectName("InsertBtn")
        self._insert_btn.setFixedHeight(26)
        self._insert_btn.clicked.connect(self._insert)
        res_hdr.addWidget(self._insert_btn)

        rc.addLayout(res_hdr)

        self._result_box = QTextEdit()
        self._result_box.setPlaceholderText("OCR result will appear here…")
        self._result_box.setMinimumHeight(160)
        rc.addWidget(self._result_box)
        root.addWidget(result_card)

    # ── File handling
    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.tiff)"
        )
        if path: self._load_file(path)

    def _load_file(self, path):
        self._image_path = path
        self._snip_image = None
        self.drop_zone.show_file(path)
        self._status.setText(f"Loaded: {os.path.basename(path)}")
        self._result_box.clear()

    def _clear(self):
        self._image_path = None
        self._snip_image = None
        self.drop_zone.reset()
        self._result_box.clear()
        self._status.setText("No image loaded.")

    # ── Snip — FIX: hide window first, wait 150 ms, THEN grab screen
    def _start_snip(self):
        top = self.window()
        top.hide()
        QApplication.processEvents()
        # Wait for Windows to actually repaint the desktop behind the window
        # before grabbing the screen — avoids the black-frame glitch.
        QTimer.singleShot(150, lambda: self._grab_and_snip(top))

    def _grab_and_snip(self, top):
        screen      = QApplication.primaryScreen()
        screenshot  = screen.grabWindow(0)
        dpr         = screen.devicePixelRatio()
        self._overlay = SnipOverlay(screenshot, dpr)
        self._overlay.snipped.connect(self._on_snipped)
        self._overlay.cancelled.connect(lambda: self._on_snip_cancelled(top))

    def _on_snipped(self, pil_img):
        self.window().show()
        self._snip_image = pil_img
        self._image_path = None
        self.drop_zone.show_pil(pil_img)
        self._status.setText(f"Snip: {pil_img.width}×{pil_img.height}px — running OCR…")
        self._result_box.clear()
        self._run()

    def _on_snip_cancelled(self, top=None):
        if top is not None:
            top.show()
        else:
            self.window().show()
        self._status.setText("Snip cancelled.")

    # ── OCR
    def _run(self):
        source = self._snip_image if self._snip_image else self._image_path
        if source is None:
            self._status.setText("⚠  Load an image or snip the screen first.")
            return
        if self._worker and self._worker.isRunning():
            return
        langs    = self.lang_bar.get()
        use_gpu  = self.gpu_check.isChecked() and self.gpu_check.isEnabled()
        mode_str = "GPU" if use_gpu else "CPU"
        self._run_btn.setEnabled(False)
        self._progress.show()
        self._status.setText(f"Running EasyOCR [{mode_str}] ({', '.join(langs)})…")
        self._worker = OCRWorker(source, langs, use_gpu)
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_done(self, text):
        self._result_box.setPlainText(text)
        self._status.setText(f"✓ Done — {len(text.split())} words detected")
        self._finish()

    def _on_error(self, msg):
        self._result_box.setPlainText(f"[Error]\n{msg}")
        self._status.setText(f"✗ Error — {msg[:80]}")
        self._finish()

    def _finish(self):
        self._progress.hide()
        self._run_btn.setEnabled(True)

    # ── Actions
    def _copy(self):
        txt = self._result_box.toPlainText()
        if txt:
            QApplication.clipboard().setText(txt)
            self._copy_btn.setText("✅ Copied!")
            QTimer.singleShot(1500, lambda: self._copy_btn.setText("📋 Copy"))

    def _insert(self):
        txt = self._result_box.toPlainText().strip()
        if txt:
            self.text_ready.emit(txt)
            self._status.setText("✓ Text sent to Chat input.")

    # ── Public API for chat_panel inline snip
    def start_snip_for_chat(self, callback, use_gpu: bool = False):
        """Called by General Chat snip button. Hides window, waits, grabs, snips."""
        top = self.window()
        top.hide()
        QApplication.processEvents()
        QTimer.singleShot(150, lambda: self._grab_for_chat(top, callback, use_gpu))

    def _grab_for_chat(self, top, callback, use_gpu: bool):
        screen     = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        dpr        = screen.devicePixelRatio()
        overlay    = SnipOverlay(screenshot, dpr)

        def _got(pil_img):
            top.show()
            callback(pil_img, use_gpu)

        def _cancel():
            top.show()

        overlay.snipped.connect(_got)
        overlay.cancelled.connect(_cancel)
        self._overlay = overlay
