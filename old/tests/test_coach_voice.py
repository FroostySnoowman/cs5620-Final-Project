from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_coach_voice_deterministic_and_clean():
    from inference.predict import recommend_from_match
    from nlp.coach_voice import coach_letter_banned_terms_present
    from pipeline.parser import load_match

    m = load_match(ROOT / "data" / "raw_matches.json")
    ids = list(m["players"].keys())
    a, b = ids[0], ids[1]
    r1 = recommend_from_match(m, a, b, include_nlg=False, include_coach_voice=True, nlg_seed=7)
    r2 = recommend_from_match(m, a, b, include_nlg=False, include_coach_voice=True, nlg_seed=7)
    cv1 = r1["coach_voice"]
    cv2 = r2["coach_voice"]
    assert cv1["coach_letter"] == cv2["coach_letter"]
    assert len(cv1["coach_letter"]) > 100
    assert cv1["the_one_thing"]
    banned = coach_letter_banned_terms_present(cv1["coach_letter"])
    assert not banned, f"banned terms in letter: {banned}"


def test_coach_voice_varies_without_seed():
    from inference.predict import recommend_from_match
    from pipeline.parser import load_match

    m = load_match(ROOT / "data" / "raw_matches.json")
    ids = list(m["players"].keys())
    a, b = ids[0], ids[1]
    r1 = recommend_from_match(
        m, a, b, include_nlg=False, include_coach_voice=True, nlg_seed=None
    )
    r2 = recommend_from_match(
        m, a, b, include_nlg=False, include_coach_voice=True, nlg_seed=None
    )
    assert r1["coach_voice"]["coach_letter"] != r2["coach_voice"]["coach_letter"]
    assert r1["coach_voice"].get("run_entropy")
    assert r1["coach_voice"]["run_entropy"] != r2["coach_voice"]["run_entropy"]


def test_local_coach_lm_flag_runs():
    from inference.predict import recommend_from_match
    from nlp.coach_voice import coach_letter_banned_terms_present
    from pipeline.parser import load_match

    m = load_match(ROOT / "data" / "raw_matches.json")
    ids = list(m["players"].keys())
    a, b = ids[0], ids[1]
    r = recommend_from_match(
        m,
        a,
        b,
        include_nlg=False,
        include_coach_voice=True,
        nlg_seed=11,
        local_coach_lm=True,
    )
    cv = r["coach_voice"]
    assert cv.get("local_coach_lm") is True
    assert not coach_letter_banned_terms_present(cv["coach_letter"])


def test_coach_cli_module_runs():
    import subprocess
    import sys

    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "nlp.coach",
            "--data",
            str(ROOT / "data" / "raw_matches.json"),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0
    assert "Hey " in r.stdout or "Good work" in r.stdout or len(r.stdout) > 50
