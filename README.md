# Local Helper

A single-user, local desktop AI assistant inspired by Perplexity Spaces.
Built with Python + PyQt5, connecting to an AI proxy supporting Claude, GPT, and Gemini models.

## Features
- Multiple **Spaces** with custom AI system instructions
- **Thread Organization** — chat history per Space stored in SQLite
- **File Context** — attach local `.txt` / `.py` files as AI context
- **Web Search** — multi-engine via `ddgs` (DuckDuckGo, Google, Bing, Brave, etc.)
- **GitHub Integration** — connect a repo and read files as context
- **Dropbox Sync** — sync Space files folder with Dropbox
- **Scheduled Tasks** — recurring AI tasks via APScheduler
- **Space Templates** — JSON-based templates for quick Space creation

## Setup

```bash
pip install -r requirements.txt
```

Then edit `config.py` and set your proxy `BASE_URL` and `API_KEY`.

```bash
python main.py
```

## Configuration
See `config.py` — set your proxy URL, API key, default model, and optional Dropbox/GitHub tokens.
