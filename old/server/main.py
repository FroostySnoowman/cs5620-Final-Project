"""
Optional FastAPI wrapper for integration tests and external proxies.

Does not replace your own api/ folder—run locally or behind your gateway.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI
from pydantic import BaseModel, Field

from inference.predict import recommend_from_match
from pipeline.parser import load_match

app = FastAPI(title="BreakPoint AI", version="1.0.0")


class AnalyzeRequest(BaseModel):
    match: Dict[str, Any] = Field(..., description="Full match JSON (same schema as raw_matches.json)")
    focal_id: str
    opponent_id: str
    include_nlg: bool = True
    include_coach_voice: bool = True
    nlg_seed: Optional[int] = None
    session_nonce: Optional[str] = None
    local_coach_lm: bool = False


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze")
def analyze(req: AnalyzeRequest) -> dict:
    return recommend_from_match(
        req.match,
        req.focal_id,
        req.opponent_id,
        include_nlg=req.include_nlg,
        include_coach_voice=req.include_coach_voice,
        nlg_seed=req.nlg_seed,
        session_nonce=req.session_nonce,
        local_coach_lm=req.local_coach_lm,
    )


@app.post("/analyze_file")
def analyze_file(
    path: str,
    focal_id: str,
    opponent_id: str,
    include_nlg: bool = True,
    include_coach_voice: bool = True,
    nlg_seed: Optional[int] = None,
    session_nonce: Optional[str] = None,
    local_coach_lm: bool = False,
) -> dict:
    """Load JSON from disk on the server (dev only)."""
    match = load_match(path)
    return recommend_from_match(
        match,
        focal_id,
        opponent_id,
        include_nlg=include_nlg,
        include_coach_voice=include_coach_voice,
        nlg_seed=nlg_seed,
        session_nonce=session_nonce,
        local_coach_lm=local_coach_lm,
    )
