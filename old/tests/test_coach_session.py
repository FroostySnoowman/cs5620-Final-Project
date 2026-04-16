from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_coach_differs_with_session_nonce():
    from inference.predict import recommend_from_match
    from pipeline.parser import load_match

    m = load_match(ROOT / "data" / "raw_matches.json")
    ids = list(m["players"].keys())
    a, b = ids[0], ids[1]
    r1 = recommend_from_match(
        m, a, b, include_nlg=False, include_coach_voice=True, nlg_seed=1, session_nonce="aaa"
    )
    r2 = recommend_from_match(
        m, a, b, include_nlg=False, include_coach_voice=True, nlg_seed=1, session_nonce="bbb"
    )
    assert r1["coach_voice"]["coach_letter"] != r2["coach_voice"]["coach_letter"]
