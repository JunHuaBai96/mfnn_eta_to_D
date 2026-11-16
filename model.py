# -*- coding: utf-8 -*-
"""
model.py
Residual multifidelity NN inspired by Lu et al., PNAS 2020, adapted to eta->D.
y_H ≈ alpha_1 * (A * [x, y_L] + b) + alpha_2 * F_nl(x, y_L)
"""

from __future__ import annotations
from typing import Optional, Tuple
import torch
import torch.nn as nn


class MLP(nn.Module):
    def __init__(self, in_dim: int, out_dim: int = 1, width: int = 64, depth: int = 3):
        super().__init__()
        layers = []
        d = in_dim
        for _ in range(depth):
            layers += [nn.Linear(d, width), nn.Tanh()]
            d = width
        layers.append(nn.Linear(d, out_dim))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


class SingleFidelityNN(nn.Module):
    def __init__(self, in_dim: int = 16, width: int = 64, depth: int = 3):
        super().__init__()
        self.net = MLP(in_dim, 1, width, depth)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class ResidualMFNN(nn.Module):
    """Lu-style composite multifidelity: linear + nonlinear residual on LF prediction."""

    def __init__(self, in_dim: int = 16, width: int = 64, depth_l: int = 3, depth_h: int = 3):
        super().__init__()
        self.lf_net = MLP(in_dim, 1, width, depth_l)
        # linear map on [x, y_L]
        self.lin = nn.Linear(in_dim + 1, 1, bias=True)
        self.nl_net = MLP(in_dim + 1, 1, width, depth_h)
        # learnable mixing (Lu et al. alpha weights)
        self.alpha_1 = nn.Parameter(torch.tensor(0.5))
        self.alpha_2 = nn.Parameter(torch.tensor(0.5))

    def forward_lf(self, x: torch.Tensor) -> torch.Tensor:
        return self.lf_net(x)

    def forward_hf(self, x: torch.Tensor, y_l: Optional[torch.Tensor] = None) -> torch.Tensor:
        if y_l is None:
            y_l = self.forward_lf(x)
        z = torch.cat([x, y_l.unsqueeze(-1)], dim=-1)
        y_lin = self.lin(z).squeeze(-1)
        y_nl = self.nl_net(z)
        return self.alpha_1 * y_lin + self.alpha_2 * y_nl

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.forward_hf(x)
