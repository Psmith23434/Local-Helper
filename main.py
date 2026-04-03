"""Entry point for Local Helper."""

import sys
import os
from PyQt5.QtWidgets import QApplication
from database import init_db
import scheduler
from ui.main_window import MainWindow
from config import FILES_DIR, TEMPLATES_DIR


def main():
    # Ensure required folders exist
    os.makedirs(FILES_DIR, exist_ok=True)
    os.makedirs(TEMPLATES_DIR, exist_ok=True)

    # Initialize database
    init_db()

    # Start background scheduler
    scheduler.start()

    # Launch GUI
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()

    exit_code = app.exec_()

    # Clean shutdown
    scheduler.stop()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
