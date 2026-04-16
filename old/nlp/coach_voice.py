"""
Warm, second-person coach voice—template NLG only (no LLMs).

High entropy: phrase banks, shuffled insight order, session_nonce mixed into RNG.
"""

from __future__ import annotations

import hashlib
import random
import secrets
from typing import Any, Dict, List, Optional

from .coach_scenarios import compose_elite_paragraph, scenario_id
from .lexicon_loader import extra_lines_for_key, load_optional_lexicon
from .line_synthesizer import synthesize_for_key
from .local_coach_lm import optional_local_shimmy

# Maps tactic id name -> plain coaching imperative
_TACTIC_COACH: Dict[str, str] = {
    "aggressive": "When you get a look, take time away and swing with conviction.",
    "neutral": "Stay patient—let the point come to you and avoid silly errors.",
    "approach_net": "If you get a short ball you like, come forward and finish at net.",
    "extend_rally": "When the point opens up, make them play one more ball.",
}

_COACH_LINES: Dict[str, List[str]] = {
    "net_advantage": [
        "You win more up there than {opp} does—that's your green light to approach when the ball sits short.",
        "Net is where you tilt the match. Look for chances to move in and keep volleys simple.",
        "Own the front of the court when you can—you're winning that battle on paper.",
    ],
    "net_weakness": [
        "{opp} is comfortable up front, so don't donate cheap approaches. Keep depth and make them beat you from the back first.",
        "I'd rather you stay patient than rush the net into their strength. Force long balls before you come in.",
    ],
    "short_rally": [
        "You like the quick points—take the return early and don't let rallies drag when you're ahead in those exchanges.",
        "First-strike tennis suits you here. Look to step in on the right ball.",
    ],
    "extend_vs_short": [
        "{opp} wins the quick ones—your job is to stretch the point and move them side to side.",
        "Let the rally breathe. Depth and margin beat trying to end it in two shots.",
    ],
    "first_serve_return": [
        "On their first serve you can still create pressure—block deep, change pace, and don't give free points.",
        "Return with intent: even neutral returns that land deep buy you looks on the next ball.",
    ],
    "second_serve_risk": [
        "Protect your second ball—mix location and spin so {opp} can't tee off.",
        "First-serve percentage matters here; predictable kick seconds will get attacked.",
    ],
    "target_bh": [
        "I'd keep testing the backhand—make them hit it on the run.",
        "Patterns that finish to the backhand wing are your friend in neutral rallies.",
    ],
    "target_fh": [
        "The forehand side is where errors show up for them—don't be shy about opening that wing.",
        "Pressure the forehand when you get a short ball to that side.",
    ],
    "volley_edge": [
        "Your volley results look stronger than theirs—when you get a ball at net, trust your hands.",
        "Finish points at net when you can; you're converting better on volleys in this sample.",
    ],
    "volley_weakness": [
        "Their volleys are cleaner than yours on the sheet—don't feed them easy mid-court balls to pick off.",
        "Stay back a touch longer unless the approach is obvious; they're sharp up front.",
    ],
    "forehand_eff_edge": [
        "The forehand winner/error ledger tilts your way—run patterns that let you open up on that wing.",
        "You can trust your forehand a bit more in this matchup when you get a look.",
    ],
    "backhand_eff_edge": [
        "Backhand balance favors you here—use depth to the backhand to set up the next ball.",
        "Your backhand is doing more damage than theirs in the aggregates—don't hide it.",
    ],
}

_GREETINGS = [
    "Hey {first_name},\n\nI've been through the numbers from you and {opp}. Here's how I'd talk to you before you go back out.",
    "{first_name},\n\nGood work getting this on paper. Against {opp}, here's what I'd want you feeling.",
    "Alright {first_name},\n\nQuick read on you versus {opp}—keep it simple and trust the trends below.",
    "{first_name},\n\nHere's the straight talk before you step on court with {opp}.",
]

