import torch
import torch.nn as nn


class StrategyModel(nn.Module):
    def __init__(self, input_dim: int, num_actions: int, dropout: float = 0.1):
        super().__init__()
        self.input_dim = input_dim
        self.num_actions = num_actions
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, num_actions),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
