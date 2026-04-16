"""
Combinatorial tennis coach lines from vocabulary pools (no LLM).
"""

from __future__ import annotations

import random
from typing import List

from . import tennis_vocabulary as V


def _pick(rng: random.Random, seq: tuple) -> str:
    return rng.choice(seq)


def synthesize_for_key(rng: random.Random, key: str, you: str, opp: str, n: int = 24) -> List[str]:
    """
    Generate ``n`` unique-ish lines for a tactical key using slot filling.
    """
    lines: List[str] = []
    key = key or ""

    for _ in range(n * 3):  # oversample, dedupe later
        if len(lines) >= n:
            break
        o = _pick(rng, V.OPENERS)
        if key in ("net_advantage", "volley_edge"):
            p = _pick(rng, V.PRESSURE_VERBS)
            nw = _pick(rng, V.NET_WORDS)
            m = _pick(rng, V.MOOD)
            c = _pick(rng, V.CLOSING_FRAGS)
            line = f"{o} use {nw} to {p} {opp} {m}—you're ahead in those numbers {c}"
        elif key in ("net_weakness", "volley_weakness"):
            d = _pick(rng, V.DEPTH_WORDS)
            c = _pick(rng, V.CLOSING_FRAGS)
            line = f"{o} keep {d} first—don't rush forward into {opp}'s comfort zone {c}"
        elif key in ("short_rally",):
            r = _pick(rng, V.RALLY_WORDS)
            c = _pick(rng, V.CLOSING_FRAGS)
            line = f"{o} {r} tilt your way—take time away early {c}"
        elif key in ("extend_vs_short",):
            r = _pick(rng, V.RALLY_WORDS)
            op = _pick(rng, V.OPP_PRESSURE)
            c = _pick(rng, V.CLOSING_FRAGS)
            line = f"{o} stretch {r}, {op}, and make {opp} work laterally {c}"
        elif key in ("first_serve_return",):
            rw = _pick(rng, V.RETURN_WORDS)
            c = _pick(rng, V.CLOSING_FRAGS)
            line = f"{o} lean on {rw} to blunt {opp}'s first delivery {c}"
        elif key in ("second_serve_risk",):
            sw = _pick(rng, V.SERVE_WORDS)
            c = _pick(rng, V.CLOSING_FRAGS)
            line = f"{o} protect {sw}—{opp} is hunting short seconds {c}"
        elif key in ("target_bh",):
            w = _pick(rng, V.WING_WORDS)
            p = _pick(rng, V.PRESSURE_VERBS)
            c = _pick(rng, V.CLOSING_FRAGS)
            line = f"{o} {p} {w} patterns and make {opp} defend on the move {c}"
        elif key in ("target_fh",):
            w = _pick(rng, V.WING_WORDS)
            p = _pick(rng, V.PRESSURE_VERBS)
            c = _pick(rng, V.CLOSING_FRAGS)
            line = f"{o} {p} {w} looks when the court opens {c}"
        elif key in ("forehand_eff_edge", "backhand_eff_edge"):
            w = _pick(rng, V.WING_WORDS)
            p = _pick(rng, V.PRESSURE_VERBS)
            c = _pick(rng, V.CLOSING_FRAGS)
            line = f"{o} the winner/error sheet favors your {w}—{p} that matchup {c}"
        else:
            d = _pick(rng, V.DEPTH_WORDS)
            p = _pick(rng, V.PRESSURE_VERBS)
            c = _pick(rng, V.CLOSING_FRAGS)
            line = f"{o} prioritize {d} and {p} {opp}'s weaknesses {c}"

        if line not in lines:
            lines.append(line)

    return lines[:n]
