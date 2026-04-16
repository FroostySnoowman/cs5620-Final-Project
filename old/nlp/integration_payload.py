"""
Structured payloads for downstream apps (no LLM required).

Facts stay in JSON for your web or mobile client to render.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .coach_scenarios import estimate_coach_combinatorics


def build_integration_payload(
    recommendation_result: Dict[str, Any],
    *,
    personalized_feedback: Dict[str, Any],
    source: str = "breakpoint_ai",
) -> Dict[str, Any]:
    """
    Single object you can POST to your API or store as a session record.

    Use ``structured_facts_json`` for any consumer that needs a portable string;
    this project does not require an external language model.
    """
    focal = recommendation_result.get("focal_player")
    opp = recommendation_result.get("opponent")
    brief = recommendation_result.get("tactical_brief") or {}
    pred = recommendation_result.get("model_prediction") or {}

    signals: List[Dict[str, Any]] = []
    for r in brief.get("recommendations") or []:
        signals.append(
            {
                "key": r.get("key"),
                "priority": r.get("priority"),
                "summary": r.get("text"),
                "metrics": {k: v for k, v in r.items() if k not in ("key", "priority", "text")},
            }
        )

    nctx = recommendation_result.get("match_narrative_context") or {}
    narrative_summary: Dict[str, Any] = {}
    if nctx:
        clutch = nctx.get("clutch") or {}
        narrative_summary = {
            "momentum": nctx.get("momentum"),
            "serve_pressure_bucket": nctx.get("serve_pressure_bucket"),
            "return_pressure_bucket": nctx.get("return_pressure_bucket"),
            "rally_shape": nctx.get("rally_shape"),
            "match_outcome_for_focal": nctx.get("match_outcome_for_focal"),
            "clutch_serve": clutch.get("serve_bucket"),
            "clutch_return": clutch.get("return_bucket"),
            "n_points": nctx.get("n_points"),
        }

    facts: Dict[str, Any] = {
        "source": source,
        "schema_version": 3,
        "players": {"focal": focal, "opponent": opp},
        "rally_length_advice_supported": recommendation_result.get("rally_length_advice_supported"),
        "shot_history_support": recommendation_result.get("shot_history_support"),
        "match_narrative_summary": narrative_summary or None,
        "coach_combinatorics": estimate_coach_combinatorics(),
        "signals": signals,
        "model": {
            "top_tactic": pred.get("tactic"),
            "action_id": pred.get("action"),
            "probabilities": pred.get("probs"),
        },
        "uncertainty": brief.get("uncertainty"),
    }

    coach = recommendation_result.get("coach_voice") or {}
    if coach:
        facts["coach"] = {
            "the_one_thing": coach.get("the_one_thing"),
            "sign_off": coach.get("sign_off"),
            "method": coach.get("method"),
            "scenario_id": coach.get("scenario_id"),
            "local_coach_lm": coach.get("local_coach_lm"),
        }

    facts_json = json.dumps(facts, indent=2, default=str)

    return {
        "facts": facts,
        "narrative": personalized_feedback.get("full_text"),
        "headline": personalized_feedback.get("headline"),
        "bullets": personalized_feedback.get("bullets"),
        "structured_facts_json": facts_json,
    }
