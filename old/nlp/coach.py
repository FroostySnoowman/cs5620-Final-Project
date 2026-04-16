"""
CLI: print the coach-style closing letter (or full coach_voice JSON).

Usage:
  python -m nlp.coach --data data/raw_matches.json --focal "A" --opponent "B"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from inference.predict import recommend_from_match
from pipeline.parser import load_match


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Coach-style closing summary (warm second-person letter, no ML jargon in the letter)."
    )
    ap.add_argument("--data", type=str, default=str(ROOT / "data" / "raw_matches.json"))
    ap.add_argument("--focal", type=str, default="", help="Focal player (must match JSON)")
    ap.add_argument("--opponent", type=str, default="", help="Opponent name")
    ap.add_argument("--seed", type=int, default=None, help="Seed for wording variation")
    ap.add_argument("--session-nonce", type=str, default=None, help="Client id for varied coach copy")
    ap.add_argument("--json", action="store_true", help="Print full coach_voice object as JSON")
    ap.add_argument(
        "--with-nlg",
        action="store_true",
        help="Also compute personalized_feedback / integration_payload (slower, larger)",
    )
    ap.add_argument(
        "--local-coach-lm",
        action="store_true",
        help="Optional on-device synonym shims for coach text (no API)",
    )
    args = ap.parse_args()

    match = load_match(args.data)
    players = list((match.get("players") or {}).keys())
    if len(players) < 2:
        print("Need at least two players in match JSON", file=sys.stderr)
        sys.exit(1)
    focal = args.focal or players[0]
    opp = args.opponent or (players[1] if players[0] == focal else players[0])
    if opp == focal:
        opp = players[1] if players[0] == focal else players[0]

    out = recommend_from_match(
        match,
        focal,
        opp,
        include_nlg=args.with_nlg,
        include_coach_voice=True,
        nlg_seed=args.seed,
        session_nonce=args.session_nonce,
        local_coach_lm=args.local_coach_lm,
    )
    cv = out.get("coach_voice") or {}
    if args.json:
        print(json.dumps(cv, indent=2, default=str))
    else:
        print(cv.get("coach_letter", ""))


if __name__ == "__main__":
    main()
