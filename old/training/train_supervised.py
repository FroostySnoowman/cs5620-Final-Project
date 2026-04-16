import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.supervised_model import StrategyModel
from pipeline.constants import NUM_TACTICS
from pipeline.dataset import build_match_tensors
from pipeline.parser import load_match


def confusion_matrix(pred: np.ndarray, true: np.ndarray, n: int) -> np.ndarray:
    cm = np.zeros((n, n), dtype=np.int64)
    for p, t in zip(pred, true):
        cm[t, p] += 1
    return cm


def class_weights(y: torch.Tensor, num_classes: int) -> torch.Tensor:
    """Balanced weights: n / (K * count_c) so rare classes get higher loss."""
    counts = torch.bincount(y, minlength=num_classes).float()
    n = float(y.numel())
    w = n / (num_classes * counts.clamp(min=1.0))
    return w


def train(
    X_train: torch.Tensor,
    y_train: torch.Tensor,
    X_val: torch.Tensor,
    y_val: torch.Tensor,
    input_dim: int,
    epochs: int = 80,
    lr: float = 1e-3,
    weight_decay: float = 1e-4,
    seed: int = 42,
) -> StrategyModel:
    torch.manual_seed(seed)
    model = StrategyModel(input_dim=input_dim, num_actions=NUM_TACTICS)
    opt = optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    ce = nn.CrossEntropyLoss(weight=class_weights(y_train, NUM_TACTICS))

    for epoch in range(epochs):
        model.train()
        opt.zero_grad()
        logits = model(X_train)
        loss = ce(logits, y_train)
        loss.backward()
        opt.step()

        if (epoch + 1) % 10 == 0 or epoch == 0:
            model.eval()
            with torch.no_grad():
                tr_logits = model(X_train)
                va_logits = model(X_val)
                tr_acc = (tr_logits.argmax(1) == y_train).float().mean().item()
                va_acc = (va_logits.argmax(1) == y_val).float().mean().item()
            print(f"Epoch {epoch + 1}/{epochs}  loss={loss.item():.4f}  "
                  f"train_acc={tr_acc:.3f}  val_acc={va_acc:.3f}")

    return model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=str, default=str(ROOT / "data" / "raw_matches.json"))
    ap.add_argument("--out", type=str, default=str(ROOT / "strategy_model.pt"))
    ap.add_argument("--config-out", type=str, default=str(ROOT / "model_config.json"))
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--val-ratio", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    match = load_match(args.data)
    X_train, y_train, X_val, y_val, meta = build_match_tensors(match, val_ratio=args.val_ratio)
    print("Dataset:", json.dumps({k: v for k, v in meta.items() if k != "players"}, indent=2))

    model = train(
        X_train,
        y_train,
        X_val,
        y_val,
        input_dim=meta["input_dim"],
        epochs=args.epochs,
        seed=args.seed,
    )

    model.eval()
    with torch.no_grad():
        pred = model(X_val).argmax(1).numpy()
        true = y_val.numpy()
    cm = confusion_matrix(pred, true, NUM_TACTICS)
    print("Confusion matrix (rows=true, cols=pred):")
    print(cm)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out_path)

    cfg = {
        "version": 2,
        "input_dim": meta["input_dim"],
        "num_classes": NUM_TACTICS,
        "contrast_len": meta["contrast_len"],
        "weights_path": str(out_path.name),
    }
    Path(args.config_out).write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"Saved weights to {out_path}")
    print(f"Saved config to {args.config_out}")


if __name__ == "__main__":
    main()
