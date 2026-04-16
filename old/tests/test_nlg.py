from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_nlg_deterministic_with_seed():
    from inference.predict import recommend_from_match
    from pipeline.parser import load_match

    m = load_match(ROOT / "data" / "raw_matches.json")
    ids = list(m["players"].keys())
    a, b = ids[0], ids[1]
    r1 = recommend_from_match(m, a, b, include_nlg=True, nlg_seed=42)
    r2 = recommend_from_match(m, a, b, include_nlg=True, nlg_seed=42)
    assert r1["personalized_feedback"]["full_text"] == r2["personalized_feedback"]["full_text"]


def test_integration_payload_has_facts_and_structured_json():
    from inference.predict import recommend_from_match
    from pipeline.parser import load_match

    m = load_match(ROOT / "data" / "raw_matches.json")
    ids = list(m["players"].keys())
    a, b = ids[0], ids[1]
    r = recommend_from_match(m, a, b, nlg_seed=0)
    ip = r["integration_payload"]
    assert "facts" in ip
    assert "structured_facts_json" in ip
    assert r["focal_player"] in ip["structured_facts_json"]
