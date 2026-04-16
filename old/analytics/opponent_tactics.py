"""
Aggregate opponent / self profiles and contrast features for tactics (no LLM).

Rates use additive smoothing: (wins + alpha) / (played + 2*alpha) to avoid 0/0.
"""

from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np

from pipeline.parser import extract_points

SMOOTH_ALPHA = 1.0

# Contrast indices 2–5 are short/long rally win rates (self/opp pairs).
RALLY_CONTRAST_SLICE = slice(2, 6)
RALLY_NEUTRAL_VALUE = 0.5


def rally_length_advice_supported(match: dict) -> bool:
    """
    True only if point history contains at least one rally with length > 2.

    If every point is 1–2 shots, aggregate short/medium/long buckets are not
    useful for "extend vs shorten" tactics; skip those recommendations and
    neutralize rally contrast features for ML.
    """
    pts = extract_points(match)
    if not pts:
        return False
    return any(int(p["rally_length"]) > 2 for p in pts)


def _smoothed_rate(won: int, played: int, alpha: float = SMOOTH_ALPHA) -> float:
    if played < 0 or won < 0:
        return 0.0
    return (won + alpha) / (played + 2.0 * alpha)


@dataclass
class PlayerProfile:
    player_id: str
    net_rate: float
    short_rally_rate: float
    medium_rally_rate: float
    long_rally_rate: float
    first_serve_return_rate: float
    second_serve_return_rate: float
    unforced_error_rate: float
    points_won_rate: float
    break_conv_rate: float
    fh_error_rate: float
    bh_error_rate: float
    # Aggregate stroke efficacy (winners vs errors on that stroke), smoothed
    fh_shot_eff: float
    bh_shot_eff: float
    volley_shot_eff: float
    oh_shot_eff: float
    n_points: int


def _get_block(players: dict, pid: str, key: str) -> dict:
    return (players.get(pid) or {}).get(key) or {}


def build_profile(match: dict, player_id: str) -> PlayerProfile:
    players = match.get("players") or {}
    serve = _get_block(players, player_id, "serve")
    ret = _get_block(players, player_id, "return")
    rally = _get_block(players, player_id, "rally")
    ind = _get_block(players, player_id, "individualMatch")

    net_w = int(rally.get("netPointsWon") or 0)
    net_a = int(rally.get("netPointsAttempted") or 0)
    sw = int(ind.get("rallyShortWon") or 0)
    sp = int(ind.get("rallyShortPlayed") or 0)
    mw = int(ind.get("rallyMediumWon") or 0)
    mp = int(ind.get("rallyMediumPlayed") or 0)
    lw = int(ind.get("rallyLongWon") or 0)
    lp = int(ind.get("rallyLongPlayed") or 0)

    fsw = int(ret.get("firstServeReturnPointsWon") or 0)
    fsp = int(ret.get("firstServeReturnPointsPlayed") or 0)
    ssw = int(ret.get("secondServeReturnPointsWon") or 0)
    ssp = int(ret.get("secondServeReturnPointsPlayed") or 0)

    ufe = int(rally.get("unforcedErrors") or 0)
    pts_w = int(ind.get("pointsWon") or 0)
    pts_p = int(ind.get("pointsPlayed") or 0)

    bp_c = int(ret.get("breakPointsConverted") or 0)
    bp_o = int(ret.get("breakPointOpportunities") or 0)

    fh_e = int(rally.get("forehandErrors") or 0)
    bh_e = int(rally.get("backhandErrors") or 0)
    stroke_denom = max(fh_e + bh_e, 1)

    fh_w = int(rally.get("forehandWinners") or 0)
    bh_w = int(rally.get("backhandWinners") or 0)
    vw = int(rally.get("volleyWinners") or 0)
    ve = int(rally.get("volleyErrors") or 0)
    ohw = int(rally.get("overheadWinners") or 0)
    ohe = int(rally.get("overheadErrors") or 0)

    fh_shot_eff = _smoothed_rate(fh_w, fh_w + fh_e) if fh_w + fh_e > 0 else 0.5
    bh_shot_eff = _smoothed_rate(bh_w, bh_w + bh_e) if bh_w + bh_e > 0 else 0.5
    volley_shot_eff = _smoothed_rate(vw, vw + ve) if vw + ve > 0 else 0.5
    oh_shot_eff = _smoothed_rate(ohw, ohw + ohe) if ohw + ohe > 0 else 0.5

    return PlayerProfile(
        player_id=player_id,
        net_rate=_smoothed_rate(net_w, net_a),
        short_rally_rate=_smoothed_rate(sw, sp),
        medium_rally_rate=_smoothed_rate(mw, mp),
        long_rally_rate=_smoothed_rate(lw, lp),
        first_serve_return_rate=_smoothed_rate(fsw, fsp),
        second_serve_return_rate=_smoothed_rate(ssw, ssp),
        unforced_error_rate=_smoothed_rate(ufe, max(pts_p, 1)),
        points_won_rate=_smoothed_rate(pts_w, pts_p),
        break_conv_rate=_smoothed_rate(bp_c, bp_o),
        fh_error_rate=fh_e / stroke_denom,
        bh_error_rate=bh_e / stroke_denom,
        fh_shot_eff=fh_shot_eff,
        bh_shot_eff=bh_shot_eff,
        volley_shot_eff=volley_shot_eff,
        oh_shot_eff=oh_shot_eff,
        n_points=pts_p,
    )


