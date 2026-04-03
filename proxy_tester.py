"""Simple proxy/API tester - sends a minimal request to each model and shows the result."""

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QTextEdit, QLineEdit
)
from PyQt5.QtCore import QThread, pyqtSignal
from openai import OpenAI, APIConnectionError, APIStatusError, RateLimitError

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
            client = OpenAI(base_url=self.base_url, api_key=self.api_key, max_retries=0)
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": TEST_PROMPT}],
                max_tokens=60,
            )
            reply  = response.choices[0].message.content.strip()
            usage  = response.usage
            tokens = f"in={usage.prompt_tokens} out={usage.completion_tokens} total={usage.total_tokens}"
            self.result.emit(self.model, reply, tokens)

        except APIStatusError as e:
            # HTTP error returned by the proxy/API (4xx, 5xx)
            body = ""
            try:
                body = e.response.text
            except Exception:
                try:
                    body = str(e.response.json())
                except Exception:
                    body = repr(getattr(e, 'body', ''))
            parts = [f"status={getattr(e, 'status_code', 'unknown')}"]
            req_id = getattr(e, 'request_id', None)
            if req_id:
                parts.append(f"request_id={req_id}")
            parts.append(f"type={type(e).__name__}")
            parts.append(f"message={str(e)}")
            if body:
                parts.append(f"body={body}")
            self.result.emit(self.model, "ERROR:\n" + "\n".join(parts), "")

        except RateLimitError as e:
            self.result.emit(self.model, f"ERROR:\ntype=RateLimitError\nmessage={str(e)}", "")

        except APIConnectionError as e:
            self.result.emit(
                self.model,
                f"ERROR:\ntype={type(e).__name__}\nCould not connect to: {self.base_url}\ndetail={repr(e)}",
                ""
            )

        except Exception as e:
            self.result.emit(self.model, f"ERROR:\ntype={type(e).__name__}\ndetail={repr(e)}", "")


class ProxyTester(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Proxy Tester (Debug)")
        self.resize(760, 540)
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

        # Model selector + buttons
        row = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.addItems(MODELS)
        self.btn_test_one = QPushButton("Test Selected")
        self.btn_test_all = QPushButton("Test ALL Models")
        self.btn_clear    = QPushButton("Clear")
        row.addWidget(self.model_combo)
        row.addWidget(self.btn_test_one)
        row.addWidget(self.btn_test_all)
        row.addWidget(self.btn_clear)
        layout.addLayout(row)

        # Output
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFontFamily("Courier New")
        layout.addWidget(self.output)

        self.btn_test_one.clicked.connect(self._test_one)
        self.btn_test_all.clicked.connect(self._test_all)
        self.btn_clear.clicked.connect(self.output.clear)

    def _get_config(self):
        return self.url_input.text().strip(), self.key_input.text().strip()

    def _test_one(self):
        self._run(self.model_combo.currentText())

    def _test_all(self):
        for model in MODELS:
            self._run(model)

    def _run(self, model):
        base_url, api_key = self._get_config()
        self.output.append(f'<span style="color:#888">⏳ Testing <b>{model}</b> → {base_url}</span>')
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
        safe_reply = reply.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.output.append(
            f'{icon} <b>{model}</b>{token_info}<br>'
            f'<span style="color:{color}; white-space:pre-wrap; font-family:Courier New">'
            f'{safe_reply}</span><br>'
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = ProxyTester()
    w.show()
    sys.exit(app.exec_())
