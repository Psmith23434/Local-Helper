import sys
import os

# ── CRITICAL: Pre-load torch c10.dll BEFORE PyQt5 imports ──────────────────────────
# PyTorch 2.9+ on Windows crashes with [WinError 1114] if PyQt is imported first.
# Fix: https://github.com/pytorch/pytorch/issues/166628
import platform
if platform.system() == "Windows":
    import ctypes
    from importlib.util import find_spec
    try:
        if (spec := find_spec("torch")) and spec.origin and os.path.exists(
            dll_path := os.path.join(os.path.dirname(spec.origin), "lib", "c10.dll")
        ):
            ctypes.CDLL(os.path.normpath(dll_path))
    except Exception:
        pass

import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFileDialog,
    QProgressBar, QFrame, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QDragEnterEvent, QDropEvent

# ── Dark theme ──────────────────────────────────────────────────────────────────

STYLE = """
QWidget {
    background-color: #1a1a1a;
    color: #e0e0e0;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QFrame#card {
    background-color: #242424;
    border: 1px solid #333;
    border-radius: 10px;
}
QPushButton {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3a3a3a;
    border-radius: 7px;
    padding: 8px 18px;
}
QPushButton:hover { background-color: #363636; border-color: #555; }
QPushButton:pressed { background-color: #444; }
QPushButton#primary {
    background-color: #6c3fc5;
    color: #fff;
    border: none;
    font-weight: 600;
}
QPushButton#primary:hover { background-color: #7a4dd4; }
QPushButton#primary:pressed { background-color: #5a34a8; }
QPushButton#danger {
    background-color: #3a1a1a;
    color: #e06060;
    border: 1px solid #5a2a2a;
}
QPushButton#danger:hover { background-color: #4a2020; }
QTextEdit {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border: 1px solid #333;
    border-radius: 7px;
    padding: 8px;
    font-family: Consolas, monospace;
    font-size: 12px;
}
QCheckBox { color: #aaa; font-size: 12px; spacing: 6px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #555; border-radius: 4px;
    background: #2a2a2a;
}
QCheckBox::indicator:checked { background: #6c3fc5; border-color: #6c3fc5; }
QLabel#status { color: #888; font-size: 11px; }
QLabel#title_lbl { color: #e0e0e0; font-size: 15px; font-weight: 600; }
QLabel#hint { color: #555; font-size: 11px; }
QProgressBar {
    background-color: #2a2a2a; border: none;
    border-radius: 4px; height: 6px;
}
QProgressBar::chunk { background-color: #6c3fc5; border-radius: 4px; }
"""

# ── Language definitions ──────────────────────────────────────────────────────────────
LANGS = [
    ("Auto",  ["en", "de"]),
    ("EN",    ["en"]),
    ("DE",    ["de"]),
    ("FR",    ["fr"]),
    ("ES",    ["es"]),
    ("IT",    ["it"]),
    ("NL",    ["nl"]),
    ("PT",    ["pt"]),
    ("PL",    ["pl"]),
    ("CS",    ["cs"]),
    ("SV",    ["sv"]),
    ("RU ⚠",  ["ru", "en"]),  # Cyrillic — isolated reader
]

# ── OCR worker thread ─────────────────────────────────────────────────────

class OCRWorker(QThread):
    finished = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, image_path, langs, use_gpu):
        super().__init__()
        self.image_path = image_path
        self.langs = langs
        self.use_gpu = use_gpu

    def run(self):
        try:
            import easyocr
            from PIL import Image
            reader = easyocr.Reader(self.langs, gpu=self.use_gpu)
            img = np.array(Image.open(self.image_path).convert("RGB"))
            results = reader.readtext(img, detail=0, paragraph=True)
            self.finished.emit("\n".join(results) if results else "[No text detected]")
        except ImportError:
            self.error.emit("easyocr not installed.\nRun: pip install easyocr")
        except Exception as e:
            self.error.emit(str(e))

# ── Drop zone ───────────────────────────────────────────────────────────────────

