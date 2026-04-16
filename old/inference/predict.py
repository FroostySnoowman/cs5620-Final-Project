import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analytics.history_signals import build_match_narrative_context
from analytics.opponent_tactics import (
    build_profile,
    build_tactical_brief,
    rally_length_advice_supported,
)
from nlp.coach_voice import render_coach_voice
from nlp.feedback_nlg import render_personalized_feedback
from nlp.integration_payload import build_integration_payload
from models.supervised_model import StrategyModel
from pipeline.constants import NUM_TACTICS, TACTIC_NAMES
from pipeline.dataset import build_focal_samples
from pipeline.parser import load_match
from pipeline.shot_stats import history_shot_support


def _load_config(root: Path) -> Dict[str, Any]:
    cfg_path = root / "model_config.json"
    if not cfg_path.is_file():
        raise FileNotFoundError(
            f"Missing {cfg_path}; run training.train_supervised first."
        )
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def load_strategy_model(root: Optional[Path] = None) -> Tuple[StrategyModel, Dict[str, Any]]:
    base = root or ROOT
    cfg = _load_config(base)
    weights = base / cfg.get("weights_path", "strategy_model.pt")
    if not weights.is_file():
        raise FileNotFoundError(f"Missing weights at {weights}")
    model = StrategyModel(
        input_dim=cfg["input_dim"],
        num_actions=cfg.get("num_classes", NUM_TACTICS),
    )
    state = torch.load(weights, map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()
    return model, cfg


def predict_vector(state: np.ndarray, model: Optional[StrategyModel] = None) -> Dict[str, Any]:
    if model is None:
        model, _ = load_strategy_model()
    x = torch.from_numpy(np.asarray(state, dtype=np.float32)).unsqueeze(0)
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1).squeeze(0).numpy()
        action = int(logits.argmax(1).item())
    return {
        "action": action,
        "tactic": TACTIC_NAMES[action],
        "probs": {TACTIC_NAMES[i]: float(probs[i]) for i in range(len(probs))},
    }


def recommend_from_match(
    match: dict,
    focal_id: str,
    opponent_id: str,
    model: Optional[StrategyModel] = None,
    *,
    include_nlg: bool = True,
    include_coach_voice: bool = True,
    nlg_seed: Optional[int] = None,
    display_name_focal: Optional[str] = None,
    display_name_opponent: Optional[str] = None,
    session_nonce: Optional[str] = None,
    local_coach_lm: bool = False,
) -> Dict[str, Any]:
    """
    Aggregate tactical brief + model vote on the last point's state
    (after full match rolling stats — use for post-match review).

    When ``include_nlg`` is True, adds ``personalized_feedback`` (varied prose) and
    ``integration_payload`` (facts JSON + optional LLM prompt shell for your stack).

    When ``include_coach_voice`` is True, adds ``coach_voice`` (warm second-person letter,
    no ML jargon in the letter text).

    ``session_nonce`` (e.g. UUID from your app) varies coach wording without LLMs.

    ``match_narrative_context`` (in the output dict) summarizes point-sequence signals
    for scenario-conditioned coach copy. ``local_coach_lm`` enables optional on-device
    synonym shims (no API).
    """
    if model is None:
        model, _ = load_strategy_model()

    X, _ = build_focal_samples(match, focal_id, opponent_id)
    last_state = X[-1]
    pred = predict_vector(last_state, model=model)

    self_p = build_profile(match, focal_id)
    opp_p = build_profile(match, opponent_id)
    rally_adv = rally_length_advice_supported(match)
    brief = build_tactical_brief(
        self_p,
        opp_p,
        self_name=focal_id,
        opp_name=opponent_id,
        include_rally_length_advice=rally_adv,
    )

    narrative_ctx = build_match_narrative_context(match, focal_id, opponent_id)

    out: Dict[str, Any] = {
        "focal_player": focal_id,
        "opponent": opponent_id,
        "rally_length_advice_supported": rally_adv,
        "shot_history_support": history_shot_support(match),
        "model_prediction": pred,
        "tactical_brief": brief,
        "match_narrative_context": narrative_ctx,
    }

    if include_nlg:
        nlg = render_personalized_feedback(
            out,
            you_label=display_name_focal,
            opp_label=display_name_opponent,
            seed=nlg_seed,
        )
        out["personalized_feedback"] = nlg

    if include_coach_voice:
        out["coach_voice"] = render_coach_voice(
            out,
            you_label=display_name_focal,
            opp_label=display_name_opponent,
            seed=nlg_seed,
            session_nonce=session_nonce,
            local_coach_lm=local_coach_lm,
        )

    if include_nlg:
        out["integration_payload"] = build_integration_payload(
            out, personalized_feedback=out["personalized_feedback"]
        )

    return out


def main():
    ap = argparse.ArgumentParser(
        description="Tennis tactics: stats + ML + template NLG + coach voice (no LLM required)"
    )
    ap.add_argument("--data", type=str, default=str(ROOT / "data" / "raw_matches.json"))
    ap.add_argument("--focal", type=str, default="", help="Focal player name (must match JSON)")
    ap.add_argument("--opponent", type=str, default="", help="Opponent name")
    ap.add_argument("--no-nlg", action="store_true", help="Omit personalized_feedback / integration_payload")
    ap.add_argument("--no-coach", action="store_true", help="Omit coach_voice (warm closing letter)")
    ap.add_argument("--nlg-seed", type=int, default=None, help="Seed for wording variation (NLG + coach)")
    ap.add_argument("--session-nonce", type=str, default=None, help="Client id for varied coach copy (no LLM)")
    ap.add_argument(
        "--local-coach-lm",
        action="store_true",
        help="Optional on-device synonym shims for coach text (no API)",
    )
    args = ap.parse_args()

    match = load_match(args.data)
    players = list((match.get("players") or {}).keys())
    if len(players) < 2:
        print("Need at least two players in match JSON")
        sys.exit(1)
    focal = args.focal or players[0]
    opp = args.opponent or (players[1] if players[0] == focal else players[0])
    if opp == focal:
        opp = players[1] if players[0] == focal else players[0]

    out = recommend_from_match(
        match,
        focal,
        opp,
        include_nlg=not args.no_nlg,
        include_coach_voice=not args.no_coach,
        nlg_seed=args.nlg_seed,
        session_nonce=args.session_nonce,
        local_coach_lm=args.local_coach_lm,
    )
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
