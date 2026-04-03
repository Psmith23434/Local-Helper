"""Tips tab — example conversations and usage tips."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.theme import get as T


TIPS = [
    {
        "icon": "💡",
        "title": "Quick comparison: Python vs JavaScript",
        "prompt": "Quick comparison: Python vs JavaScript for backend dev",
        "response": (
            "| Feature | Python | JavaScript (Node) |\n"
            "|---|---|---|\n"
            "| Syntax | Clean, readable | Flexible, curly-brace |\n"
            "| Speed | Moderate | Fast (V8 engine) |\n"
            "| Ecosystem | Data/ML/scripting | Full-stack/real-time |\n"
            "\n**When to pick Python:** data science, ML, rapid prototyping.\n"
            "**When to pick Node.js:** real-time apps, full-stack JS consistency."
        ),
        "tags": ["comparison", "backend", "python", "javascript"],
    },
    {
        "icon": "🐍",
        "title": "Python quicksort with type hints",
        "prompt": "Write me a clean Python quicksort with type hints",
        "response": (
            "```python\n"
            "from typing import TypeVar\nT = TypeVar('T')\n\n"
            "def quicksort(arr: list[T]) -> list[T]:\n"
            "    if len(arr) <= 1: return arr\n"
            "    pivot = arr[len(arr) // 2]\n"
            "    left   = [x for x in arr if x < pivot]\n"
            "    middle = [x for x in arr if x == pivot]\n"
            "    right  = [x for x in arr if x > pivot]\n"
            "    return quicksort(left) + middle + quicksort(right)\n"
            "```\n"
            "**How it works:** middle pivot avoids worst-case on sorted input. "
            "Partition into three lists, recursively sort, concatenate."
        ),
        "tags": ["python", "algorithms", "code"],
    },
    {
        "icon": "🔍",
        "title": "Use web search for current events",
        "prompt": "What's the latest news about Python 3.14?",
        "response": "Enable 🔍 Web search in the top bar before sending — the app will fetch live results and inject them into the AI context. Without it, the AI only knows its training data.",
        "tags": ["web search", "tips"],
    },
    {
        "icon": "🤖",
        "title": "Create a Coding Agent",
        "prompt": "Go to Agents tab → + New Agent",
        "response": (
            "Set a system prompt like:\n"
            "> *You are an expert Python developer. Use type hints, docstrings, and PEP-8. "
            "Format code in markdown fences with the language tag.*\n\n"
            "Optionally connect your GitHub repo. Now every chat in this agent "
            "has that context baked in automatically."
        ),
        "tags": ["agents", "setup", "tips"],
    },
    {
        "icon": "🚀",
        "title": "Commit AI code to GitHub",
        "prompt": "Ask the AI to write a function, then click 🚀 Commit",
        "response": (
            "When the AI returns a code block, a bar appears below the chat:\n"
            "• 📋 **Copy** — clipboard\n"
            "• 💾 **Save** — local file with correct extension\n"
            "• 🚀 **Commit** — enter a path + message → pushed to GitHub instantly"
        ),
        "tags": ["github", "code", "tips"],
    },
    {
        "icon": "💰",
        "title": "Keep token costs low",
        "prompt": "Practical tips for reducing token usage",
        "response": (
            "• Keep web search **off** unless you need current data\n"
            "• Use shorter system prompts in agents\n"
            "• Start a new thread for unrelated topics — shorter history = fewer tokens\n"
            "• Use a faster/cheaper model (Sonnet vs Opus) for simple tasks\n"
            "• Don’t inject large GitHub files unless necessary"
        ),
        "tags": ["tokens", "cost", "tips"],
    },
]


class TipsTab(QWidget):
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
        cl.setSpacing(14)

        h = QLabel("💡 Tips & Examples")
        h.setFont(QFont("Segoe UI", 22, QFont.Bold))
        h.setStyleSheet(f"color:{d['text']};")
        cl.addWidget(h)
        sub = QLabel("Example prompts and usage tips to get the most out of Local Helper.")
        sub.setStyleSheet(f"color:{d['muted']};font-size:13px;margin-bottom:8px;")
        cl.addWidget(sub)

        for tip in TIPS:
            card = QFrame()
            card.setStyleSheet(
                f"QFrame{{background:{d['surface']};border:1px solid {d['border']};"
                f"border-radius:10px;padding:0;}}"
            )
            cl2 = QVBoxLayout(card)
            cl2.setContentsMargins(16, 12, 16, 14)
            cl2.setSpacing(6)

            # Header
            hdr = QHBoxLayout()
            title_lbl = QLabel(f"{tip['icon']}  {tip['title']}")
            title_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
            title_lbl.setStyleSheet(f"color:{d['text']};background:transparent;border:none;")
            hdr.addWidget(title_lbl)
            hdr.addStretch()
            # Tags
            for tag in tip["tags"][:3]:
                tl = QLabel(tag)
                tl.setStyleSheet(
                    f"background:{d['surface2']};color:{d['muted']};font-size:10px;"
                    f"padding:2px 7px;border-radius:10px;border:none;"
                )
                hdr.addWidget(tl)
            cl2.addLayout(hdr)

            # Prompt box
            p_lbl = QLabel(f"🗨️  {tip['prompt']}")
            p_lbl.setStyleSheet(
                f"background:{d['surface2']};color:{d['accent']};font-size:12px;"
                f"padding:5px 10px;border-radius:6px;border:none;"
            )
            cl2.addWidget(p_lbl)

            # Response preview
            r_lbl = QLabel(tip["response"])
            r_lbl.setWordWrap(True)
            r_lbl.setStyleSheet(
                f"color:{d['muted']};font-size:12px;background:transparent;border:none;"
                f"padding:4px 2px;"
            )
            cl2.addWidget(r_lbl)

            cl.addWidget(card)

        cl.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)
