"""
Scenario-conditioned paragraph composition: narrative context × tactical lines.

Combinatorial richness: multiple independent slot draws per paragraph; see
``estimate_coach_combinatorics``.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from . import elite_voice as EV


def _pick(rng: random.Random, options: tuple) -> str:
    return rng.choice(options)


def narrative_hook(rng: random.Random, ctx: Dict[str, Any]) -> Optional[str]:
    """Optional first sentence tied to momentum / clutch / rally shape (no fake point scores)."""
    if not ctx:
        return None
    clutch = ctx.get("clutch") or {}
    # Weighted draw
    r = rng.random()

    if r < 0.12 and clutch.get("serve_bucket") == "heavy_pressure":
        return _pick(rng, EV.HOOK_SERVE_HEAVY)
    if r < 0.12 and clutch.get("return_bucket") == "many_chances":
        return _pick(rng, EV.HOOK_RETURN_CHANCEY)
    if r < 0.1 and ctx.get("rally_shape") == "mostly_short":
        return _pick(rng, EV.HOOK_SHORT_RALLY_SHAPE)

    m = ctx.get("momentum") or "neutral"
    if m == "hot":
        return _pick(rng, EV.HOOK_HOT) if rng.random() < 0.55 else None
    if m == "cold":
        return _pick(rng, EV.HOOK_COLD) if rng.random() < 0.55 else None
    return _pick(rng, EV.HOOK_NEUTRAL) if rng.random() < 0.4 else None


def compose_elite_paragraph(
    rng: random.Random,
    ctx: Dict[str, Any],
    you: str,
    opp: str,
    core_line: str,
) -> str:
    """
    Wrap a tactical core line with elite-tone slots (opener/bridge/cadence) and optional hook.
    ``core_line`` already includes {you}/{opp} if needed.
    """
    parts: List[str] = []
    hook = narrative_hook(rng, ctx)
    if hook:
        parts.append(hook)

    o = _pick(rng, EV.ELITE_OPENERS)
    if rng.random() < 0.52:
        merged = f"{o} {core_line}"
    else:
        b = _pick(rng, EV.ELITE_BRIDGES)
        merged = f"{o} {b} {core_line}"

    if rng.random() < 0.58:
        merged = f"{merged} {_pick(rng, EV.ELITE_CADENCES)}"

    parts.append(merged)
    return " ".join(parts)


def scenario_id(ctx: Dict[str, Any]) -> str:
    """Compact key for debugging / integration payloads."""
    if not ctx:
        return "default"
    return "|".join(
        [
            str(ctx.get("momentum", "?")),
            str(ctx.get("return_pressure_bucket", "?")),
            str(ctx.get("serve_pressure_bucket", "?")),
            str(ctx.get("rally_shape", "?")),
            str((ctx.get("clutch") or {}).get("serve_bucket", "?")),
        ]
    )


def estimate_coach_combinatorics() -> Dict[str, Any]:
    """
    Documented combinatorial scale: slot product × tactic pools × ordering.

    A single body paragraph can exceed 10^6 paths (openers × bridges × cadences
    × hooks × merged tactic lines); a full letter multiplies paragraph choices
    and shuffle order.
    """
    n_opener = len(EV.ELITE_OPENERS)
    n_bridge = len(EV.ELITE_BRIDGES)
    n_cad = len(EV.ELITE_CADENCES)
    n_hook_families = 5  # hot/cold/neutral + serve/return/rally specials
    # Rough paths per paragraph before tactic text (optional hook × structure × cadence)
    per_para_slots = (
        n_hook_families * n_opener * (1 + n_bridge) * 2 * n_cad
    )
    tactic_pool_conservative = 250  # merged template + synth lines per key
    per_paragraph_lower_bound = per_para_slots * tactic_pool_conservative
    return {
        "per_paragraph_template_slot_product": int(per_para_slots),
        "per_paragraph_with_tactic_pool_lower_bound": int(per_paragraph_lower_bound),
        "meets_million_plus_per_paragraph": per_paragraph_lower_bound >= 1_000_000,
        "slot_counts": {
            "elite_openers": n_opener,
            "elite_bridges": n_bridge,
            "elite_cadences": n_cad,
            "tactic_pool_assumption": tactic_pool_conservative,
        },
    }
