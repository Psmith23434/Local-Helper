"""Settings tab — theme, font size, layout, API config, clear history."""

import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QLineEdit, QSpinBox, QGroupBox, QMessageBox,
    QSlider, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import database as db
from ui.theme import get as T, set_theme, names as theme_names, name as theme_name
from ui.styles import accent_btn_qss


class SettingsTab(QWidget):
    theme_changed  = pyqtSignal()         # tell main window to re-apply QSS
    layout_changed = pyqtSignal(str)      # emits new layout name e.g. "Sidebar"

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

        # ── Appearance ───────────────────────────────────────────────
        grp_appear = self._group("Appearance")
        gl = QVBoxLayout(grp_appear)
        gl.setSpacing(10)

        # Theme
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

        # Font size
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

        # Layout switcher
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

        # ── API / Proxy ─────────────────────────────────────────────
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

        # ── GitHub ───────────────────────────────────────────────
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

        # ── Web Search ───────────────────────────────────────────
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

        # ── Danger zone ───────────────────────────────────────────
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

    # ── Helpers ───────────────────────────────────────────────────
    def _group(self, title: str) -> QGroupBox:
        g = QGroupBox(title)
        return g

    def _lbl(self, text: str, muted: bool = True) -> QLabel:
        d = T()
        l = QLabel(text)
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

    def _write_config(self, updates: dict):
        try:
            with open("config.py", "r", encoding="utf-8") as f:
                lines = f.readlines()
            new_lines = []
            for line in lines:
                written = False
                for key, val in updates.items():
                    if line.strip().startswith(key + " ") or line.strip().startswith(key + "="):
                        if isinstance(val, str):
                            new_lines.append(f'{key} = "{val}"\n')
                        else:
                            new_lines.append(f'{key} = {val}\n')
                        written = True
                        break
                if not written:
                    new_lines.append(line)
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
