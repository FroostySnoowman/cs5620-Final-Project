from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_normalize_actions():
    from pipeline.parser import extract_points, load_match

    m = load_match(ROOT / "data" / "raw_matches.json")
    pts = extract_points(m)
    assert len(pts) > 0
    p0 = pts[0]
    assert "terminal_type" in p0
    assert isinstance(p0["actions_detail"], list)


def test_rolling_rates_monotone():
    from pipeline.features import init_rolling_stats, rolling_rates, update_rolling_stats

    s = init_rolling_stats("A", net_prior=0.5)
    p = {
        "server": "A",
        "winner": "A",
        "rally_length": 3,
        "net": {},
    }
    update_rolling_stats(s, p)
    r = rolling_rates(s)
    assert r["serve_win_rate"] == 1.0
    assert s["serve_played"] == 1


def test_contrast_length():
    from analytics.opponent_tactics import CONTRAST_LEN, build_profile, contrast_vector
    from pipeline.parser import load_match

    m = load_match(ROOT / "data" / "raw_matches.json")
    ids = list(m["players"].keys())
    a, b = ids[0], ids[1]
    pa = build_profile(m, a)
    pb = build_profile(m, b)
    c = contrast_vector(pa, pb)
    assert c.shape[0] == CONTRAST_LEN


def test_rally_length_advice_only_when_longer_rallies_exist():
    from analytics.opponent_tactics import (
        RALLY_NEUTRAL_VALUE,
        contrast_vector,
        rally_length_advice_supported,
    )
    from pipeline.parser import extract_points

    minimal_players = {
        "A": {"serve": {}, "return": {}, "rally": {}, "individualMatch": {"pointsPlayed": 2, "pointsWon": 1}},
        "B": {"serve": {}, "return": {}, "rally": {}, "individualMatch": {"pointsPlayed": 2, "pointsWon": 1}},
    }
    base_pt = {
        "pointLoserId": "B",
        "actions": [{"type": "ACE", "actorId": "A"}],
        "netChoices": {},
    }
    short_only = {
        "players": minimal_players,
        "history": [
            {**base_pt, "pointWinnerId": "A", "serverId": "A", "receiverId": "B", "rallyLength": 1},
            {**base_pt, "pointWinnerId": "B", "serverId": "B", "receiverId": "A", "rallyLength": 2},
        ],
    }
    with_long = {
        "players": minimal_players,
        "history": short_only["history"]
        + [
            {
                **base_pt,
                "pointWinnerId": "A",
                "serverId": "A",
                "receiverId": "B",
                "rallyLength": 9,
            },
        ],
    }
    assert rally_length_advice_supported(short_only) is False
    assert rally_length_advice_supported(with_long) is True
    assert max(p["rally_length"] for p in extract_points(short_only)) <= 2

    from analytics.opponent_tactics import build_profile

    pa = build_profile(short_only, "A")
    pb = build_profile(short_only, "B")
    cn = contrast_vector(pa, pb, neutralize_rally_lengths=True)
    assert (cn[2:6] == RALLY_NEUTRAL_VALUE).all()


def test_label_deterministic():
    from pipeline.labels import infer_tactic_label

    pt = {
        "rally_length": 10,
        "winner": "A",
        "server": "B",
        "terminal_type": "WINNER",
        "terminal_actor": "A",
        "net": {},
        "actions_detail": [],
    }
    assert infer_tactic_label(pt, "A") == 3  # extend_rally