CONTRAST_LEN = 19


def contrast_vector(
    self_profile: PlayerProfile,
    opp_profile: PlayerProfile,
    neutralize_rally_lengths: bool = False,
) -> np.ndarray:
    """Fixed-length vector for model input (self vs opponent strengths)."""
    v = np.array(
        [
            self_profile.net_rate,
            opp_profile.net_rate,
            self_profile.short_rally_rate,
            opp_profile.short_rally_rate,
            self_profile.long_rally_rate,
            opp_profile.long_rally_rate,
            self_profile.first_serve_return_rate,
            opp_profile.first_serve_return_rate,
            self_profile.second_serve_return_rate,
            opp_profile.second_serve_return_rate,
            self_profile.unforced_error_rate,
            opp_profile.unforced_error_rate,
            self_profile.points_won_rate - opp_profile.points_won_rate,
            self_profile.fh_shot_eff,
            opp_profile.fh_shot_eff,
            self_profile.bh_shot_eff,
            opp_profile.bh_shot_eff,
            self_profile.volley_shot_eff,
            opp_profile.volley_shot_eff,
        ],
        dtype=np.float32,
    )
    if neutralize_rally_lengths:
        v[RALLY_CONTRAST_SLICE] = RALLY_NEUTRAL_VALUE
    return v


def low_sample_warning(profile: PlayerProfile, threshold: int = 40) -> bool:
    return profile.n_points < threshold


