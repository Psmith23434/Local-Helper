"""OCR helpers — EasyOCR (quick/offline) and GPT-4o Vision (AI/online)."""

import base64
import io
import numpy as np
from PIL import Image

# EasyOCR language codes for the toolbar selector
LANG_MAP = {
    "eng": ["en"],
    "deu": ["de"],
    "fra": ["fr"],
    "spa": ["es"],
    "ita": ["it"],
    "nld": ["nl"],
    "por": ["pt"],
    "rus": ["ru"],
    "pol": ["pl"],
    "ces": ["cs"],
    "swe": ["sv"],
}

DEFAULT_LANGS = ["en", "de"]  # auto mode: English + German

# Module-level reader cache — EasyOCR model loads once (~1–2 s), reused after
_reader_cache = {}


def _get_reader(langs: list, use_gpu: bool = False):
    """Return a cached EasyOCR Reader for the given language list and GPU flag."""
    import easyocr
    key = (tuple(sorted(langs)), use_gpu)
    if key not in _reader_cache:
        print(f"[OCR] Loading EasyOCR model for languages: {langs}, GPU: {use_gpu}")
        _reader_cache[key] = easyocr.Reader(langs, gpu=use_gpu)
    return _reader_cache[key]


def run_ocr(image: Image.Image, mode: str = "quick", lang_override: str = None,
           use_gpu: bool = False) -> str:
    """
    Extract text from a PIL Image.

    Args:
        image:         PIL Image to process.
        mode:          'quick' = EasyOCR (offline)
                       'ai'    = GPT-4o vision (online)
        lang_override: Tesseract-style language code from UI (e.g. 'deu').
        use_gpu:       Whether to use CUDA GPU for EasyOCR (ignored in AI mode).

    Returns:
        Extracted text as a string.
    """
    if mode == "ai":
        return _ai_ocr(image)
    return _easyocr_ocr(image, lang_override, use_gpu=use_gpu)


# ── Quick OCR (EasyOCR) ───────────────────────────────────────────────────────

def _easyocr_ocr(image: Image.Image, lang_override: str = None,
                 use_gpu: bool = False) -> str:
    try:
        import easyocr  # noqa
    except ImportError:
        return "[Error] easyocr not installed. Run: pip install easyocr"

    if lang_override and lang_override != "auto":
        langs = LANG_MAP.get(lang_override, DEFAULT_LANGS)
    else:
        langs = DEFAULT_LANGS

    try:
        reader = _get_reader(langs, use_gpu=use_gpu)
        img_array = np.array(image.convert("RGB"))
        results = reader.readtext(img_array, detail=0, paragraph=True)
        text = "\n".join(results).strip()
        return text or "[No text found]"
    except Exception as e:
        return f"[EasyOCR Error] {e}"


# ── AI OCR (GPT-4o Vision) ────────────────────────────────────────────────────

def _ai_ocr(image: Image.Image) -> str:
    try:
        from ai_client import get_client
        from config import load_config

        config = load_config()
        client = get_client(config)
        b64 = _image_to_base64(image)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                    {"type": "text", "text": (
                        "Extract ALL text visible in this image exactly as it appears. "
                        "Preserve formatting and line breaks. Output only the extracted text."
                    )}
                ]
            }],
            max_tokens=2048
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"[AI OCR Error] {e}"


def _image_to_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


# ── Utility: encode image for chat payload ────────────────────────────────────

def image_to_chat_payload(image: Image.Image, prompt: str) -> list:
    b64 = _image_to_base64(image)
    return [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        {"type": "text", "text": prompt}
    ]
