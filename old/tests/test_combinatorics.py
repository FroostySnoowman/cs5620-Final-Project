def test_coach_combinatorics_million_plus():
    from nlp.coach_scenarios import estimate_coach_combinatorics

    e = estimate_coach_combinatorics()
    assert e["meets_million_plus_per_paragraph"]
    assert e["per_paragraph_with_tactic_pool_lower_bound"] >= 1_000_000