class DropLabel(QLabel):
    file_dropped = pyqtSignal(str)
    EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff"}

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(160)
        self._set_idle()

    def _set_idle(self):
        self.setPixmap(QPixmap())
        self.setText("\n\n\U0001f5bc  Drop an image here\nor click Browse\n")
        self.setStyleSheet(
            "QLabel{border:2px dashed #3a3a3a;border-radius:10px;"
            "background:#1e1e1e;color:#555;font-size:13px;}"
        )

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.setStyleSheet(
                "QLabel{border:2px dashed #6c3fc5;border-radius:10px;"
                "background:#221a33;color:#a080e0;font-size:13px;}"
            )

    def dragLeaveEvent(self, _):
        self._set_idle()

    def dropEvent(self, e: QDropEvent):
        self._set_idle()
        urls = e.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if any(path.lower().endswith(x) for x in self.EXTS):
                self.file_dropped.emit(path)

    def show_preview(self, path):
        pix = QPixmap(path).scaledToWidth(380, Qt.SmoothTransformation)
        if pix.height() > 160:
            pix = pix.scaledToHeight(160, Qt.SmoothTransformation)
        self.setText("")
        self.setStyleSheet(
            "QLabel{border:1px solid #333;border-radius:10px;"
            "background:#1e1e1e;padding:4px;}"
        )
        self.setPixmap(pix)

# ── Language bar ───────────────────────────────────────────────────────────────────

class LangBar(QWidget):
    def __init__(self):
        super().__init__()
        self._selected = ["en", "de"]
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lbl = QLabel("Language:")
        lbl.setStyleSheet("color:#888;font-size:11px;min-width:62px;")
        lay.addWidget(lbl)
        self._btns = {}
        for label, codes in LANGS:
            b = QPushButton(label)
            b.setCheckable(True)
            b.setChecked(label == "Auto")
            b.setFixedHeight(24)
            ru = label.startswith("RU")
            b.setStyleSheet(
                f"QPushButton{{background:#2a2a2a;color:{'#c07040' if ru else '#888'};"
                f"border:1px solid {'#5a3a20' if ru else '#333'};"
                f"border-radius:5px;font-size:10px;padding:0 7px;}}"
                f"QPushButton:checked{{background:{'#9a5020' if ru else '#6c3fc5'};"
                f"color:#fff;border-color:{'#9a5020' if ru else '#6c3fc5'};}}"
                f"QPushButton:hover{{background:#333;color:#e0e0e0;}}"
            )
            b.clicked.connect(lambda _, c=codes, btn=b: self._pick(c, btn))
            lay.addWidget(b)
            self._btns[label] = b
        lay.addStretch()

    def _pick(self, codes, clicked_btn):
        self._selected = codes
        for b in self._btns.values():
            b.setChecked(False)
        clicked_btn.setChecked(True)

    def get_langs(self):
        return self._selected

# ── Main window ───────────────────────────────────────────────────────────────────

