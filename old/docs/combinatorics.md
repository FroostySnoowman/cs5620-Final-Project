# Coach letter combinatorics (no API LLMs)

The elite coach path combines:

1. **Tactical pools** — built-in lines, optional `nlp/data/tennis_lexicon.json`, and combinatorial lines from `line_synthesizer` (many slots per tactical key).
2. **Scenario slots** — `nlp/elite_voice.py` openers, bridges, cadences, and momentum/clutch hooks from `match_narrative_context` (`analytics/history_signals.py`).
3. **Ordering** — up to six body paragraphs are shuffled; greeting, closer, and sign-off are sampled independently.
4. **Entropy** — unseeded runs use `run_entropy` so repeated CLI calls differ.

Call `estimate_coach_combinatorics()` in `nlp.coach_scenarios` for documented lower bounds. The per-paragraph slot product × a conservative tactic pool **exceeds 10^6** paths before counting full-letter ordering.

Optional **`--local-coach-lm`** applies on-device synonym shims (`nlp/local_coach_lm.py`) — still no network or API.
