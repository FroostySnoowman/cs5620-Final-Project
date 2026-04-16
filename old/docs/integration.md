# Integration guide (Statistics AI)

Your `app/` and `api/` codebases are not modified by this project. Use this contract to call the Python engine from your stack (subprocess, HTTP proxy to the optional server below, or shared package).

## End-to-end flow

1. Train (or ship prebuilt `strategy_model.pt` + `model_config.json`).
2. Load match JSON (same schema as `data/raw_matches.json`).
3. Call `inference.predict.recommend_from_match(match, focal_id, opponent_id, ...)`.

## Key response fields

| Field | Purpose |
|-------|---------|
| `tactical_brief` | Structured recommendations + uncertainty |
| `model_prediction` | 4-class tactic + softmax-style `probs` |
| `personalized_feedback` | Analytical NLG (if `include_nlg=True`) |
| `coach_voice` | Warm second-person letter; template-only, no LLMs |
| `integration_payload` | `facts` + `structured_facts_json` for your DB/API |
| `shot_history_support` | Whether terminal actions in history are labeled enough for shot-level history stats |
| `rally_length_advice_supported` | False if every point was 1–2 shots (rally tactics omitted) |

## Variation without LLMs

- `nlg_seed`: integer for reproducible wording.
- `session_nonce`: string (e.g. UUID per app session) so coach copy changes between visits when combined with seed.

## Retraining

After feature changes, `input_dim` in `model_config.json` must match the built tensors. Run:

```bash
python3 -m training.train_supervised --data data/raw_matches.json
```

## Optional HTTP server

See `server/main.py` in this repo (`GET /health`, `POST /analyze`). Run:

```bash
uvicorn server.main:app --reload --port 8765
```

OpenAPI: `openapi.yaml` at repo root.
