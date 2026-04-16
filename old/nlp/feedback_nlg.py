"""
Personalized feedback from structured analytics + model output.

Controlled NLG: phrase banks + seeded variation. No LLM required; pairs well with
your own NLP stack or an optional external generator (see `integration_payload`).
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

_OPENERS: Dict[str, List[str]] = {
    "net_advantage": [
        "Net profile: {you} holds the edge up front against {opp}.",
        "Up front, the matchup tilts toward {you}.",
    ],
    "net_weakness": [
        "{opp} has been the more efficient player at net in this sample.",
        "Net exchanges favor {opp} on paper—stay patient from the back.",
    ],
    "short_rally": [
        "Short points are a strength area for {you} here.",
        "When rallies stay compact, {you} tends to come out ahead.",
    ],
    "extend_vs_short": [
        "{opp} has the better short-point record—length helps {you}.",
        "Stretching the point is the safer script for {you}.",
    ],
    "first_serve_return": [
        "Return games offer a realistic pressure angle for {you}.",
        "First-serve return effectiveness is a lever for {you}.",
    ],
    "second_serve_risk": [
        "Second serves need extra protection against {opp}.",
        "{opp} capitalizes on second-ball looks—tighten patterns.",
    ],
    "target_bh": [
        "Error splits point to the backhand wing for {opp}.",
        "The backhand is the more attackable side for {opp}.",
    ],
    "target_fh": [
        "Forehand errors cluster more for {opp} in this data.",
        "The forehand is the more volatile wing for {opp}.",
    ],
}


def _pick(rng: random.Random, options: List[str]) -> str:
    return rng.choice(options)


def _model_paragraph(rng: random.Random, you: str, opp: str, pred: Dict[str, Any]) -> str:
    tactic = (pred.get("tactic") or "neutral").replace("_", " ")
    probs = pred.get("probs") or {}
    p = float(probs.get(pred.get("tactic", ""), 0.0))
    pct = f"{100.0 * p:.1f}%"
    intros = [
        (
            "The tactic model’s top pick is **{tactic}** (about {pct} of head weight)—"
            "use it alongside the stats above, not instead of them."
        ),
        (
            "Given how this match unfolded, the classifier leans **{tactic}** (~{pct}); "
            "cross-check with what you felt on court."
        ),
    ]
    return _pick(rng, intros).format(tactic=tactic, pct=pct, you=you, opp=opp)


def _fallback(rng: random.Random, you: str, opp: str) -> str:
    return _pick(
        rng,
        [
            f"The snapshot for {you} vs {opp} is fairly balanced on available metrics—prioritize clear patterns and serve intent.",
            f"No single stat dominates; for {you}, disciplined shot selection against {opp} matters most.",
        ],
    )


def render_personalized_feedback(
    recommendation_result: Dict[str, Any],
    *,
    you_label: Optional[str] = None,
    opp_label: Optional[str] = None,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Turn `recommend_from_match` output into varied prose + bullets.

    Same `seed` => same wording (good for tests and caching).
    """
    rng = random.Random(seed)
    you = you_label or recommendation_result.get("focal_player", "Player")
    opp = opp_label or recommendation_result.get("opponent", "Opponent")

    brief = recommendation_result.get("tactical_brief") or {}
    recs = sorted(
        brief.get("recommendations") or [],
        key=lambda x: x.get("priority", 99),
    )
    pred = recommendation_result.get("model_prediction") or {}

    paragraphs: List[str] = []
    bullets: List[str] = []

    for r in recs:
        key = str(r.get("key", ""))
        text = str(r.get("text", "")).strip()
        opener_list = _OPENERS.get(key)
        if opener_list:
            opener = _pick(rng, opener_list).format(you=you, opp=opp)
            para = f"{opener}\n{text}"
        else:
            para = text
        paragraphs.append(para)
        bullets.append(text[:220] + ("…" if len(text) > 220 else ""))

    if not paragraphs:
        paragraphs.append(_fallback(rng, you, opp))

    paragraphs.append(_model_paragraph(rng, you, opp, pred))

    unc = brief.get("uncertainty") or {}
    rnote = unc.get("rally_length_note")
    if rnote:
        paragraphs.append(str(rnote))

    headline = (
        f"Personalized plan: {you} vs {opp}"
        if recs
        else f"Match notes: {you} vs {opp}"
    )

    full = "\n\n".join(paragraphs)
    return {
        "headline": headline,
        "paragraphs": paragraphs,
        "bullets": bullets,
        "full_text": full,
        "tone": "analytical_coach",
        "variation_seed": seed,
        "method": "template_nlg_v1",
    }
