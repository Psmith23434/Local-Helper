"""Entry point for Local Helper."""

# ── Silence urllib3/chardet version mismatch warning from requests ────────────
import warnings
warnings.filterwarnings("ignore", category=Warning, module="requests")
warnings.filterwarnings("ignore", message="urllib3", category=Warning)
warnings.filterwarnings("ignore", message="chardet", category=Warning)
warnings.filterwarnings("ignore", message="charset_normalizer", category=Warning)
# ─────────────────────────────────────────────────────────────────────────────

# ── CRITICAL: pre-load torch c10.dll BEFORE any PyQt5 import ─────────────────
# PyTorch 2.9+ on Windows raises [WinError 1114] if PyQt5 is loaded first.
import platform as _platform
if _platform.system() == "Windows":
    import ctypes as _ctypes
    import os as _os
    from importlib.util import find_spec as _find_spec
    try:
        _spec = _find_spec("torch")
        if _spec and _spec.origin:
            _dll = _os.path.join(_os.path.dirname(_spec.origin), "lib", "c10.dll")
            if _os.path.exists(_dll):
                _ctypes.CDLL(_os.path.normpath(_dll))
    except Exception:
        pass
# ─────────────────────────────────────────────────────────────────────────────

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from database import init_db
import scheduler
from ui.main_window import MainWindow, apply_dark_palette
from config import FILES_DIR, TEMPLATES_DIR
from snipping_tool import register_snip_hotkey


def main():
    os.makedirs(FILES_DIR, exist_ok=True)
    os.makedirs(TEMPLATES_DIR, exist_ok=True)

    init_db()
    scheduler.start()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    apply_dark_palette(app)

    try:
        from config import GUI_LAYOUT
    except ImportError:
        GUI_LAYOUT = "Tabbed"

    window = MainWindow(layout=GUI_LAYOUT)
    window.show()

    register_snip_hotkey(
        root=window,
        send_to_chat_callback=getattr(window, "attach_image", lambda b64, prompt: None)
    )

    exit_code = app.exec_()
    scheduler.stop()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
