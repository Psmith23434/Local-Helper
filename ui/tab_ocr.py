"""OCR tab — wraps OCRWidget and wires 'Insert into Chat' to the chat panel."""

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from ui.ocr_widget import OCRWidget


class OCRTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.ocr_widget = OCRWidget()
        lay.addWidget(self.ocr_widget)
        # text_ready is connected to the chat panel in TabbedLayout after init
