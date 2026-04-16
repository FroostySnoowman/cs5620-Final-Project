import json
from typing import Any, Dict, List, Optional


def load_match(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_action_type(raw: str) -> str:
    return (raw or "").strip().upper()


def normalize_point_actions(actions: List[dict]) -> List[Dict[str, Any]]:
    out = []
    for a in actions:
        out.append(
            {
                "type": normalize_action_type(a.get("type", "")),
                "actor_id": a.get("actorId"),
            }
        )
    return out


def terminal_action(actions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Last action in the point (data source lists events in order)."""
    if not actions:
        return None
    return actions[-1]


def focal_won_point(point: dict, focal_id: str) -> bool:
    return point.get("winner") == focal_id


def extract_points(match: dict) -> List[dict]:
    history = match.get("history") or []
    points = []
    for point in history:
        raw_actions = point.get("actions") or []
        norm_actions = normalize_point_actions(raw_actions)
        term = terminal_action(norm_actions)
        net_raw = point.get("netChoices") or {}
        points.append(
            {
                "server": point["serverId"],
                "winner": point["pointWinnerId"],
                "loser": point.get("pointLoserId"),
                "receiver": point.get("receiverId"),
                "rally_length": int(point.get("rallyLength", 0)),
                "actions": [a["type"] for a in norm_actions],
                "actions_detail": norm_actions,
                "terminal_type": term["type"] if term else "",
                "terminal_actor": term.get("actor_id") if term else None,
                "net": net_raw,
            }
        )
    return points


def match_player_ids(match: dict) -> List[str]:
    players = match.get("players") or {}
    return list(players.keys())
