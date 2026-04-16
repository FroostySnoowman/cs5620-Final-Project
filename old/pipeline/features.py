import numpy as np
from typing import Any, Dict


def init_rolling_stats(
    player: str,
    net_prior: float = 0.5,
) -> Dict[str, Any]:
    return {
        "player": player,
        "points": 0,
        "wins": 0,
        "serve_played": 0,
        "serve_won": 0,
        "return_played": 0,
        "return_won": 0,
        "net_played": 0,
        "net_won": 0,
        "avg_rally_length": 0.0,
        "net_prior": float(net_prior),
    }


def _safe_rate(num: int, den: int) -> float:
    if den <= 0:
        return 0.0
    return num / den


def rolling_rates(stats: Dict[str, Any]) -> Dict[str, float]:
    serve_wr = _safe_rate(stats["serve_won"], stats["serve_played"])
    ret_wr = _safe_rate(stats["return_won"], stats["return_played"])
    if stats["net_played"] > 0:
        net_wr = _safe_rate(stats["net_won"], stats["net_played"])
    else:
        net_wr = stats["net_prior"]
    return {
        "serve_win_rate": serve_wr,
        "return_win_rate": ret_wr,
        "net_win_rate": net_wr,
        "avg_rally_length": float(stats["avg_rally_length"]),
    }


def compute_state(
    point: dict,
    rolling_stats: Dict[str, Any],
    contrast: np.ndarray,
) -> np.ndarray:
    """
    State vector = [rolling features (6) | static contrast (K)].
    """
    r = rolling_rates(rolling_stats)
    base = np.array(
        [
            r["serve_win_rate"],
            r["return_win_rate"],
            r["avg_rally_length"],
            r["net_win_rate"],
            float(point["rally_length"]),
            float(int(point["server"] == rolling_stats["player"])),
        ],
        dtype=np.float32,
    )
    c = np.asarray(contrast, dtype=np.float32).ravel()
    return np.concatenate([base, c], axis=0)


def update_rolling_stats(stats: Dict[str, Any], point: dict) -> Dict[str, Any]:
    pid = stats["player"]
    stats["points"] += 1
    if point["winner"] == pid:
        stats["wins"] += 1

    n = stats["points"]
    stats["avg_rally_length"] = (
        stats["avg_rally_length"] * (n - 1) + float(point["rally_length"])
    ) / n

    if point["server"] == pid:
        stats["serve_played"] += 1
        if point["winner"] == pid:
            stats["serve_won"] += 1
    else:
        stats["return_played"] += 1
        if point["winner"] == pid:
            stats["return_won"] += 1

    net = point.get("net") or {}
    if net.get(pid) is True:
        stats["net_played"] += 1
        if point["winner"] == pid:
            stats["net_won"] += 1

    return stats
