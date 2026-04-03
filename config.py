# ─────────────────────────────────────────────
#  Local Helper — Configuration
#  Fill in your proxy details below.
# ─────────────────────────────────────────────

# AI Proxy
BASE_URL = "https://YOUR_PROXY_URL/v1"   # <-- replace with your proxy base URL
API_KEY  = "YOUR_API_KEY"                 # <-- replace with your proxy API key

# Default model (must be supported by your proxy)
DEFAULT_MODEL = "claude-sonnet-4.6"

# Available models shown in the UI dropdown
AVAILABLE_MODELS = [
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

# Dropbox (optional)
DROPBOX_ACCESS_TOKEN = ""   # <-- your Dropbox access token, or leave empty

# GitHub (optional)
GITHUB_TOKEN = ""            # <-- your GitHub personal access token, or leave empty

# Web search results count (3–5 recommended)
WEB_SEARCH_RESULTS = 5

# Database file
DB_PATH = "local_helper.db"

# Space files directory (synced with Dropbox if token is set)
FILES_DIR = "space_files"

# Templates directory
TEMPLATES_DIR = "templates"
