"""Theme definitions for Local Helper."""

THEMES = {
    "Dark": {
        "bg":           "#0d0d0d",
        "surface":      "#141414",
        "surface2":     "#1a1a1a",
        "surface3":     "#1f1f1f",
        "border":       "#2a2a2a",
        "accent":       "#7c6af7",
        "accent_dim":   "#5a4fd1",
        "accent2":      "#4ade80",
        "text":         "#e8e8e8",
        "muted":        "#666666",
        "faint":        "#3a3a3a",
        "user_color":   "#7c6af7",
        "ai_color":     "#4ade80",
        "red":          "#f87171",
        "yellow":       "#fbbf24",
        "blue":         "#60a5fa",
        "tab_active":   "#1a1a1a",
        "tab_inactive": "#0d0d0d",
        "code_bg":      "#0a0a0a",
        "scrollbar":    "#2a2a2a",
    },
    "VS Code": {
        "bg":           "#1e1e1e",
        "surface":      "#252526",
        "surface2":     "#2d2d30",
        "surface3":     "#333337",
        "border":       "#3e3e42",
        "accent":       "#569cd6",
        "accent_dim":   "#264f78",
        "accent2":      "#4ec9b0",
        "text":         "#d4d4d4",
        "muted":        "#858585",
        "faint":        "#3c3c3c",
        "user_color":   "#9cdcfe",
        "ai_color":     "#4ec9b0",
        "red":          "#f44747",
        "yellow":       "#dcdcaa",
        "blue":         "#569cd6",
        "tab_active":   "#1e1e1e",
        "tab_inactive": "#2d2d30",
        "code_bg":      "#1a1a1a",
        "scrollbar":    "#424242",
    },
    # ── Fire ─────────────────────────────────────────────────────────────────
    # Deep charcoal base with ember oranges, molten gold accents and ash whites.
    # Inspired by: glowing coals, forge light, lava cracks.
    "Fire": {
        "bg":           "#0e0a07",   # near-black with warm brown undertone
        "surface":      "#17100a",   # dark charred wood
        "surface2":     "#1f160e",   # slightly lighter ember layer
        "surface3":     "#271c12",   # warm medium dark
        "border":       "#3d2710",   # dark amber border
        "accent":       "#f97316",   # vivid orange flame
        "accent_dim":   "#c2410c",   # burnt ember
        "accent2":      "#fbbf24",   # molten gold / yellow core
        "text":         "#f5e6d0",   # warm ash white
        "muted":        "#a07850",   # faded ember / warm grey
        "faint":        "#3d2710",   # very dark ember
        "user_color":   "#fb923c",   # orange flame — user messages
        "ai_color":     "#fcd34d",   # gold — AI responses
        "red":          "#ef4444",   # hot red for errors/danger
        "yellow":       "#fbbf24",   # amber
        "blue":         "#93c5fd",   # cool contrast blue (rare use)
        "tab_active":   "#1f160e",
        "tab_inactive": "#0e0a07",
        "code_bg":      "#0a0804",   # near-black for code blocks
        "scrollbar":    "#3d2710",
    },
}

_current = "Dark"


def get() -> dict:
    return THEMES[_current]


def set_theme(name: str):
    global _current
    if name in THEMES:
        _current = name


def name() -> str:
    return _current


def names() -> list[str]:
    return list(THEMES.keys())
