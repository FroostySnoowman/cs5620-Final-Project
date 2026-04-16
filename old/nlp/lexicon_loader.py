"""
Optional JSON lexicon: ``nlp/data/tennis_lexicon.json`` with shape
``{"by_key": {"net_advantage": ["...", ...], ...}, "greetings": [...], ...}``.

Merges with built-ins and combinatorial lines in ``coach_voice``.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List


@lru_cache(maxsize=1)
def load_optional_lexicon() -> Dict[str, Any]:
    path = Path(__file__).resolve().parent / "data" / "tennis_lexicon.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def extra_lines_for_key(key: str) -> List[str]:
    data = load_optional_lexicon()
    by_key = data.get("by_key") or {}
    raw = by_key.get(key)
    if isinstance(raw, list):
        return [str(x) for x in raw if isinstance(x, str)]
    return []
