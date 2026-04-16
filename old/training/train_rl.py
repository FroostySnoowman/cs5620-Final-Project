"""
Offline DQN from chronological match data: state = pre-point features,
action = tactic label, reward = +1/-1 point outcome for focal player.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.rl_agent import DQNAgent
from pipeline.dataset import build_focal_samples
from pipeline.parser import extract_points, load_match, match_player_ids


def collect_offline_transitions(match: dict) -> List[Tuple]:
    ids = match_player_ids(match)
    if len(ids) < 2:
        raise ValueError("Need two players")
    p0, p1 = ids[0], ids[1]
    out: List[Tuple] = []
    for focal, other in [(p0, p1), (p1, p0)]:
        X, y = build_focal_samples(match, focal, other)
        points = extract_points(match)
        for i in range(len(points)):
            r = 1.0 if points[i]["winner"] == focal else -1.0
            if i < len(points) - 1:
                ns = X[i + 1]
                done = 0.0
            else:
                ns = np.zeros_like(X[i])
                done = 1.0
            out.append((X[i], int(y[i]), r, ns, done))
    return out


def train_offline(
    agent: DQNAgent,
    transitions: List[Tuple],
    gradient_steps: int = 5000,
    log_every: int = 500,
) -> None:
    agent.buffer.extend(transitions)
    for step in range(gradient_steps):
        loss = agent.train_step()
        if loss is not None and (step + 1) % log_every == 0:
            print(f"step {step + 1}/{gradient_steps}  loss={loss:.4f}  buffer={len(agent.buffer)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=str, default=str(ROOT / "data" / "raw_matches.json"))
    ap.add_argument("--out", type=str, default=str(ROOT / "rl_agent.pt"))
    ap.add_argument("--steps", type=int, default=5000)
    ap.add_argument("--config", type=str, default=str(ROOT / "model_config.json"))
    args = ap.parse_args()

    match = load_match(args.data)
    transitions = collect_offline_transitions(match)
    dim = int(np.asarray(transitions[0][0]).shape[0])
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if cfg.get("input_dim") != dim:
        raise ValueError(f"RL state dim {dim} != model_config input_dim {cfg.get('input_dim')}")

    agent = DQNAgent(state_dim=dim, action_dim=cfg.get("num_classes", 4))
    train_offline(agent, transitions, gradient_steps=args.steps)

    torch.save(agent.policy.state_dict(), args.out)
    print(f"Saved RL policy to {args.out}")


if __name__ == "__main__":
    main()
