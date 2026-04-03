"""Entry point for Local Helper."""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from database import init_db
import scheduler
from ui.main_window import MainWindow, apply_dark_palette
from config import FILES_DIR, TEMPLATES_DIR


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

    exit_code = app.exec_()
    scheduler.stop()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
