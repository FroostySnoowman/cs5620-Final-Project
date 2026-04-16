"""
Per-player shot-category rates from point history (terminal action only).

When the feed does not encode strokes on outcomes, counts stay in ``unknown``.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, DefaultDict, Dict

from pipeline.parser import extract_points
from pipeline.shot_taxonomy import classify_action_type


def _empty_buckets() -> DefaultDict[str, Dict[str, int]]:
    return defaultdict(lambda: {"won": 0, "played": 0})


def history_terminal_shot_rates(match: dict) -> Dict[str, Dict[str, float]]:
    """
    For each player_id, per shot category: smoothed win rate on points where
    that category was the terminal action attributed to them.

    Returns nested dict player -> category -> rate in [0,1], plus ``_points`` meta.
    """
    points = extract_points(match)
    # player -> category -> {won, played}
    raw: Dict[str, DefaultDict[str, Dict[str, int]]] = defaultdict(_empty_buckets)

    for p in points:
        term_type = p.get("terminal_type") or ""
        cat = classify_action_type(term_type)
        actor = p.get("terminal_actor")
        if not actor:
            continue
        winner = p.get("winner")
        raw[actor][cat]["played"] += 1
        if winner == actor:
            raw[actor][cat]["won"] += 1

    out: Dict[str, Any] = {}
    alpha = 1.0
    for pid, buckets in raw.items():
        out[pid] = {}
        for cat, b in buckets.items():
            pl, w = b["played"], b["won"]
            out[pid][cat] = (w + alpha) / (pl + 2.0 * alpha) if pl > 0 else 0.5
    return out


def history_shot_support(match: dict, min_terminal: int = 8) -> Dict[str, Any]:
    """Whether history has enough labeled terminal shots for shot-specific advice."""
    points = extract_points(match)
    labeled = 0
    for p in points:
        t = p.get("terminal_type") or ""
        if classify_action_type(t) != "unknown":
            labeled += 1
    return {
        "terminal_labeled_points": labeled,
        "total_points": len(points),
        "shot_advice_supported": labeled >= min_terminal,
    }
