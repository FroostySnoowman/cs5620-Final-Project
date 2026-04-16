import copy
import random
from typing import List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim


class DQN(nn.Module):
    def __init__(self, state_dim: int, action_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, action_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class ReplayBuffer:
    def __init__(self, capacity: int = 100_000):
        self.capacity = capacity
        self._data: List[Tuple] = []
        self._pos = 0

    def push(self, transition: Tuple) -> None:
        if len(self._data) < self.capacity:
            self._data.append(transition)
        else:
            self._data[self._pos % self.capacity] = transition
            self._pos += 1

    def extend(self, transitions: List[Tuple]) -> None:
        for t in transitions:
            self.push(t)

    def sample(self, batch_size: int) -> List[Tuple]:
        k = min(batch_size, len(self._data))
        return random.sample(self._data, k)

    def __len__(self) -> int:
        return len(self._data)


class DQNAgent:
    """Offline DQN with replay buffer and periodic target sync."""

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        lr: float = 1e-3,
        gamma: float = 0.99,
        target_sync_every: int = 200,
    ):
        self.policy = DQN(state_dim, action_dim)
        self.target = DQN(state_dim, action_dim)
        self.target.load_state_dict(copy.deepcopy(self.policy.state_dict()))
        self.optimizer = optim.Adam(self.policy.parameters(), lr=lr)
        self.gamma = gamma
        self.target_sync_every = target_sync_every
        self.buffer = ReplayBuffer()
        self.batch_size = 64
        self.train_steps = 0

    def train_step(self) -> Optional[float]:
        if len(self.buffer) < self.batch_size:
            return None
        batch = self.buffer.sample(self.batch_size)
        s = torch.stack([torch.tensor(b[0], dtype=torch.float32) for b in batch])
        a = torch.tensor([b[1] for b in batch], dtype=torch.long)
        r = torch.tensor([b[2] for b in batch], dtype=torch.float32)
        ns = torch.stack([torch.tensor(b[3], dtype=torch.float32) for b in batch])
        d = torch.tensor([b[4] for b in batch], dtype=torch.float32)

        q = self.policy(s).gather(1, a.unsqueeze(1)).squeeze(1)
        with torch.no_grad():
            next_q = self.target(ns).max(1)[0]
            target = r + self.gamma * next_q * (1.0 - d)

        loss = nn.functional.mse_loss(q, target)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        self.train_steps += 1
        if self.train_steps % self.target_sync_every == 0:
            self.target.load_state_dict(copy.deepcopy(self.policy.state_dict()))
        return float(loss.item())
