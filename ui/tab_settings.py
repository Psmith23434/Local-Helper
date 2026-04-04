"""Settings tab — theme, font size, layout, API config, translation, clear history."""

import sys
import subprocess
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QLineEdit, QSpinBox, QGroupBox, QMessageBox,
    QSlider, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
import database as db
from ui.theme import get as T, set_theme, names as theme_names, name as theme_name
from ui.styles import accent_btn_qss

# Module-level reference to the LibreTranslate background process
_lt_process = None


class SettingsTab(QWidget):
    theme_changed  = pyqtSignal()
    layout_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        d = T()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea{{border:none;background:{d['bg']};}}")

        content = QWidget()
        content.setStyleSheet(f"background:{d['bg']};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(40, 30, 40, 40)
        cl.setSpacing(20)

        # Title
        h = QLabel("⚙️  Settings")
        h.setFont(QFont("Segoe UI", 22, QFont.Bold))
        h.setStyleSheet(f"color:{d['text']};")
        cl.addWidget(h)

        # ── Appearance ───────────────────────────────────────────────────────────
        grp_appear = self._group("Appearance")
        gl = QVBoxLayout(grp_appear)
        gl.setSpacing(10)

        row = QHBoxLayout()
        row.addWidget(self._lbl("Theme"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(theme_names())
        self.theme_combo.setCurrentText(theme_name())
        self.theme_combo.setFixedWidth(180)
        row.addWidget(self.theme_combo)
        row.addStretch()
        btn_apply_theme = QPushButton("Apply")
        btn_apply_theme.setFixedWidth(80)
        btn_apply_theme.clicked.connect(self._apply_theme)
        row.addWidget(btn_apply_theme)
        gl.addLayout(row)

        row2 = QHBoxLayout()
        row2.addWidget(self._lbl("Font size"))
        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setRange(9, 16)
        self.font_slider.setValue(10)
        self.font_slider.setFixedWidth(160)
        self.font_size_lbl = QLabel("10 px")
        self.font_size_lbl.setFixedWidth(40)
        self.font_size_lbl.setStyleSheet(f"color:{d['muted']};")
        self.font_slider.valueChanged.connect(
            lambda v: self.font_size_lbl.setText(f"{v} px")
        )
        row2.addWidget(self.font_slider)
        row2.addWidget(self.font_size_lbl)
        row2.addStretch()
        btn_apply_font = QPushButton("Apply")
        btn_apply_font.setFixedWidth(80)
        btn_apply_font.clicked.connect(self._apply_font)
        row2.addWidget(btn_apply_font)
        gl.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(self._lbl("Layout"))
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["Tabbed", "Sidebar"])
        try:
            from config import GUI_LAYOUT
            self.layout_combo.setCurrentText(GUI_LAYOUT)
        except Exception:
            self.layout_combo.setCurrentText("Tabbed")
        self.layout_combo.setFixedWidth(180)
        row3.addWidget(self.layout_combo)
        row3.addStretch()
        btn_apply_layout = QPushButton("Apply")
        btn_apply_layout.setFixedWidth(80)
        btn_apply_layout.setToolTip("Saves to config.py and closes the app — relaunch to apply")
        btn_apply_layout.clicked.connect(self._apply_layout)
        row3.addWidget(btn_apply_layout)
        gl.addLayout(row3)
        cl.addWidget(grp_appear)

        # ── API / Proxy ─────────────────────────────────────────────────────
        grp_api = self._group("AI Proxy")
        al = QVBoxLayout(grp_api)
        al.setSpacing(10)
        al.addWidget(self._lbl("Base URL"))
        self.api_url = QLineEdit()
        self._load_config_value("BASE_URL", self.api_url)
        al.addWidget(self.api_url)
        al.addWidget(self._lbl("API Key"))
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.Password)
        self._load_config_value("API_KEY", self.api_key)
        al.addWidget(self.api_key)
        al.addWidget(self._lbl("Default Model"))
        self.default_model = QLineEdit()
        self._load_config_value("DEFAULT_MODEL", self.default_model)
        al.addWidget(self.default_model)
        btn_save_api = QPushButton("Save to config.py")
        btn_save_api.setStyleSheet(accent_btn_qss())
        btn_save_api.setFixedWidth(160)
        btn_save_api.clicked.connect(self._save_api)
        al.addWidget(btn_save_api)
        cl.addWidget(grp_api)

        # ── Translation ─────────────────────────────────────────────────────
        grp_trans = self._group("Translation")
        tl = QVBoxLayout(grp_trans)
        tl.setSpacing(12)

        # — Backend selector —
        tl.addWidget(self._lbl(
            "Translation backend  —  LibreTranslate = self-hosted (private, no internet needed);  "
            "Google = always-on online fallback via deep-translator (no key, no account)"
        ))
        backend_row = QHBoxLayout()
        self.backend_combo = QComboBox()
        self.backend_combo.addItems(["LibreTranslate (self-hosted)", "Google Translate (online)"])
        self.backend_combo.setFixedWidth(260)
        # Load current setting
        current_backend = self._read_config_str("TRANSLATE_BACKEND", "libretranslate")
        self.backend_combo.setCurrentIndex(0 if current_backend == "libretranslate" else 1)
        self.backend_combo.currentIndexChanged.connect(self._on_backend_changed)
        backend_row.addWidget(self.backend_combo)
        backend_row.addStretch()
        tl.addLayout(backend_row)

        # — LibreTranslate sub-section (hidden when Google is selected) —
        self._lt_section = QWidget()
        lt_lay = QVBoxLayout(self._lt_section)
        lt_lay.setContentsMargins(0, 0, 0, 0)
        lt_lay.setSpacing(8)

        lt_lay.addWidget(self._lbl(
            "LibreTranslate server URL  —  default: http://localhost:5000  —  "
            "change to your VPS address when ready"
        ))
        self.lt_url = QLineEdit()
        self.lt_url.setPlaceholderText("http://localhost:5000")
        self._load_config_value("LIBRETRANSLATE_URL", self.lt_url)
        lt_lay.addWidget(self.lt_url)

        # Start / Stop LibreTranslate process
        lt_lay.addWidget(self._lbl(
            "Run LibreTranslate locally (Option B — no Docker needed).  "
            "Click Start once; it runs silently in the background until you click Stop or close the app.  "
            "First launch downloads language models (∼1–2 GB) — takes a few minutes."
        ))
        lt_btn_row = QHBoxLayout()
        self._lt_start_btn = QPushButton("▶  Start LibreTranslate")
        self._lt_start_btn.setFixedHeight(32)
        self._lt_start_btn.setStyleSheet(
            "QPushButton{background:#0d2420;color:#2dd4bf;border:1px solid #1a4a40;"
            "border-radius:6px;font-weight:700;padding:0 14px;}"
            "QPushButton:hover{background:#0f2e28;border-color:#2a6a58;}"
            "QPushButton:disabled{color:#444;border-color:#222;background:#111;}"
        )
        self._lt_start_btn.clicked.connect(self._start_libretranslate)

        self._lt_stop_btn = QPushButton("■  Stop LibreTranslate")
        self._lt_stop_btn.setFixedHeight(32)
        self._lt_stop_btn.setEnabled(False)
        self._lt_stop_btn.setStyleSheet(
            "QPushButton{background:#1a0000;color:#f87171;border:1px solid #4a0000;"
            "border-radius:6px;font-weight:700;padding:0 14px;}"
            "QPushButton:hover{background:#2a0000;border-color:#7a0000;}"
            "QPushButton:disabled{color:#444;border-color:#222;background:#111;}"
        )
        self._lt_stop_btn.clicked.connect(self._stop_libretranslate)

        self._lt_status_lbl = QLabel("Not running")
        self._lt_status_lbl.setStyleSheet("color:#666;font-size:11px;")

        lt_btn_row.addWidget(self._lt_start_btn)
        lt_btn_row.addWidget(self._lt_stop_btn)
        lt_btn_row.addWidget(self._lt_status_lbl)
        lt_btn_row.addStretch()
        lt_lay.addLayout(lt_btn_row)

        tl.addWidget(self._lt_section)

        # — Default target language —
        tl.addWidget(self._lbl("Default target language (shown in the Translate panel)"))
        self.trans_lang_combo = QComboBox()
        self.trans_lang_combo.setFixedWidth(220)
        try:
            import translator as TR
            self.trans_lang_combo.addItems(TR.LANG_NAMES[1:])  # skip Auto-detect
            default = TR.code_to_name(
                self._read_config_str("TRANSLATE_TARGET_LANG", "en")
            )
            idx = self.trans_lang_combo.findText(default)
            if idx >= 0:
                self.trans_lang_combo.setCurrentIndex(idx)
        except Exception:
            self.trans_lang_combo.addItem("English")
        tl.addWidget(self.trans_lang_combo)

        btn_save_trans = QPushButton("Save to config.py")
        btn_save_trans.setStyleSheet(accent_btn_qss())
        btn_save_trans.setFixedWidth(160)
        btn_save_trans.clicked.connect(self._save_trans)
        tl.addWidget(btn_save_trans)
        cl.addWidget(grp_trans)

        # Apply initial visibility
        self._on_backend_changed(self.backend_combo.currentIndex())

        # ── GitHub ────────────────────────────────────────────────────────────
        grp_gh = self._group("GitHub")
        ghl = QVBoxLayout(grp_gh)
        ghl.setSpacing(10)
        ghl.addWidget(self._lbl("GitHub Token (ghp_...)"))
        self.gh_token = QLineEdit()
        self.gh_token.setEchoMode(QLineEdit.Password)
        self._load_config_value("GITHUB_TOKEN", self.gh_token)
        ghl.addWidget(self.gh_token)
        btn_save_gh = QPushButton("Save to config.py")
        btn_save_gh.setStyleSheet(accent_btn_qss())
        btn_save_gh.setFixedWidth(160)
        btn_save_gh.clicked.connect(self._save_gh)
        ghl.addWidget(btn_save_gh)
        cl.addWidget(grp_gh)

        # ── Web Search ───────────────────────────────────────────────────────
        grp_ws = self._group("Web Search")
        wl = QVBoxLayout(grp_ws)
        wl.setSpacing(10)
        wl.addWidget(self._lbl("Max results per search (1–5 — more = more tokens)"))
        self.ws_spin = QSpinBox()
        self.ws_spin.setRange(1, 5)
        self.ws_spin.setValue(self._read_config_int("WEB_SEARCH_RESULTS", 3))
        self.ws_spin.setFixedWidth(70)
        wl.addWidget(self.ws_spin)
        btn_save_ws = QPushButton("Save")
        btn_save_ws.setFixedWidth(80)
        btn_save_ws.clicked.connect(self._save_ws)
        wl.addWidget(btn_save_ws)
        cl.addWidget(grp_ws)

        # ── Danger zone ───────────────────────────────────────────────────────
        grp_danger = self._group("Danger Zone")
        grp_danger.setStyleSheet(
            f"QGroupBox{{border:1px solid {d['red']};border-radius:8px;"
            f"margin-top:10px;padding-top:10px;color:{d['red']};font-size:11px;font-weight:700;}}"
            f"QGroupBox::title{{subcontrol-origin:margin;left:10px;padding:0 4px;}}"
        )
        dl = QVBoxLayout(grp_danger)
        dl.setSpacing(10)
        dl.addWidget(self._lbl("Clear all chat history (cannot be undone)", muted=False))
        btn_clear = QPushButton("🗑  Clear All History")
        btn_clear.setStyleSheet(
            f"QPushButton{{background:{d['red']};color:#fff;font-weight:700;border:none;"
            f"border-radius:6px;padding:7px 16px;}}"
            f"QPushButton:hover{{background:#dc2626;}}"
        )
        btn_clear.setFixedWidth(180)
        btn_clear.clicked.connect(self._clear_history)
        dl.addWidget(btn_clear)
        cl.addWidget(grp_danger)

        cl.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

    # ── Backend visibility toggle ───────────────────────────────────────────
    def _on_backend_changed(self, idx: int):
        # idx 0 = LibreTranslate, idx 1 = Google
        self._lt_section.setVisible(idx == 0)

    # ── LibreTranslate process management ─────────────────────────────────
    def _start_libretranslate(self):
        global _lt_process
        if _lt_process is not None and _lt_process.poll() is None:
            self._lt_status_lbl.setText("Already running")
            return

        url = self.lt_url.text().strip() or "http://localhost:5000"
        try:
            host, port = "127.0.0.1", "5000"
            if ":" in url.split("//")[-1]:
                parts = url.split("//")[-1].split(":")
                host  = parts[0]
                port  = parts[1].split("/")[0]
        except Exception:
            host, port = "127.0.0.1", "5000"

        try:
            # Launch libretranslate with no visible console window (Windows: CREATE_NO_WINDOW)
            kwargs = {}
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            _lt_process = subprocess.Popen(
                [sys.executable, "-m", "libretranslate", "--host", host, "--port", port],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                **kwargs,
            )
            self._lt_start_btn.setEnabled(False)
            self._lt_stop_btn.setEnabled(True)
            self._lt_status_lbl.setText("⏳ Starting… (first run may take a few minutes)")
            self._lt_status_lbl.setStyleSheet("color:#fb923c;font-size:11px;")
            # Poll every 3 s until the server responds
            self._lt_poll_timer = QTimer(self)
            self._lt_poll_timer.timeout.connect(self._poll_lt_ready)
            self._lt_poll_timer.start(3000)
        except FileNotFoundError:
            QMessageBox.warning(
                self, "LibreTranslate not installed",
                "Could not find the libretranslate command.\n\n"
                "Run this in your terminal first:\n\n    pip install libretranslate"
            )

    def _poll_lt_ready(self):
        import translator as TR
        if TR.libretranslate_available():
            self._lt_poll_timer.stop()
            self._lt_status_lbl.setText("● Running")
            self._lt_status_lbl.setStyleSheet("color:#4ade80;font-size:11px;font-weight:700;")
        else:
            # Still starting — keep polling, update dots animation
            cur = self._lt_status_lbl.text()
            dots = cur.count(".")
            self._lt_status_lbl.setText("⏳ Starting" + "." * ((dots % 3) + 1))

    def _stop_libretranslate(self):
        global _lt_process
        if _lt_process is not None:
            try:
                _lt_process.terminate()
                _lt_process = None
            except Exception:
                pass
        if hasattr(self, "_lt_poll_timer"):
            self._lt_poll_timer.stop()
        self._lt_start_btn.setEnabled(True)
        self._lt_stop_btn.setEnabled(False)
        self._lt_status_lbl.setText("Not running")
        self._lt_status_lbl.setStyleSheet("color:#666;font-size:11px;")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _group(self, title: str) -> QGroupBox:
        return QGroupBox(title)

    def _lbl(self, text: str, muted: bool = True) -> QLabel:
        d = T()
        l = QLabel(text)
        l.setWordWrap(True)
        l.setStyleSheet(f"color:{ d['muted'] if muted else d['text']};font-size:12px;background:transparent;")
        return l

    def _load_config_value(self, key: str, widget: QLineEdit):
        try:
            import config
            widget.setText(str(getattr(config, key, "")))
        except Exception:
            pass

    def _read_config_int(self, key: str, default: int) -> int:
        try:
            import config
            return int(getattr(config, key, default))
        except Exception:
            return default

    def _read_config_str(self, key: str, default: str) -> str:
        try:
            import config
            return str(getattr(config, key, default))
        except Exception:
            return default

    def _write_config(self, updates: dict):
        try:
            with open("config.py", "r", encoding="utf-8") as f:
                lines = f.readlines()
            new_lines = []
            written_keys = set()
            for line in lines:
                matched = False
                for key, val in updates.items():
                    if line.strip().startswith(key + " ") or line.strip().startswith(key + "="):
                        if isinstance(val, str):
                            new_lines.append(f'{key} = "{val}"\n')
                        else:
                            new_lines.append(f'{key} = {val}\n')
                        written_keys.add(key)
                        matched = True
                        break
                if not matched:
                    new_lines.append(line)
            for key, val in updates.items():
                if key not in written_keys:
                    if isinstance(val, str):
                        new_lines.append(f'\n{key} = "{val}"\n')
                    else:
                        new_lines.append(f'\n{key} = {val}\n')
            with open("config.py", "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            return True
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save config.py:\n{e}")
            return False

    def _apply_theme(self):
        set_theme(self.theme_combo.currentText())
        self.theme_changed.emit()

    def _apply_font(self):
        size = self.font_slider.value()
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QFont
        QApplication.instance().setFont(QFont("Segoe UI", size))

    def _apply_layout(self):
        self.layout_changed.emit(self.layout_combo.currentText())

    def _save_api(self):
        ok = self._write_config({
            "BASE_URL":      self.api_url.text().strip(),
            "API_KEY":       self.api_key.text().strip(),
            "DEFAULT_MODEL": self.default_model.text().strip(),
        })
        if ok:
            QMessageBox.information(self, "Saved", "API settings saved to config.py.\nRestart the app to apply.")

    def _save_trans(self):
        idx = self.backend_combo.currentIndex()
        backend_val = "libretranslate" if idx == 0 else "google"
        try:
            import translator as TR
            code = TR.name_to_code(self.trans_lang_combo.currentText())
        except Exception:
            code = "en"
        updates = {
            "TRANSLATE_BACKEND":     backend_val,
            "TRANSLATE_TARGET_LANG": code,
        }
        if idx == 0:  # only save LT URL when LT is the chosen backend
            updates["LIBRETRANSLATE_URL"] = self.lt_url.text().strip() or "http://localhost:5000"
        ok = self._write_config(updates)
        if ok:
            QMessageBox.information(
                self, "Saved",
                "Translation settings saved to config.py.\n"
                "Changes apply next time you open a Translate panel."
            )

    def _save_gh(self):
        ok = self._write_config({"GITHUB_TOKEN": self.gh_token.text().strip()})
        if ok:
            QMessageBox.information(self, "Saved", "GitHub token saved.")

    def _save_ws(self):
        ok = self._write_config({"WEB_SEARCH_RESULTS": self.ws_spin.value()})
        if ok:
            QMessageBox.information(self, "Saved", f"Web search set to {self.ws_spin.value()} results.")

    def _clear_history(self):
        if QMessageBox.question(
            self, "Clear History",
            "This will permanently delete ALL threads and messages. Are you sure?"
        ) == QMessageBox.Yes:
            import sqlite3
            from config import DB_PATH
            conn = sqlite3.connect(DB_PATH)
            conn.execute("DELETE FROM messages")
            conn.execute("DELETE FROM threads")
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Done", "All history cleared.")
