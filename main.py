"""Entry point for Local Helper."""

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

    # Read layout preference from config
    try:
        from config import GUI_LAYOUT
    except ImportError:
        GUI_LAYOUT = "Tabbed"

    window = MainWindow(layout=GUI_LAYOUT)
    window.show()

    # Register global snipping tool hotkey (Ctrl+Shift+S)
    # Passes the window's attach_image method as the send-to-chat callback.
    # If MainWindow does not yet expose attach_image, wire it up there.
    register_snip_hotkey(
        root=window,
        send_to_chat_callback=getattr(window, "attach_image", lambda b64, prompt: None)
    )

    exit_code = app.exec_()
    scheduler.stop()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
