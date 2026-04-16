"""
Tactic labels derived from point history (no LLM).

Rules (priority order):
1. approach_net — netChoices marks focal player at net, or terminal volley-like tag.
2. aggressive — short rally and focal wins via ace/winner or opponent error on terminal.
3. extend_rally — rally length >= LONG_RALLY_THRESHOLD.
4. neutral — default.
"""

from typing import Optional

from .constants import (
    LONG_RALLY_THRESHOLD,
    SHORT_RALLY_THRESHOLD,
    TACTIC_AGGRESSIVE,
    TACTIC_APPROACH_NET,
    TACTIC_EXTEND_RALLY,
    TACTIC_NEUTRAL,
)


def _terminal_is_focal_success(
    focal_id: str,
    focal_won: bool,
    terminal_type: str,
    terminal_actor: Optional[str],
) -> bool:
    if not focal_won:
        return False
    t = terminal_type
    if t == "ACE" and terminal_actor == focal_id:
        return True
    if t == "WINNER" and terminal_actor == focal_id:
        return True
    if t in ("FORCED ERROR", "UNFORCED ERROR") and terminal_actor != focal_id:
        return True
    if t == "DOUBLE FAULT" and terminal_actor != focal_id:
        return True
    return False


def infer_tactic_label(point: dict, focal_id: str) -> int:
    rally = int(point["rally_length"])
    net = point.get("net") or {}
    if net.get(focal_id) is True:
        return TACTIC_APPROACH_NET

    detail = point.get("actions_detail") or []
    for a in detail:
        typ = a.get("type") or ""
        aid = a.get("actor_id")
        if "VOLLEY" in typ and aid == focal_id:
            return TACTIC_APPROACH_NET

    term_type = point.get("terminal_type") or ""
    term_actor = point.get("terminal_actor")
    won = point.get("winner") == focal_id

    if rally >= LONG_RALLY_THRESHOLD:
        return TACTIC_EXTEND_RALLY

    if rally <= SHORT_RALLY_THRESHOLD and _terminal_is_focal_success(
        focal_id, won, term_type, term_actor
    ):
        return TACTIC_AGGRESSIVE

    return TACTIC_NEUTRAL
