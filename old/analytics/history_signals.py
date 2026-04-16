"""
Point-sequence and aggregate signals for scenario-conditioned coach NLG (no LLM).

Buckets are discrete labels so templates stay grammatical.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from pipeline.parser import extract_points, focal_won_point


def _bucket_momentum(rate: float) -> str:
    if rate >= 0.62:
        return "hot"
    if rate <= 0.38:
        return "cold"
    return "neutral"


def _bucket_pressure(rate: float) -> str:
    """Higher rate = more pressure on opponent (good for focal)."""
    if rate >= 0.55:
        return "high"
    if rate <= 0.42:
        return "low"
    return "moderate"


def _rally_bucket(length: int) -> str:
    if length <= 2:
        return "short"
    if length <= 6:
        return "medium"
    return "long"


def _terminal_bucket(terminal: str) -> str:
    t = (terminal or "").upper()
    if "UNFORCED" in t:
        return "ue"
    if "FORCED" in t:
        return "fe"
    if "WINNER" in t:
        return "winner"
    if "DOUBLE" in t or "FAULT" in t:
        return "serve_event"
    return "other"


def _get_block(players: dict, pid: str, key: str) -> dict:
    return (players.get(pid) or {}).get(key) or {}


def _rolling_win_rates(
    wins: List[bool], windows: Tuple[int, ...] = (5, 10, 20)
) -> Dict[str, Optional[float]]:
    n = len(wins)
    out: Dict[str, Optional[float]] = {}
    for w in windows:
        if n < w:
            out[f"last_{w}"] = None
        else:
            slice_ = wins[-w:]
            out[f"last_{w}"] = sum(slice_) / float(w)
    return out


def build_match_narrative_context(
    match: dict, focal_id: str, opponent_id: str
) -> Dict[str, Any]:
    """
    Structured context from point history + player aggregate blocks.

    Per-point scorelines are not in the feed; clutch language uses aggregates only.
    """
    points = extract_points(match)
    players = match.get("players") or {}

    wins: List[bool] = [focal_won_point(p, focal_id) for p in points]
    n_pts = len(points)

    rally_hist = {"short": 0, "medium": 0, "long": 0}
    focal_serve_pts = 0
    focal_serve_won = 0
    focal_return_pts = 0
    focal_return_won = 0

    terminal_mix: Dict[str, int] = {
        "ue": 0,
        "fe": 0,
        "winner": 0,
        "other": 0,
    }
    double_faults = 0
    first_serve_attempts = 0
    first_serve_faults = 0

    for p in points:
        rl = int(p.get("rally_length") or 0)
        rally_hist[_rally_bucket(rl)] += 1

        if p.get("server") == focal_id:
            focal_serve_pts += 1
            if p.get("winner") == focal_id:
                focal_serve_won += 1
        else:
            focal_return_pts += 1
            if p.get("winner") == focal_id:
                focal_return_won += 1

        term = p.get("terminal_type") or ""
        tb = _terminal_bucket(term)
        if tb in terminal_mix:
            terminal_mix[tb] += 1
        else:
            terminal_mix["other"] += 1

        for a in p.get("actions") or []:
            au = (a or "").upper()
            if "DOUBLE" in au and "FAULT" in au:
                double_faults += 1
            if "FIRST_SERVE_FAULT" in au:
                first_serve_faults += 1
                first_serve_attempts += 1
            if "FIRST_IN" in au:
                first_serve_attempts += 1

    # Streaks (focal)
    longest_win = 0
    longest_loss = 0
    cur_w = 0
    cur_l = 0
    for w in wins:
        if w:
            cur_w += 1
            cur_l = 0
            longest_win = max(longest_win, cur_w)
        else:
            cur_l += 1
            cur_w = 0
            longest_loss = max(longest_loss, cur_l)

    rolling = _rolling_win_rates(wins)
    last5 = rolling.get("last_5")
    last10 = rolling.get("last_10")
    last20 = rolling.get("last_20")

    momentum = _bucket_momentum(last10 if last10 is not None else (sum(wins) / n_pts if n_pts else 0.5))

    serve_win_rate = (
        focal_serve_won / focal_serve_pts if focal_serve_pts else None
    )
    return_win_rate = (
        focal_return_won / focal_return_pts if focal_return_pts else None
    )

    serve_pressure = (
        _bucket_pressure(serve_win_rate) if serve_win_rate is not None else "moderate"
    )
    return_pressure = (
        _bucket_pressure(return_win_rate) if return_win_rate is not None else "moderate"
    )

    rally_total = sum(rally_hist.values()) or 1
    rally_share_short = rally_hist["short"] / rally_total

    if rally_share_short >= 0.85:
        rally_shape = "mostly_short"
    elif rally_hist["long"] / rally_total >= 0.12:
        rally_shape = "some_long"
    else:
        rally_shape = "mixed"

    # Aggregates: focal
    focal_serve = _get_block(players, focal_id, "serve")
    focal_ret = _get_block(players, focal_id, "return")
    focal_ind = _get_block(players, focal_id, "individualMatch")

    bp_conv = int(focal_ret.get("breakPointsConverted") or 0)
    bp_opp = int(focal_ret.get("breakPointOpportunities") or 0)
    bp_save = int(focal_serve.get("breakPointsSaved") or 0)
    bp_faced = int(focal_serve.get("breakPointsFaced") or 0)

    if bp_opp >= 8:
        clutch_return = "many_chances"
    elif bp_opp >= 3:
        clutch_return = "some_chances"
    else:
        clutch_return = "few_chances"

    if bp_faced >= 12:
        clutch_serve = "heavy_pressure"
    elif bp_faced >= 5:
        clutch_serve = "moderate_pressure"
    else:
        clutch_serve = "light_pressure"

    match_winner = match.get("matchWinner")
    outcome = "won" if match_winner == focal_id else "lost" if match_winner else "unknown"

    ctx: Dict[str, Any] = {
        "focal_id": focal_id,
        "opponent_id": opponent_id,
        "n_points": n_pts,
        "momentum": momentum,
        "serve_pressure_bucket": serve_pressure,
        "return_pressure_bucket": return_pressure,
        "rally_shape": rally_shape,
        "rally_histogram": rally_hist,
        "rolling_win_rate": {
            "last_5": last5,
            "last_10": last10,
            "last_20": last20,
        },
        "streaks": {
            "longest_win_streak": longest_win,
            "longest_loss_streak": longest_loss,
        },
        "history_rates": {
            "serve_points_won_rate": serve_win_rate,
            "return_points_won_rate": return_win_rate,
        },
        "terminal_mix": terminal_mix,
        "double_faults_total": double_faults,
        "first_serve_fault_rate": (
            first_serve_faults / first_serve_attempts
            if first_serve_attempts
            else None
        ),
        "clutch": {
            "break_points_on_return": {"converted": bp_conv, "opportunities": bp_opp},
            "break_points_on_serve": {"saved": bp_save, "faced": bp_faced},
            "return_bucket": clutch_return,
            "serve_bucket": clutch_serve,
        },
        "match_outcome_for_focal": outcome,
        "aggregate": {
            "focal_points_won_rate": (
                int(focal_ind.get("pointsWon") or 0)
                / max(int(focal_ind.get("pointsPlayed") or 1), 1)
            ),
        },
    }
    return ctx
