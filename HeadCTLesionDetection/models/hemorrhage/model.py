"""Lightweight 3D CNN for study/series-level hemorrhage classification."""

from __future__ import annotations

import torch
from torch import nn


class ConvBlock3D(nn.Module):
    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv3d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm3d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv3d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm3d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class Hemorrhage3DCNN(nn.Module):
    def __init__(self, in_channels: int = 1, base_channels: int = 16, dropout: float = 0.2) -> None:
        super().__init__()
        channels = [base_channels, base_channels * 2, base_channels * 4, base_channels * 8]
        self.features = nn.Sequential(
            ConvBlock3D(in_channels, channels[0]),
            nn.MaxPool3d(2),
            ConvBlock3D(channels[0], channels[1]),
            nn.MaxPool3d(2),
            ConvBlock3D(channels[1], channels[2]),
            nn.MaxPool3d(2),
            ConvBlock3D(channels[2], channels[3]),
        )
        self.head = nn.Sequential(
            nn.AdaptiveAvgPool3d(1),
            nn.Flatten(),
            nn.Dropout(dropout),
            nn.Linear(channels[3], 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.features(x))


def count_parameters(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