class EasyOCRTester(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EasyOCR Tester")
        self.setMinimumSize(560, 660)
        self._image_path = None
        self._worker = None
        self._build_ui()
        self._detect_gpu()

    def _detect_gpu(self):
        try:
            import torch
            if torch.cuda.is_available():
                name = torch.cuda.get_device_name(0)
                self.gpu_check.setText(f"Use GPU  —  {name}")
                self.gpu_check.setEnabled(True)
                self.gpu_check.setChecked(True)
                self.gpu_check.setStyleSheet(
                    "color:#6daa45;font-size:12px;spacing:6px;"
                    "QCheckBox::indicator{width:16px;height:16px;border:1px solid #555;"
                    "border-radius:4px;background:#2a2a2a;}"
                    "QCheckBox::indicator:checked{background:#6c3fc5;border-color:#6c3fc5;}"
                )
            else:
                self.gpu_check.setText("Use GPU  —  not available (CUDA not found)")
                self.gpu_check.setEnabled(False)
        except ImportError:
            self.gpu_check.setText("Use GPU  —  torch not installed")
            self.gpu_check.setEnabled(False)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(18, 18, 18, 18)

        title = QLabel("EasyOCR Tester")
        title.setObjectName("title_lbl")
        root.addWidget(title)
        hint = QLabel("Test EasyOCR on any image — drop an image or use Browse")
        hint.setObjectName("hint")
        root.addWidget(hint)

        drop_card = QFrame(); drop_card.setObjectName("card")
        dc_lay = QVBoxLayout(drop_card); dc_lay.setContentsMargins(12, 12, 12, 12)
        self.drop_zone = DropLabel()
        self.drop_zone.file_dropped.connect(self._load_image)
        dc_lay.addWidget(self.drop_zone)
        browse_row = QHBoxLayout()
        browse_btn = QPushButton("\U0001f4c2  Browse Image")
        browse_btn.clicked.connect(self._browse)
        clear_btn = QPushButton("✕  Clear")
        clear_btn.setObjectName("danger")
        clear_btn.clicked.connect(self._clear)
        browse_row.addWidget(browse_btn)
        browse_row.addWidget(clear_btn)
        browse_row.addStretch()
        dc_lay.addLayout(browse_row)
        root.addWidget(drop_card)

        self.lang_bar = LangBar()
        root.addWidget(self.lang_bar)

        self.gpu_check = QCheckBox("Use GPU  —  detecting...")
        self.gpu_check.setChecked(False)
        self.gpu_check.setEnabled(False)
        root.addWidget(self.gpu_check)

        self.run_btn = QPushButton("⚡  Extract Text")
        self.run_btn.setObjectName("primary")
        self.run_btn.setFixedHeight(40)
        self.run_btn.clicked.connect(self._run_ocr)
        root.addWidget(self.run_btn)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        root.addWidget(self.progress)
        self.status_lbl = QLabel("No image loaded.")
        self.status_lbl.setObjectName("status")
        root.addWidget(self.status_lbl)

        result_card = QFrame(); result_card.setObjectName("card")
        rc_lay = QVBoxLayout(result_card)
        rc_lay.setContentsMargins(12, 12, 12, 12)
        rc_lay.setSpacing(6)
        res_hdr = QHBoxLayout()
        res_lbl = QLabel("Extracted Text")
        res_lbl.setStyleSheet("font-weight:600;font-size:12px;color:#aaa;")
        copy_btn = QPushButton("\U0001f4cb Copy")
        copy_btn.setFixedHeight(26)
        copy_btn.setStyleSheet(
            "QPushButton{background:#2a2a2a;color:#888;border:1px solid #333;"
            "border-radius:5px;font-size:11px;padding:0 10px;}"
            "QPushButton:hover{background:#333;color:#e0e0e0;}"
        )
        copy_btn.clicked.connect(self._copy)
        res_hdr.addWidget(res_lbl)
        res_hdr.addStretch()
        res_hdr.addWidget(copy_btn)
        rc_lay.addLayout(res_hdr)
        self.result_box = QTextEdit()
        self.result_box.setPlaceholderText("OCR result will appear here…")
        self.result_box.setMinimumHeight(180)
        rc_lay.addWidget(self.result_box)
        root.addWidget(result_card)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.tiff)"
        )
        if path:
            self._load_image(path)

    def _load_image(self, path):
        self._image_path = path
        self.drop_zone.show_preview(path)
        self.status_lbl.setText(f"Loaded: {os.path.basename(path)}")
        self.result_box.clear()

    def _clear(self):
        self._image_path = None
        self.drop_zone._set_idle()
        self.result_box.clear()
        self.status_lbl.setText("No image loaded.")

    def _run_ocr(self):
        if not self._image_path:
            self.status_lbl.setText("⚠  Please load an image first.")
            return
        if self._worker and self._worker.isRunning():
            return
        langs = self.lang_bar.get_langs()
        use_gpu = self.gpu_check.isChecked() and self.gpu_check.isEnabled()
        mode_str = "GPU" if use_gpu else "CPU"
        self.run_btn.setEnabled(False)
        self.progress.show()
        self.status_lbl.setText(
            f"Running EasyOCR [{mode_str}] ({', '.join(langs)}) — first run loads model…"
        )
        self._worker = OCRWorker(self._image_path, langs, use_gpu)
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_done(self, text):
        self.result_box.setPlainText(text)
        self.status_lbl.setText(f"✓ Done — {len(text.split())} words detected")
        self._finish()

    def _on_error(self, msg):
        self.result_box.setPlainText(f"[Error]\n{msg}")
        self.status_lbl.setText("✗ Error — see result box")
        self._finish()

    def _finish(self):
        self.progress.hide()
        self.run_btn.setEnabled(True)

    def _copy(self):
        txt = self.result_box.toPlainText()
        if txt:
            QApplication.clipboard().setText(txt)
            self.status_lbl.setText("Copied to clipboard.")

# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    win = EasyOCRTester()
    win.show()
    sys.exit(app.exec_())