def build_tactical_brief(
    self_profile: PlayerProfile,
    opp_profile: PlayerProfile,
    self_name: str = "You",
    opp_name: str = "Opponent",
    include_rally_length_advice: bool = True,
) -> Dict[str, Any]:
    """
    Structured + template lines (deterministic). uncertainty flags when N is small.

    When include_rally_length_advice is False (e.g. all points in history are
    1–2 shots), omit short-rally / extend-rally recommendations.
    """
    lines: List[str] = []
    recs: List[Dict[str, Any]] = []

    def add_line(text: str, key: str, priority: int, data: dict):
        lines.append(text)
        recs.append({"key": key, "priority": priority, "text": text, **data})

    net_delta = self_profile.net_rate - opp_profile.net_rate
    if net_delta > 0.08:
        add_line(
            f"{self_name} net win rate ({self_profile.net_rate:.1%}) exceeds "
            f"{opp_name} ({opp_profile.net_rate:.1%}); favor approaches and net finishes when neutral.",
            "net_advantage",
            1,
            {"metric": "net_delta", "value": float(net_delta)},
        )
    elif net_delta < -0.08:
        add_line(
            f"{opp_name} is stronger at net ({opp_profile.net_rate:.1%} vs {self_profile.net_rate:.1%}); "
            f"keep them deep and avoid low-percentage net approaches.",
            "net_weakness",
            2,
            {"metric": "net_delta", "value": float(net_delta)},
        )

    if include_rally_length_advice:
        short_delta = self_profile.short_rally_rate - opp_profile.short_rally_rate
        if abs(short_delta) > 0.05:
            if short_delta > 0:
                add_line(
                    f"Short rallies favor {self_name} ({self_profile.short_rally_rate:.1%} vs "
                    f"{opp_profile.short_rally_rate:.1%}); take the ball early and shorten points.",
                    "short_rally",
                    1,
                    {"metric": "short_delta", "value": float(short_delta)},
                )
            else:
                add_line(
                    f"{opp_name} wins short points more often; extend rallies (your long: "
                    f"{self_profile.long_rally_rate:.1%}, theirs: {opp_profile.long_rally_rate:.1%}).",
                    "extend_vs_short",
                    2,
                    {"metric": "short_delta", "value": float(short_delta)},
                )

    fs_ret_gap = self_profile.first_serve_return_rate - opp_profile.first_serve_return_rate
    if fs_ret_gap > 0.05:
        add_line(
            f"Pressure {opp_name}'s first serve: your first-serve return win rate "
            f"({self_profile.first_serve_return_rate:.1%}) is higher than their return on your first "
            f"({opp_profile.first_serve_return_rate:.1%}).",
            "first_serve_return",
            3,
            {"metric": "fs_ret_gap", "value": float(fs_ret_gap)},
        )

    if opp_profile.second_serve_return_rate > 0.45:
        add_line(
            f"{opp_name} punishes second serves ({opp_profile.second_serve_return_rate:.1%}); "
            f"raise first-serve percentage and avoid predictable second patterns.",
            "second_serve_risk",
            2,
            {"metric": "opp_2nd_ret", "value": float(opp_profile.second_serve_return_rate)},
        )

    if opp_profile.fh_error_rate + opp_profile.bh_error_rate > 0.02:
        if opp_profile.bh_error_rate > opp_profile.fh_error_rate + 0.05:
            add_line(
                f"{opp_name} error split suggests more backhand errors than forehand; "
                f"probe the backhand wing in neutral rallies.",
                "target_bh",
                3,
                {
                    "opp_bh_share": float(
                        opp_profile.bh_error_rate / max(opp_profile.fh_error_rate + opp_profile.bh_error_rate, 1e-6)
                    ),
                },
            )
        elif opp_profile.fh_error_rate > opp_profile.bh_error_rate + 0.05:
            add_line(
                f"{opp_name} error split suggests more forehand errors; test the forehand under pressure.",
                "target_fh",
                3,
                {},
            )

    # Stroke efficacy edges from aggregate winner/error splits (per-shot buckets).
    v_delta = self_profile.volley_shot_eff - opp_profile.volley_shot_eff
    fh_delta = self_profile.fh_shot_eff - opp_profile.fh_shot_eff
    bh_delta = self_profile.bh_shot_eff - opp_profile.bh_shot_eff

    if abs(v_delta) > 0.05:
        if v_delta > 0:
            add_line(
                f"Volley efficacy favors {self_name} ({self_profile.volley_shot_eff:.1%} vs "
                f"{opp_profile.volley_shot_eff:.1%}); look to finish at net when volleys appear.",
                "volley_edge",
                2,
                {"metric": "volley_delta", "value": float(v_delta)},
            )
        else:
            add_line(
                f"{opp_name} is stronger on volleys ({opp_profile.volley_shot_eff:.1%} vs "
                f"{self_profile.volley_shot_eff:.1%}); avoid low-percentage net rushers.",
                "volley_weakness",
                2,
                {"metric": "volley_delta", "value": float(v_delta)},
            )

    if abs(fh_delta) > 0.05:
        add_line(
            f"Forehand winner/error balance tilts toward {self_name if fh_delta > 0 else opp_name} "
            f"({self_profile.fh_shot_eff:.1%} vs {opp_profile.fh_shot_eff:.1%}).",
            "forehand_eff_edge",
            4,
            {"metric": "fh_delta", "value": float(fh_delta)},
        )

    if abs(bh_delta) > 0.05:
        add_line(
            f"Backhand winner/error balance tilts toward {self_name if bh_delta > 0 else opp_name} "
            f"({self_profile.bh_shot_eff:.1%} vs {opp_profile.bh_shot_eff:.1%}).",
            "backhand_eff_edge",
            4,
            {"metric": "bh_delta", "value": float(bh_delta)},
        )

    unc_self = low_sample_warning(self_profile)
    unc_opp = low_sample_warning(opp_profile)
    summary = " ".join(lines) if lines else (
        "Profiles are balanced on available aggregates; prioritize high-percentage patterns and serve placement."
    )

    rally_note = None
    if not include_rally_length_advice:
        rally_note = (
            "Rally-length tactics omitted: every point in this match was 1–2 shots, "
            "so extend/shorten recommendations are not supported."
        )

    return {
        "lines": lines,
        "recommendations": sorted(recs, key=lambda x: x["priority"]),
        "summary": summary,
        "rally_length_advice_included": include_rally_length_advice,
        "uncertainty": {
            "self_low_n": unc_self,
            "opponent_low_n": unc_opp,
            "note": "Aggregate stats are match-level; multi-match data improves confidence."
            if (unc_self or unc_opp)
            else None,
            "rally_length_note": rally_note,
        },
    }
