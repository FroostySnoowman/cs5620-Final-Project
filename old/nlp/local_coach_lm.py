"""
Tiny local word bigram + synonym shimmy—no network, no API.

Optional surface variation only; does not invent match facts.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import DefaultDict, Dict, List, Set

from . import elite_voice as EV

_WORD = re.compile(r"[A-Za-z]+")


def _tokenize(s: str) -> List[str]:
    return _WORD.findall(s.lower())


def _default_corpus() -> List[str]:
    lines: List[str] = []
    for tup in (
        EV.ELITE_OPENERS,
        EV.ELITE_BRIDGES,
        EV.ELITE_CADENCES,
        EV.HOOK_HOT,
        EV.HOOK_COLD,
        EV.HOOK_NEUTRAL,
        EV.HOOK_SERVE_HEAVY,
        EV.HOOK_RETURN_CHANCEY,
        EV.HOOK_SHORT_RALLY_SHAPE,
    ):
        lines.extend(tup)
    return lines


class WordBigramModel:
    """Sparse bigram counts for light plausibility checks."""

    def __init__(self) -> None:
        self._succ: DefaultDict[str, Set[str]] = defaultdict(set)

    def fit(self, sentences: List[str]) -> None:
        for s in sentences:
            w = _tokenize(s)
            for a, b in zip(w, w[1:]):
                self._succ[a].add(b)

    def has_bigram(self, w1: str, w2: str) -> bool:
        return w2 in self._succ.get(w1, ())


_MODEL: WordBigramModel | None = None


def _model() -> WordBigramModel:
    global _MODEL
    if _MODEL is None:
        _MODEL = WordBigramModel()
        _MODEL.fit(_default_corpus())
    return _MODEL


def optional_local_shimmy(
    rng,
    text: str,
    *,
    p_apply: float = 0.34,
) -> str:
    """
    Replace a few words with synonyms when the change is weakly bigram-consistent
    with the elite corpus (otherwise keep original word).
    """
    if rng.random() > p_apply:
        return text
    m = _model()
    words = text.split()
    if len(words) < 6:
        return text
    idxs = [i for i, w in enumerate(words) if _WORD.match(w)]
    if not idxs:
        return text
    rng.shuffle(idxs)
    out = list(words)
    for i in idxs[:3]:
        raw = words[i]
        key = raw.lower().strip(".,;:!?—")
        alts = EV.SYNONYMS.get(key)
        if not alts:
            continue
        prev = _tokenize(out[i - 1])[-1] if i > 0 else "<s>"
        nxt_tok = _tokenize(out[i + 1])[0] if i + 1 < len(out) else "</s>"
        for alt in alts:
            if " " in alt.strip():
                continue
            a = alt.strip()
            if not a:
                continue
            ok_prev = m.has_bigram(prev, a) or prev == "<s>"
            ok_next = m.has_bigram(a, nxt_tok) or nxt_tok == "</s>"
            if ok_prev or ok_next:
                rep = alt
                if raw[:1].isupper():
                    rep = rep[:1].upper() + rep[1:]
                out[i] = rep
                break
    return " ".join(out)


def build_corpus_from_strings(strings: List[str]) -> None:
    """Extend bigram training (e.g. after loading extra templates)."""
    mod = _model()
    mod.fit(strings)
