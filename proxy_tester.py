"""Simple proxy/API tester - sends a minimal request to each model and shows the result."""

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QTextEdit, QLineEdit
)
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from openai import OpenAI

# ─────────────────────────────────────────────
BASE_URL  = "https://YOUR_PROXY_URL/v1"   # <-- replace
API_KEY   = "YOUR_API_KEY"                 # <-- replace

MODELS = [
    "claude-opus-4.6",
    "claude-sonnet-4.6",
    "claude-sonnet-4.5",
    "claude-opus-4.5",
    "claude-haiku-4.5",
    "gpt-5.4",
    "gpt-5.2",
    "gpt-4.1",
    "gemini-3-pro-preview",
    "gemini-2.5-pro",
]

TEST_PROMPT = "Reply with exactly one sentence confirming you are working."
# ─────────────────────────────────────────────


class TestWorker(QThread):
    result = pyqtSignal(str, str, str)  # model, reply, tokens

    def __init__(self, model, base_url, api_key):
        super().__init__()
        self.model    = model
        self.base_url = base_url
        self.api_key  = api_key

    def run(self):
        try:
            client = OpenAI(base_url=self.base_url, api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": TEST_PROMPT}],
                max_tokens=60,
            )
            reply  = response.choices[0].message.content.strip()
            usage  = response.usage
            tokens = f"in={usage.prompt_tokens} out={usage.completion_tokens} total={usage.total_tokens}"
            self.result.emit(self.model, reply, tokens)
        except Exception as e:
            self.result.emit(self.model, f"ERROR: {e}", "")


class ProxyTester(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Proxy Tester")
        self.resize(640, 480)
        self._workers = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Config row
        cfg = QHBoxLayout()
        cfg.addWidget(QLabel("Base URL:"))
        self.url_input = QLineEdit(BASE_URL)
        cfg.addWidget(self.url_input)
        cfg.addWidget(QLabel("API Key:"))
        self.key_input = QLineEdit(API_KEY)
        self.key_input.setEchoMode(QLineEdit.Password)
        cfg.addWidget(self.key_input)
        layout.addLayout(cfg)

        # Model selector + test single
        row = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.addItems(MODELS)
        self.btn_test_one  = QPushButton("Test Selected")
        self.btn_test_all  = QPushButton("Test ALL Models")
        self.btn_clear     = QPushButton("Clear")
        row.addWidget(self.model_combo)
        row.addWidget(self.btn_test_one)
        row.addWidget(self.btn_test_all)
        row.addWidget(self.btn_clear)
        layout.addLayout(row)

        # Output
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        self.btn_test_one.clicked.connect(self._test_one)
        self.btn_test_all.clicked.connect(self._test_all)
        self.btn_clear.clicked.connect(self.output.clear)

    def _get_config(self):
        return self.url_input.text().strip(), self.key_input.text().strip()

    def _test_one(self):
        model = self.model_combo.currentText()
        self._run(model)

    def _test_all(self):
        for model in MODELS:
            self._run(model)

    def _run(self, model):
        base_url, api_key = self._get_config()
        self.output.append(f'<span style="color:#888">⏳ Testing <b>{model}</b>...</span>')
        worker = TestWorker(model, base_url, api_key)
        worker.result.connect(self._on_result)
        worker.start()
        self._workers.append(worker)  # prevent GC

    def _on_result(self, model, reply, tokens):
        if reply.startswith("ERROR:"):
            color = "#cc0000"
            icon  = "❌"
        else:
            color = "#2d6a4f"
            icon  = "✅"
        token_info = f' <span style="color:#999">({tokens})</span>' if tokens else ""
        self.output.append(
            f'{icon} <b>{model}</b>{token_info}<br>'
            f'<span style="color:{color}">{reply}</span><br>'
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = ProxyTester()
    w.show()
    sys.exit(app.exec_())
