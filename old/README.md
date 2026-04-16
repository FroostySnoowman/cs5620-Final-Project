# BreakPoint AI

Machine learning + offline RL from match JSON. Core tactics use **stats + templates** (no paid LLM APIs). **Coach voice** uses **match narrative context**, **multi-slot templates**, large phrase banks, and optional **on-device** synonym shims (`--local-coach-lm`). See [`docs/combinatorics.md`](docs/combinatorics.md) and [`docs/integration.md`](docs/integration.md).

---

## Use this order (typical workflow)

| Step | What you’re doing | Command |
|------|-------------------|---------|
| 1 | Install dependencies | [`Setup`](#setup) |
| 2 | Train the **supervised** tactic model (writes weights + config inference needs) | [`training.train_supervised`](#train-supervised-model) |
| 3 | *(Optional)* Train the **offline RL** policy (separate artifact; not required for `predict` / coach) | [`training.train_rl`](#train-offline-rl-dqn) |
| 4 | Run **full analysis** on a match: tactics, NLG, coach letter, integration JSON | [`inference.predict`](#inference-full-json-pipeline) |
| 5 | *(Optional)* Print **only the coach letter** (readable text; same core engine, lighter than full JSON) | [`nlp.coach`](#coach-letter-readable-only) |
| 6 | *(Optional)* Expose the same logic over **HTTP** for another app to call | [`server` + `POST /analyze`](#optional-http-server) |
| 7 | *(Optional)* Run **tests** after changes | [`pytest`](#tests) |

**First-time minimum:** Setup → **train_supervised** → **inference.predict** (or **nlp.coach** if you only want the letter).

**When to retrain supervised:** After you change feature dimensions (e.g. `CONTRAST_LEN` / pipeline) or want a new `strategy_model.pt` on new data.

---

## Setup

Creates a venv and installs Python dependencies from `requirements.txt`.

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip3 install -r requirements.txt
```

---

## Train supervised model

**Purpose:** Learn a tactic classifier over rolling states + contrast features. **Outputs:** `strategy_model.pt` and `model_config.json` in the project root (needed for inference).

| Flag | Meaning |
|------|--------|
| `--data` | Path to match JSON (default: `data/raw_matches.json`) |
| `--out` | Where to save weights (default: `strategy_model.pt`) |
| `--config-out` | Where to save `input_dim` and paths (default: `model_config.json`) |
| `--epochs` | Training epochs (default: 60) |
| `--val-ratio` | Validation split fraction (default: 0.15) |
| `--seed` | RNG seed (default: 42) |

```bash
python3 -m training.train_supervised --data data/raw_matches.json --epochs 60
```

---

## Train offline RL (DQN)

**Purpose:** Train an offline DQN on match transitions; saves `rl_agent.pt`. **Not required** for `inference.predict` or coach NLG—those use the supervised model. **Requires** `model_config.json` with matching `input_dim`.

| Flag | Meaning |
|------|--------|
| `--data` | Match JSON |
| `--out` | Policy weights (default: `rl_agent.pt`) |
| `--steps` | Gradient steps (default: 5000) |
| `--config` | `model_config.json` path (default: project root) |

```bash
python3 -m training.train_rl --data data/raw_matches.json --steps 5000
```

---

## Inference (full JSON pipeline)

**Purpose:** One-stop analysis: loads the match, runs the supervised model, builds tactical brief, **`match_narrative_context`**, optional analytical NLG, **`coach_voice`**, and **`integration_payload`** (unless disabled).

**Default behavior:** NLG + coach voice **on**. Prints a large JSON object to stdout.

| Flag | Meaning |
|------|--------|
| `--data` | Match JSON path |
| `--focal` | Focal player id (must match `players` keys); if omitted, first player in file |
| `--opponent` | Opponent id; if omitted, inferred |
| `--no-nlg` | Skip `personalized_feedback` and `integration_payload` |
| `--no-coach` | Skip `coach_voice` |
| `--nlg-seed` | Same integer → reproducible wording for NLG + coach |
| `--session-nonce` | Client/session string → varies coach wording without changing seed |
| `--local-coach-lm` | Optional on-device synonym shims on coach text (no API) |

```bash
python3 -m inference.predict --data data/raw_matches.json --focal "Rafael Nadal" --opponent "Roger Federer"
python3 -m inference.predict --data data/raw_matches.json --focal "Rafael Nadal" --opponent "Roger Federer" --nlg-seed 42
python3 -m inference.predict --data data/raw_matches.json --focal "Rafael Nadal" --opponent "Roger Federer" --no-nlg --no-coach
```

**Programmatic:** `recommend_from_match(match, focal_id, opponent_id, include_nlg=True, include_coach_voice=True, nlg_seed=..., session_nonce=..., local_coach_lm=False)`.

**Outputs you may care about:**

- **`personalized_feedback`**: analytical prose (headline, bullets, full text)
- **`coach_voice`**: `coach_letter`, `the_one_thing`, `sign_off`, `scenario_id`, etc.
- **`integration_payload`**: `facts`, `structured_facts_json` (schema v3 includes narrative summary + combinatorics meta)
- **`match_narrative_context`**: momentum, rally shape, rolling rates, clutch buckets (from point history + aggregates)

---

## Coach letter (readable only)

**Purpose:** Same core pipeline as inference, but prints **only the coach letter** (or full `coach_voice` JSON with `--json`). **Use when** you want human-readable text without dumping the full JSON.

| Flag | Meaning |
|------|--------|
| `--data` | Match JSON |
| `--focal` / `--opponent` | Same as inference |
| `--seed` | Passed through as `nlg_seed` → reproducible coach wording |
| `--session-nonce` | Vary coach copy between sessions |
| `--json` | Print entire `coach_voice` object (includes `run_entropy` when unseeded) |
| `--with-nlg` | Also compute analytical NLG + integration (slower, larger) |
| `--local-coach-lm` | Optional on-device shims |

```bash
python3 -m nlp.coach --data data/raw_matches.json --focal "Rafael Nadal" --opponent "Roger Federer"
python3 -m nlp.coach --data data/raw_matches.json --focal "Rafael Nadal" --opponent "Roger Federer" --seed 42
python3 -m nlp.coach --data data/raw_matches.json --focal "Rafael Nadal" --opponent "Roger Federer" --json
```

Unseeded runs use fresh entropy so wording varies run-to-run; use `--seed` for identical copy.

---

## Tests

**Purpose:** Verify pipeline, coach, narrative, and integration pieces.

```bash
python3 -m pytest tests/ -q
```

---

## Optional HTTP server

**Purpose:** Same `recommend_from_match` logic behind a REST API for integration tests or a local proxy.

```bash
uvicorn server.main:app --reload --port 8765
```

`POST /analyze` with JSON: `match`, `focal_id`, `opponent_id`, optional `include_nlg`, `include_coach_voice`, `nlg_seed`, `session_nonce`, `local_coach_lm`. See [`openapi.yaml`](openapi.yaml) and [`docs/integration.md`](docs/integration.md).

---

## Layout

```
data/raw_matches.json
pipeline/   parser, features, labels, dataset, shot_taxonomy, shot_stats, constants
analytics/  opponent profiles, contrast vector, tactical brief, history_signals
nlp/        feedback_nlg, coach_voice, coach_scenarios, elite_voice, local_coach_lm, coach (CLI), integration_payload
models/     supervised_model, rl_agent
training/   train_supervised, train_rl
inference/  predict
tests/      pytest
docs/       integration.md, combinatorics.md
server/     optional FastAPI
openapi.yaml
```

---

## What it does (conceptual)

- Parses point history and aggregates from `data/raw_matches.json`
- **Shot taxonomy** + stroke efficacy; **history** terminal-shot stats where labels exist
- **Rolling** features + **self vs opponent** contrast (state size = 6 rolling + `CONTRAST_LEN`; currently **25** floats)
- **Supervised** classifier: four tactics (`aggressive`, `neutral`, `approach_net`, `extend_rally`)
- **Offline DQN** (optional) on the same state space
- **Inference** merges model output, tactical brief, narrative context, optional NLG, coach voice, integration payload

---

## Notes

- **Single-match** files are fine for checks; **generalization** improves with many matches.
- Class imbalance uses **balanced loss weights**; rare tactics may still be hard on small data.
- Aggregates can be **low-N**; the tactical brief sets **uncertainty** when appropriate.
