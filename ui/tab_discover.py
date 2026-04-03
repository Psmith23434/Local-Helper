"""Discover tab — model capabilities, features and what's possible."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QHBoxLayout, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.theme import get as T


CARDS = [
    ("🧠", "AI Models",
     "Your proxy gives you access to multiple AI models. Each has different strengths:\n"
     "• Claude Opus — Best reasoning, longest context\n"
     "• Claude Sonnet — Fast + smart, best daily driver\n"
     "• GPT-4.1 — Strong coding and function calling\n"
     "• Gemini 2.5 Pro — Multimodal, very long context"),
    ("🔍", "Web Search",
     "Enable web search per chat to inject live results into the AI prompt. "
     "The app uses DuckDuckGo, visits the actual pages, and sends up to 3000 chars per result. "
     "Cost: ~1500–4000 extra tokens per message. Keep off by default for simple questions."),
    ("🤖", "Agents",
     "Agents are AI presets with a custom system prompt, model, and optionally a GitHub repo. "
     "Create an agent for each project: Coding Assistant, GitHub Helper, Writing Assistant, etc. "
     "Each agent keeps its own thread history."),
    ("💻", "GitHub Integration",
     "Connect a GitHub repo to an Agent. The app will inject the repo file tree into the AI context. "
     "After the AI writes code, use the ‘🚀 Commit’ button to push changes directly to your repo. "
     "Requires a GitHub classic token (starts with ghp_) in config.py."),
    ("📎", "Code Blocks",
     "When the AI responds with a code block, an action bar appears:\n"
     "• 📋 Copy — copies code to clipboard\n"
     "• 💾 Save — saves to a local file with the right extension\n"
     "• 🚀 Commit — pushes directly to your GitHub repo (if configured)"),
    ("📊", "Token Costs",
     "Every message uses tokens (roughly 1 token ≈ 4 chars).\n"
     "• Simple question: ~200–500 tokens\n"
     "• With web search: +1500–4000 tokens\n"
     "• With GitHub file tree: +100–500 tokens\n"
     "• With full file content: +500–5000 tokens\n"
     "Keep context lean for cost efficiency."),
    ("🖼️", "Images & Videos",
     "Image generation (DALL-E, Stable Diffusion) and video generation (Sora, Runway) "
     "require separate API endpoints — not part of the chat API. "
     "These can be added as dedicated features in a future update. "
     "Vision (sending images to the AI) is supported if your proxy model supports it."),
    ("⏰", "Scheduled Tasks",
     "Agents support scheduled tasks — automated prompts that run on a timer. "
     "Use them for daily summaries, repo checks, or recurring reminders. "
     "Configure via the Agent settings dialog."),
]


class DiscoverTab(QWidget):
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
        cl.setContentsMargins(32, 28, 32, 32)
        cl.setSpacing(16)

        # Header
        h = QLabel("Discover")
        h.setFont(QFont("Segoe UI", 22, QFont.Bold))
        h.setStyleSheet(f"color:{d['text']};")
        cl.addWidget(h)
        sub = QLabel("Everything your Local Helper can do.")
        sub.setStyleSheet(f"color:{d['muted']};font-size:13px;margin-bottom:12px;")
        cl.addWidget(sub)

        # Cards grid (2 columns)
        row_layout = None
        for idx, (icon, title, body) in enumerate(CARDS):
            if idx % 2 == 0:
                row_layout = QHBoxLayout()
                row_layout.setSpacing(14)
                cl.addLayout(row_layout)

            card = QFrame()
            card.setStyleSheet(
                f"QFrame{{background:{d['surface']};border:1px solid {d['border']};"
                f"border-radius:10px;padding:16px;}}"
            )
            card_l = QVBoxLayout(card)
            card_l.setSpacing(6)

            title_lbl = QLabel(f"{icon}  {title}")
            title_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
            title_lbl.setStyleSheet(f"color:{d['text']};background:transparent;border:none;")
            card_l.addWidget(title_lbl)

            body_lbl = QLabel(body)
            body_lbl.setWordWrap(True)
            body_lbl.setStyleSheet(f"color:{d['muted']};font-size:12px;background:transparent;border:none;line-height:1.6;")
            card_l.addWidget(body_lbl)
            card_l.addStretch()

            row_layout.addWidget(card, 1)

        cl.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)
