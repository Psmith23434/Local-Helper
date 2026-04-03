"""Two example conversations seeded into the database on first run."""

import database as db

CODING_EXAMPLE = {
    "space_name": "🧑‍💻  Coding Assistant",
    "instructions": "You are an expert Python developer. When writing code, always use type hints, docstrings, and follow PEP-8. Format code in markdown fences with the language tag.",
    "thread_title": "Quicksort example",
    "messages": [
        ("user", "Write me a clean Python quicksort with type hints"),
        ("assistant", """Here's a clean, idiomatic Python quicksort:\n\n```python\nfrom typing import TypeVar\n\nT = TypeVar('T')\n\n\ndef quicksort(arr: list[T]) -> list[T]:\n    \"\"\"Sort *arr* in ascending order using the quicksort algorithm.\n\n    Time complexity: O(n log n) average, O(n²) worst case.\n    Space complexity: O(n) due to list slicing.\n    \"\"\"\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left   = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right  = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)\n\n\nif __name__ == '__main__':\n    data = [3, 6, 8, 10, 1, 2, 1]\n    print(quicksort(data))  # [1, 1, 2, 3, 6, 8, 10]\n```\n\n**How it works:**\n- Pick the **middle element** as pivot (avoids worst-case on sorted input)\n- Partition into three lists: smaller, equal, larger\n- Recursively sort left and right, then concatenate"""),
    ],
}

CHAT_EXAMPLE = {
    "space_name": "💬  General Chat",
    "instructions": "You are a knowledgeable, friendly assistant. Format answers clearly using markdown: use **bold** for key terms, bullet lists for comparisons, and tables where useful.",
    "thread_title": "Python vs JavaScript",
    "messages": [
        ("user", "Quick comparison: Python vs JavaScript for backend dev"),
        ("assistant", """Here's a quick breakdown:\n\n| Feature | Python | JavaScript (Node) |\n|---|---|---|\n| Syntax | Clean, readable | Flexible, curly-brace |\n| Speed | Moderate | Fast (V8 engine) |\n| Ecosystem | Data/ML/scripting | Full-stack/real-time |\n| Async | asyncio | Native async/await |\n| Typing | Optional (mypy) | Optional (TypeScript) |\n\n**When to pick Python:**\n- Data science, ML, or scripting workflows\n- Rapid prototyping with readable code\n- Teams coming from a scientific background\n\n**When to pick Node.js:**\n- Real-time apps (chat, live dashboards)\n- Sharing code between frontend and backend\n- High-concurrency I/O-bound services\n\n> **Bottom line:** Python wins on readability and the data ecosystem. Node wins on performance for I/O-heavy workloads and full-stack JavaScript consistency."""),
    ],
}


def seed_examples():
    """Insert example spaces/threads if they don't exist yet."""
    existing = {s["name"] for s in db.get_spaces()}

    for example in [CODING_EXAMPLE, CHAT_EXAMPLE]:
        if example["space_name"] in existing:
            continue
        space_id = db.create_space(
            name=example["space_name"],
            instructions=example["instructions"],
            model="",
            github_repo="",
            web_search=True,
        )
        thread_id = db.create_thread(space_id, title=example["thread_title"])
        for role, content in example["messages"]:
            db.add_message(thread_id, role, content)