_CLOSERS = [
    "Stay simple, trust what works, and adjust if they change patterns mid-match.",
    "One pattern at a time—don't try to do everything in the first game.",
    "Small adjustments beat big overhauls—lock one theme, then build.",
    "Win the boring points first; the flashy ones show up after.",
]

_SIGN_OFFS = [
    "You've got this. See you on the practice court.",
    "Play loose, play smart. Rooting for you.",
    "Go get it.",
    "Hands up, eyes quiet—play your game.",
]


def _first_name(display_name: str) -> str:
    parts = (display_name or "there").strip().split()
    return parts[0] if parts else "there"


def _pick(rng: random.Random, options: List[str]) -> str:
    return rng.choice(options)


def _tactic_one_thing(pred: Dict[str, Any]) -> str:
    t = (pred.get("tactic") or "neutral").lower()
    return _TACTIC_COACH.get(t, _TACTIC_COACH["neutral"])


def coach_rng_seed(
    base_seed: Optional[int],
    session_nonce: Optional[str],
    you: str,
    opp: str,
    run_entropy: str = "",
) -> int:
    """Stable per-session RNG from seed + nonce + players + optional entropy (no LLMs)."""
    payload = f"{base_seed}|{session_nonce or ''}|{you}|{opp}|{run_entropy}".encode(
        "utf-8"
    )
    h = hashlib.sha256(payload).digest()
    return int.from_bytes(h[:8], "big") % (2**31)


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _merge_lines_for_key(
    rng: random.Random, key: str, you: str, opp: str
) -> List[str]:
    """Built-ins + optional JSON lexicon + combinatorial lines."""
    merged: List[str] = []
    for line in _COACH_LINES.get(key, []):
        merged.append(line.format(you=you, opp=opp))
    for line in extra_lines_for_key(key):
        try:
            merged.append(line.format(you=you, opp=opp))
        except (KeyError, ValueError):
            merged.append(line)
    merged.extend(synthesize_for_key(rng, key, you, opp, n=48))
    return _dedupe_preserve_order(merged)


def _fallback(rng: random.Random, you: str, opp: str) -> str:
    return _pick(
        rng,
        [
            f"The matchup looks fairly even on what we can see—serve with clarity and build points rather than forcing winners early.",
            f"Against {opp}, I'd emphasize high-percentage tennis first; let the openings appear.",
        ],
    )


