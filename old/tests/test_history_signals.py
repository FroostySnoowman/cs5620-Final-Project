from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_match_narrative_context_shape():
    from analytics.history_signals import build_match_narrative_context
    from pipeline.parser import load_match

    m = load_match(ROOT / "data" / "raw_matches.json")
    ids = list(m["players"].keys())
    a, b = ids[0], ids[1]
    ctx = build_match_narrative_context(m, a, b)
    assert ctx["momentum"] in ("hot", "cold", "neutral")
    assert ctx["rally_shape"] in ("mostly_short", "mixed", "some_long")
    assert "rolling_win_rate" in ctx
    assert ctx["n_points"] > 0


def test_recommend_includes_narrative_context():
    from inference.predict import recommend_from_match
    from pipeline.parser import load_match

    m = load_match(ROOT / "data" / "raw_matches.json")
    ids = list(m["players"].keys())
    a, b = ids[0], ids[1]
    r = recommend_from_match(m, a, b, include_nlg=False, include_coach_voice=True, nlg_seed=3)
    assert "match_narrative_context" in r
    assert r["match_narrative_context"]["focal_id"] == a
