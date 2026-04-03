import base64
import io
from PIL import Image

# ── Tesseract language map ────────────────────────────────────────────────────
# Maps langdetect ISO 639-1 codes → Tesseract language codes
LANG_MAP = {
    "en": "eng",
    "de": "deu",
    "fr": "fra",
    "es": "spa",
    "it": "ita",
    "nl": "nld",
    "pt": "por",
    "ru": "rus",
    "pl": "pol",
    "cs": "ces",
    "sv": "swe",
}

DEFAULT_LANG = "eng+deu"  # fallback when auto-detect fails


def run_ocr(image: Image.Image, mode: str = "quick", lang_override: str = None) -> str:
    """
    Extract text from a PIL Image.

    Args:
        image:         PIL Image to process.
        mode:          'quick' = Tesseract (offline)
                       'ai'    = GPT-4o vision (online, auto-detects language)
        lang_override: Tesseract language code (e.g. 'deu+eng').
                       If None and mode='quick', langdetect auto-detection runs first.

    Returns:
        Extracted text as a string.
    """
    if mode == "ai":
        return _ai_ocr(image)
    else:
        return _tesseract_ocr(image, lang_override)


# ── Quick OCR (Tesseract) ─────────────────────────────────────────────────────

def _tesseract_ocr(image: Image.Image, lang_override: str = None) -> str:
    try:
        import pytesseract
    except ImportError:
        return "[Error] pytesseract is not installed. Run: pip install pytesseract"

    if lang_override:
        # User pre-picked a language — run directly, no detection step
        lang = lang_override
    else:
        # Auto-detect language via a quick English pass + langdetect
        lang = _detect_language(image)

    try:
        text = pytesseract.image_to_string(image, lang=lang)
        return text.strip() or "[No text found]"
    except Exception as e:
        return f"[Tesseract Error] {e}"


def _detect_language(image: Image.Image) -> str:
    """
    Run a quick Tesseract pass with English, then use langdetect
    to identify the language. Falls back to DEFAULT_LANG on failure.
    """
    try:
        import pytesseract
        from langdetect import detect, LangDetectException

        raw = pytesseract.image_to_string(image, lang="eng")
        if not raw.strip():
            return DEFAULT_LANG

        detected = detect(raw)
        lang = LANG_MAP.get(detected, None)

        if lang:
            print(f"[OCR] Auto-detected language: {detected} → Tesseract: {lang}")
            return lang
        else:
            print(f"[OCR] Language '{detected}' not in map, using default: {DEFAULT_LANG}")
            return DEFAULT_LANG

    except Exception as e:
        print(f"[OCR] Language detection failed: {e}. Using default: {DEFAULT_LANG}")
        return DEFAULT_LANG


# ── AI OCR (GPT-4o Vision) ────────────────────────────────────────────────────

def _ai_ocr(image: Image.Image) -> str:
    """
    Send image to GPT-4o vision and extract all text.
    Uses the OpenAI client from ai_client.py.
    """
    try:
        from ai_client import get_client
        from config import load_config

        config = load_config()
        client = get_client(config)

        b64 = _image_to_base64(image)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64}"}
                        },
                        {
                            "type": "text",
                            "text": (
                                "Please extract ALL text visible in this image exactly as it appears. "
                                "Preserve formatting, line breaks, and structure where possible. "
                                "Do not add any commentary — only output the extracted text."
                            )
                        }
                    ]
                }
            ],
            max_tokens=2048
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"[AI OCR Error] {e}"


def _image_to_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


# ── Utility: encode image for chat message payload ────────────────────────────

def image_to_chat_payload(image: Image.Image, prompt: str) -> list:
    """
    Build the message content list for sending an image + prompt to GPT-4o.
    Use this when attaching a snip directly to the chat.
    """
    b64 = _image_to_base64(image)
    return [
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}"}
        },
        {
            "type": "text",
            "text": prompt
        }
    ]
