"""
Map raw point action types to coarse shot/stroke categories.

Many feeds only label outcomes (WINNER, UNFORCED ERROR); stroke may appear in the
same string (e.g. FOREHAND WINNER) or stay unknown.
"""

from __future__ import annotations

from typing import Optional

# Ordered: first match wins (more specific tokens first)
_CATEGORY_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("drop_shot", ("DROP SHOT", "DROP_SHOT", "DROPSHOT")),
    ("lob", ("LOB",)),
    ("overhead", ("OVERHEAD", "SMASH")),
    ("volley", ("VOLLEY", "HALF VOLLEY", "HALF_VOLLEY")),
    ("serve", ("SERVE", "FIRST_IN", "SECOND_IN", "ACE", "FIRST_SERVE", "SECOND_SERVE")),
    ("return", ("RETURN",)),
    ("forehand", ("FOREHAND", "FH")),
    ("backhand", ("BACKHAND", "BH", "SLICE")),
)


def classify_action_type(raw_upper: str) -> str:
    """
    Return one of: forehand, backhand, volley, overhead, lob, drop_shot,
    serve, return, unknown.
    """
    s = (raw_upper or "").strip().upper()
    if not s:
        return "unknown"
    for cat, keys in _CATEGORY_KEYWORDS:
        for k in keys:
            if k in s:
                return cat
    return "unknown"


def terminal_shot_category(point: dict) -> str:
    """Use terminal action type string from parsed point."""
    t = point.get("terminal_type") or ""
    return classify_action_type(t)


ALL_SHOT_CATEGORIES = (
    "forehand",
    "backhand",
    "volley",
    "overhead",
    "lob",
    "drop_shot",
    "serve",
    "return",
    "unknown",
)
