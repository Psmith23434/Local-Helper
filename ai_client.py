"""AI client — talks to the proxy using the OpenAI SDK."""

from openai import OpenAI
from config import BASE_URL, API_KEY, DEFAULT_MODEL

_client = None


def get_client():
    global _client
    if _client is None:
        _client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    return _client


def chat(messages: list[dict], model: str = DEFAULT_MODEL, stream: bool = False):
    """Send messages to the proxy and return the assistant reply.

    Args:
        messages: List of {role, content} dicts (system + history + user).
        model:    Model identifier string.
        stream:   If True, returns a streaming generator.

    Returns:
        str response text, or generator if stream=True.
    """
    client = get_client()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=stream,
    )
    if stream:
        return response
    return response.choices[0].message.content
