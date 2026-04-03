"""AI client — talks to the proxy using raw requests (no SDK) to avoid header conflicts."""

import requests
from config import BASE_URL, API_KEY, DEFAULT_MODEL


def _get_url():
    return BASE_URL.rstrip("/") + "/chat/completions"


def _get_headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def chat(messages: list[dict], model: str = DEFAULT_MODEL, stream: bool = False):
    """Send messages to the proxy and return the assistant reply.

    Args:
        messages: List of {role, content} dicts (system + history + user).
        model:    Model identifier string.
        stream:   If True, returns a generator yielding text chunks.

    Returns:
        str response text, or generator yielding str chunks if stream=True.
    """
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
    }

    if stream:
        return _stream(payload)
    else:
        r = requests.post(_get_url(), headers=_get_headers(), json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


def _stream(payload):
    """Generator that yields text chunks from a streaming response."""
    import json
    with requests.post(
        _get_url(),
        headers=_get_headers(),
        json=payload,
        stream=True,
        timeout=120,
    ) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line:
                continue
            text = line.decode("utf-8")
            if text.startswith("data: "):
                text = text[6:]
            if text.strip() == "[DONE]":
                break
            try:
                chunk = json.loads(text)
                delta = chunk["choices"][0].get("delta", {})
                content = delta.get("content")
                if content:
                    yield content
            except (json.JSONDecodeError, KeyError, IndexError):
                continue
