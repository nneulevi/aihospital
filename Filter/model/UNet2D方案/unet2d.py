"""2D U-Net model compatible with CT axial-slice segmentation."""

from __future__ import annotations

import torch
from torch import Tensor, nn
import torch.nn.functional as F


class DoubleConv2D(nn.Module):
    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: Tensor) -> Tensor:
        return self.conv(x)


class Down2D(nn.Module):
    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.block = nn.Sequential(nn.MaxPool2d(2), DoubleConv2D(in_channels, out_channels))

    def forward(self, x: Tensor) -> Tensor:
        return self.block(x)


class Up2D(nn.Module):
    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.up = nn.ConvTranspose2d(in_channels, in_channels // 2, kernel_size=2, stride=2)
        self.conv = DoubleConv2D(in_channels, out_channels)

    def forward(self, x: Tensor, skip: Tensor) -> Tensor:
        x = self.up(x)
        diff_y = skip.size(2) - x.size(2)
        diff_x = skip.size(3) - x.size(3)
        x = F.pad(x, [diff_x // 2, diff_x - diff_x // 2, diff_y // 2, diff_y - diff_y // 2])
        return self.conv(torch.cat([skip, x], dim=1))


class UNet2D(nn.Module):
    def __init__(self, in_channels: int = 1, out_channels: int = 1, base_channels: int = 64) -> None:
        super().__init__()
        self.fused_feature: Tensor | None = None
        c1 = base_channels
        c2 = base_channels * 2
        c3 = base_channels * 4
        c4 = base_channels * 8
        self.d1 = DoubleConv2D(in_channels, c1)
        self.d2 = Down2D(c1, c2)
        self.d3 = Down2D(c2, c3)
        self.d4 = Down2D(c3, c4)
        self.up4 = Up2D(c4, c3)
        self.up3 = Up2D(c3, c2)
        self.up2 = Up2D(c2, c1)
        self.out = nn.Conv2d(c1, out_channels, kernel_size=1)

    def forward(self, x: Tensor, cache_features: bool = False) -> Tensor:
        x1 = self.d1(x)
        x2 = self.d2(x1)
        x3 = self.d3(x2)
        x4 = self.d4(x3)
        if cache_features:
            self.fused_feature = self._fuse_features(x1, x2, x3, x4)
        x = self.up4(x4, x3)
        x = self.up3(x, x2)
        x = self.up2(x, x1)
        return self.out(x)

    @staticmethod
    def _fuse_features(*features: Tensor) -> Tensor:
        pooled = [torch.mean(feature, dim=(2, 3)) for feature in features]
        return F.normalize(torch.cat(pooled, dim=1), p=2, dim=1)

    def extract_features(self) -> Tensor:
        if self.fused_feature is None:
            raise ValueError("Run model(x, cache_features=True) before extract_features().")
        return self.fused_feature


def count_parameters(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