def render_coach_voice(
    recommendation_result: Dict[str, Any],
    *,
    you_label: Optional[str] = None,
    opp_label: Optional[str] = None,
    seed: Optional[int] = None,
    session_nonce: Optional[str] = None,
    run_entropy: Optional[str] = None,
    local_coach_lm: bool = False,
) -> Dict[str, Any]:
    """
    Build a coach letter from ``recommend_from_match`` output.

    ``session_nonce`` (e.g. UUID from your app) mixes with ``seed`` so repeat
    sessions don't get identical copy. Insight paragraphs are shuffled for variety.

    When both ``seed`` and ``session_nonce`` are omitted, a fresh ``run_entropy``
    token is generated so back-to-back CLI runs don't repeat the same letter.
    Pass ``--seed`` for reproducible wording.
    """
    you = you_label or recommendation_result.get("focal_player", "Player")
    opp = opp_label or recommendation_result.get("opponent", "Opponent")

    resolved_entropy = run_entropy
    if resolved_entropy is None:
        if seed is None and session_nonce is None:
            resolved_entropy = secrets.token_hex(16)
        else:
            resolved_entropy = ""

    rng = random.Random(
        coach_rng_seed(seed, session_nonce, you, opp, resolved_entropy)
    )
    fn = _first_name(you)

    lex = load_optional_lexicon()
    greetings = list(_GREETINGS)
    for g in lex.get("greetings") or []:
        if isinstance(g, str) and g.strip():
            greetings.append(g)
    closers = list(_CLOSERS)
    for c in lex.get("closers") or []:
        if isinstance(c, str) and c.strip():
            closers.append(c)
    sign_offs = list(_SIGN_OFFS)
    for s in lex.get("sign_offs") or []:
        if isinstance(s, str) and s.strip():
            sign_offs.append(s)

    brief = recommendation_result.get("tactical_brief") or {}
    recs = sorted(
        brief.get("recommendations") or [],
        key=lambda x: x.get("priority", 99),
    )
    pred = recommendation_result.get("model_prediction") or {}
    nctx: Dict[str, Any] = recommendation_result.get("match_narrative_context") or {}

    body_paras: List[str] = []
    for r in recs[:6]:
        key = str(r.get("key", ""))
        merged = _merge_lines_for_key(rng, key, you, opp)
        if merged:
            core = _pick(rng, merged)
            if rng.random() < 0.78:
                para = compose_elite_paragraph(rng, nctx, you, opp, core)
            else:
                para = core
            if local_coach_lm:
                para = optional_local_shimmy(rng, para)
            body_paras.append(para)
        else:
            t = str(r.get("text", "")).strip()
            if t:
                if rng.random() < 0.65:
                    t = compose_elite_paragraph(rng, nctx, you, opp, t)
                if local_coach_lm:
                    t = optional_local_shimmy(rng, t)
                body_paras.append(t)

    if not body_paras:
        fb = _fallback(rng, you, opp)
        body_paras.append(
            compose_elite_paragraph(rng, nctx, you, opp, fb)
            if rng.random() < 0.75
            else fb
        )

    rng.shuffle(body_paras)

    if not brief.get("rally_length_advice_included", True):
        rl_note = (
            "We're not leaning on rally-length strategy from this data—every point here was "
            "one or two shots—so trust the other cues above."
        )
        if rng.random() < 0.5:
            rl_note = compose_elite_paragraph(rng, nctx, you, opp, rl_note)
        if local_coach_lm:
            rl_note = optional_local_shimmy(rng, rl_note)
        body_paras.append(rl_note)

    greeting = _pick(rng, greetings).format(first_name=fn, opp=opp)
    middle = "\n\n".join(body_paras)

    if recs:
        k0 = str(recs[0].get("key", ""))
        merged0 = _merge_lines_for_key(rng, k0, you, opp)
        if merged0:
            raw_one = _pick(rng, merged0)
            the_one = (
                compose_elite_paragraph(rng, nctx, you, opp, raw_one)
                if rng.random() < 0.55
                else raw_one
            )
        else:
            the_one = _tactic_one_thing(pred)
    else:
        the_one = _tactic_one_thing(pred)

    if local_coach_lm:
        the_one = optional_local_shimmy(rng, the_one, p_apply=0.28)

    closer = _pick(rng, closers)
    sign_off = _pick(rng, sign_offs)

    coach_letter = "\n\n".join(
        [
            greeting,
            middle,
            f"If you only remember one thing: {the_one}",
            closer,
            sign_off,
        ]
    )

    return {
        "coach_letter": coach_letter,
        "the_one_thing": the_one.strip(),
        "sign_off": sign_off,
        "variation_seed": seed,
        "session_nonce": session_nonce,
        "run_entropy": resolved_entropy if resolved_entropy else None,
        "scenario_id": scenario_id(nctx),
        "local_coach_lm": local_coach_lm,
        "method": "coach_voice_v3_elite_scenario",
    }


def coach_letter_banned_terms_present(text: str) -> List[str]:
    banned = [
        "classifier",
        "probabilities",
        "head weight",
        "logits",
        "tensor",
        "gpt",
        "openai",
        "llm",
        "neural net",
        "chatgpt",
        "anthropic",
        "api key",
    ]
    found = []
    lower = text.lower()
    for b in banned:
        if b in lower:
            found.append(b)
    return found
