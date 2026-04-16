from collections import Counter
from typing import Any, Dict, List, Tuple

import numpy as np
import torch

from analytics.opponent_tactics import (
    CONTRAST_LEN,
    build_profile,
    contrast_vector,
    rally_length_advice_supported,
)
from pipeline.features import compute_state, init_rolling_stats, update_rolling_stats
from pipeline.labels import infer_tactic_label
from pipeline.parser import extract_points, match_player_ids


def build_interleaved_match_dataset(match: dict) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Two samples per point (focal p0 then p1), chronological order.
    Rolling stats updated once per point after both focals' rows are emitted.
    """
    ids = match_player_ids(match)
    if len(ids) < 2:
        raise ValueError("Match needs at least two players")
    p0, p1 = ids[0], ids[1]

    prof0 = build_profile(match, p0)
    prof1 = build_profile(match, p1)
    neutral_rally = not rally_length_advice_supported(match)
    c0 = contrast_vector(prof0, prof1, neutralize_rally_lengths=neutral_rally)
    c1 = contrast_vector(prof1, prof0, neutralize_rally_lengths=neutral_rally)

    s0 = init_rolling_stats(p0, net_prior=prof0.net_rate)
    s1 = init_rolling_stats(p1, net_prior=prof1.net_rate)

    points = extract_points(match)
    xs: List[np.ndarray] = []
    ys: List[int] = []

    for p in points:
        x0 = compute_state(p, s0, c0)
        y0 = infer_tactic_label(p, p0)
        x1 = compute_state(p, s1, c1)
        y1 = infer_tactic_label(p, p1)
        xs.extend([x0, x1])
        ys.extend([y0, y1])
        update_rolling_stats(s0, p)
        update_rolling_stats(s1, p)

    X = np.stack(xs, axis=0).astype(np.float32)
    y = np.array(ys, dtype=np.int64)
    meta = {
        "n_points": len(points),
        "n_samples": int(X.shape[0]),
        "input_dim": int(X.shape[1]),
        "contrast_len": CONTRAST_LEN,
        "label_counts": dict(Counter(y.tolist())),
        "players": (p0, p1),
        "rally_length_advice_supported": not neutral_rally,
        "rally_contrast_neutralized": neutral_rally,
    }
    return X, y, meta


def build_focal_samples(
    match: dict,
    focal_id: str,
    opponent_id: str,
) -> Tuple[np.ndarray, np.ndarray]:
    """Single focal perspective; one row per point (for inference / debugging)."""
    self_p = build_profile(match, focal_id)
    opp_p = build_profile(match, opponent_id)
    neutral_rally = not rally_length_advice_supported(match)
    cvec = contrast_vector(self_p, opp_p, neutralize_rally_lengths=neutral_rally)

    stats = init_rolling_stats(focal_id, net_prior=self_p.net_rate)
    points = extract_points(match)
    xs: List[np.ndarray] = []
    ys: List[int] = []

    for p in points:
        x = compute_state(p, stats, cvec)
        y = infer_tactic_label(p, focal_id)
        xs.append(x)
        ys.append(y)
        update_rolling_stats(stats, p)

    X = np.stack(xs, axis=0).astype(np.float32)
    y = np.array(ys, dtype=np.int64)
    return X, y


def time_ordered_split(
    X: np.ndarray,
    y: np.ndarray,
    n_points: int,
    val_ratio: float = 0.15,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Split by point index: each point contributes two consecutive rows (p0, p1).
    First (1 - val_ratio) points -> train; remainder -> validation.
    """
    if n_points < 2:
        raise ValueError("Need at least 2 points for split")
    split_pt = max(1, int(n_points * (1.0 - val_ratio)))
    split_idx = split_pt * 2
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    if X_val.shape[0] == 0:
        X_val, y_val = X_train[-2:], y_train[-2:]
        X_train, y_train = X_train[:-2], y_train[:-2]
    return (
        torch.from_numpy(X_train),
        torch.from_numpy(y_train),
        torch.from_numpy(X_val),
        torch.from_numpy(y_val),
    )


def build_match_tensors(
    match: dict,
    val_ratio: float = 0.15,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, Dict[str, Any]]:
    X, y, meta = build_interleaved_match_dataset(match)
    n_points = meta["n_points"]
    X_train, y_train, X_val, y_val = time_ordered_split(X, y, n_points, val_ratio)
    meta = {
        **meta,
        "n_train": int(X_train.shape[0]),
        "n_val": int(X_val.shape[0]),
        "label_counts_train": dict(Counter(y_train.numpy().tolist())),
        "label_counts_val": dict(Counter(y_val.numpy().tolist())),
    }
    return X_train, y_train, X_val, y_val, meta
