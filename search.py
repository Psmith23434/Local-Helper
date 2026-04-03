"""Web search and content extraction via ddgs."""

from config import WEB_SEARCH_RESULTS

try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False


def web_search(query: str, max_results: int = WEB_SEARCH_RESULTS) -> str:
    """Search the web and return extracted content as a formatted string.

    Returns empty string if ddgs is not installed or search fails.
    """
    if not DDGS_AVAILABLE:
        return ""
    try:
        results = DDGS().text(query, backend="auto", max_results=max_results)
        if not results:
            return ""

        context_parts = []
        for i, r in enumerate(results[:max_results], 1):
            title = r.get("title", "")
            url   = r.get("href", "")
            body  = r.get("body", "")

            # Try to extract full page content
            try:
                extracted = DDGS().extract(url, fmt="text_markdown")
                content = extracted.get("content", body)[:3000]  # cap at 3000 chars per result
            except Exception:
                content = body

            context_parts.append(f"[Result {i}] {title}\nURL: {url}\n{content}")

        return "\n\n---\n\n".join(context_parts)
    except Exception as e:
        return f"[Web search error: {e}]"


def news_search(query: str, max_results: int = 5) -> str:
    """Search news and return formatted results."""
    if not DDGS_AVAILABLE:
        return ""
    try:
        results = DDGS().news(query, backend="auto", max_results=max_results)
        if not results:
            return ""
        parts = []
        for i, r in enumerate(results, 1):
            parts.append(f"[News {i}] {r.get('title','')}\nSource: {r.get('source','')}\nDate: {r.get('date','')}\n{r.get('body','')}")
        return "\n\n".join(parts)
    except Exception as e:
        return f"[News search error: {e}]"
