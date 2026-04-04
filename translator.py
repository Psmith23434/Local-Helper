"""Translation backend — LibreTranslate (primary) + deep-translator (fallback).

Usage:
    from translator import translate
    text, backend = translate("Hallo Welt", source="de", target="en")
    # backend is "libretranslate" or "google"

Backend priority:
    1. LibreTranslate at LIBRETRANSLATE_URL (self-hosted, fully offline/private)
    2. deep-translator GoogleTranslate (online fallback, no key required)
"""

from __future__ import annotations

import urllib.request
import urllib.error
import json


# ── Language table ────────────────────────────────────────────────────────────
# (code, display name)  — union of LibreTranslate + deep-translator coverage
LANGUAGES: list[tuple[str, str]] = [
    ("auto", "Auto-detect"),
    ("af",   "Afrikaans"),
    ("sq",   "Albanian"),
    ("ar",   "Arabic"),
    ("az",   "Azerbaijani"),
    ("bn",   "Bengali"),
    ("bs",   "Bosnian"),
    ("bg",   "Bulgarian"),
    ("ca",   "Catalan"),
    ("zh",   "Chinese (Simplified)"),
    ("zt",   "Chinese (Traditional)"),
    ("cs",   "Czech"),
    ("da",   "Danish"),
    ("nl",   "Dutch"),
    ("en",   "English"),
    ("eo",   "Esperanto"),
    ("et",   "Estonian"),
    ("fi",   "Finnish"),
    ("fr",   "French"),
    ("gl",   "Galician"),
    ("de",   "German"),
    ("el",   "Greek"),
    ("gu",   "Gujarati"),
    ("ht",   "Haitian Creole"),
    ("he",   "Hebrew"),
    ("hi",   "Hindi"),
    ("hu",   "Hungarian"),
    ("id",   "Indonesian"),
    ("ga",   "Irish"),
    ("it",   "Italian"),
    ("ja",   "Japanese"),
    ("kn",   "Kannada"),
    ("ko",   "Korean"),
    ("lv",   "Latvian"),
    ("lt",   "Lithuanian"),
    ("lb",   "Luxembourgish"),
    ("mk",   "Macedonian"),
    ("ms",   "Malay"),
    ("mt",   "Maltese"),
    ("mr",   "Marathi"),
    ("nb",   "Norwegian"),
    ("fa",   "Persian"),
    ("pl",   "Polish"),
    ("pt",   "Portuguese"),
    ("ro",   "Romanian"),
    ("ru",   "Russian"),
    ("sr",   "Serbian"),
    ("sk",   "Slovak"),
    ("sl",   "Slovenian"),
    ("es",   "Spanish"),
    ("sw",   "Swahili"),
    ("sv",   "Swedish"),
    ("tl",   "Tagalog"),
    ("ta",   "Tamil"),
    ("th",   "Thai"),
    ("tr",   "Turkish"),
    ("uk",   "Ukrainian"),
    ("ur",   "Urdu"),
    ("vi",   "Vietnamese"),
    ("cy",   "Welsh"),
]

LANG_CODES: list[str]  = [c for c, _ in LANGUAGES]
LANG_NAMES: list[str]  = [n for _, n in LANGUAGES]


def code_to_name(code: str) -> str:
    for c, n in LANGUAGES:
        if c == code:
            return n
    return code


def name_to_code(name: str) -> str:
    for c, n in LANGUAGES:
        if n == name:
            return c
    return name


# ── Public API ────────────────────────────────────────────────────────────────

BACKEND_LIBRETRANSLATE = "libretranslate"
BACKEND_GOOGLE         = "google"


def translate(text: str, source: str = "auto", target: str = "en") -> tuple[str, str]:
    """Translate *text* from *source* language to *target* language.

    Returns a tuple: (translated_text, backend_name)
    backend_name is BACKEND_LIBRETRANSLATE or BACKEND_GOOGLE.
    On error, translated_text starts with '[Error]' and backend_name is 'error'.
    """
    if not text or not text.strip():
        return "", BACKEND_LIBRETRANSLATE

    # 1 — LibreTranslate
    try:
        result = _libretranslate(text, source, target)
        if result is not None:
            return result, BACKEND_LIBRETRANSLATE
    except Exception as e:
        print(f"[Translator] LibreTranslate failed: {e} — trying fallback")

    # 2 — deep-translator fallback
    try:
        return _deep_translator(text, source, target), BACKEND_GOOGLE
    except Exception as e:
        return f"[Error] Translation failed: {e}", "error"


def libretranslate_available() -> bool:
    """Ping the LibreTranslate server and return True if it responds."""
    url = get_libretranslate_url() + "/languages"
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def get_libretranslate_url() -> str:
    try:
        from config import LIBRETRANSLATE_URL
        return LIBRETRANSLATE_URL.rstrip("/")
    except Exception:
        return "http://localhost:5000"


def get_default_target() -> str:
    try:
        from config import TRANSLATE_TARGET_LANG
        return TRANSLATE_TARGET_LANG
    except Exception:
        return "en"


# ── LibreTranslate backend ────────────────────────────────────────────────────

def _libretranslate(text: str, source: str, target: str) -> str | None:
    """Returns translated text or None if server is unreachable."""
    url = get_libretranslate_url() + "/translate"
    src = "auto" if source == "auto" else source
    payload = json.dumps({
        "q":      text,
        "source": src,
        "target": target,
        "format": "text",
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("translatedText", None)
    except urllib.error.URLError:
        # Server not running — silently fall through to fallback
        return None


# ── deep-translator fallback ──────────────────────────────────────────────────

def _deep_translator(text: str, source: str, target: str) -> str:
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        return "[Error] deep-translator not installed. Run: pip install deep-translator"

    src = "auto" if source == "auto" else source
    translator = GoogleTranslator(source=src, target=target)
    return translator.translate(text)
