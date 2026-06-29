"""3D U-Net model implemented with PyTorch.

The network follows the classic U-Net pattern shown in M.png:
encoder blocks, max-pooling, decoder up-convolutions, skip concatenation,
and a final 1x1x1 convolution that produces segmentation logits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import torch
from torch import Tensor, nn
import torch.nn.functional as F


def _make_norm(norm: str, channels: int) -> nn.Module:
    if norm == "batch":
        return nn.BatchNorm3d(channels)
    if norm == "instance":
        return nn.InstanceNorm3d(channels, affine=True)
    if norm in {"none", ""}:
        return nn.Identity()
    raise ValueError(f"Unsupported norm: {norm!r}")


class ConvBlock3d(nn.Module):
    """Two 3x3x3 convolutions with normalization and ReLU."""

    def __init__(self, in_channels: int, out_channels: int, norm: str = "instance") -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv3d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            _make_norm(norm, out_channels),
            nn.ReLU(inplace=True),
            nn.Conv3d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            _make_norm(norm, out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: Tensor) -> Tensor:
        return self.block(x)


@dataclass(frozen=True)
class UNet3DConfig:
    in_channels: int = 1
    out_channels: int = 1
    base_channels: int = 32
    depth: int = 4
    norm: str = "instance"


class UNet3D(nn.Module):
    """3D U-Net for volumetric segmentation.

    Input shape: ``(batch, channels, depth, height, width)``.
    Output shape: ``(batch, out_channels, depth, height, width)``.
    """

    def __init__(
        self,
        in_channels: int = 1,
        out_channels: int = 1,
        base_channels: int = 32,
        depth: int = 4,
        norm: str = "instance",
    ) -> None:
        super().__init__()
        if depth < 1:
            raise ValueError("depth must be at least 1")
        if base_channels < 1:
            raise ValueError("base_channels must be at least 1")

        self.config = UNet3DConfig(
            in_channels=in_channels,
            out_channels=out_channels,
            base_channels=base_channels,
            depth=depth,
            norm=norm,
        )

        channels = [base_channels * (2**level) for level in range(depth + 1)]

        encoders: list[nn.Module] = []
        prev_channels = in_channels
        for out_ch in channels[:-1]:
            encoders.append(ConvBlock3d(prev_channels, out_ch, norm=norm))
            prev_channels = out_ch
        self.encoders = nn.ModuleList(encoders)

        self.pool = nn.MaxPool3d(kernel_size=2, stride=2)
        self.bottleneck = ConvBlock3d(channels[-2], channels[-1], norm=norm)

        upconvs: list[nn.Module] = []
        decoders: list[nn.Module] = []
        for level in reversed(range(depth)):
            in_ch = channels[level + 1]
            skip_ch = channels[level]
            upconvs.append(nn.ConvTranspose3d(in_ch, skip_ch, kernel_size=2, stride=2))
            decoders.append(ConvBlock3d(skip_ch * 2, skip_ch, norm=norm))
        self.upconvs = nn.ModuleList(upconvs)
        self.decoders = nn.ModuleList(decoders)

        self.head = nn.Conv3d(base_channels, out_channels, kernel_size=1)

    @classmethod
    def from_config(cls, config: UNet3DConfig) -> "UNet3D":
        return cls(
            in_channels=config.in_channels,
            out_channels=config.out_channels,
            base_channels=config.base_channels,
            depth=config.depth,
            norm=config.norm,
        )

    @property
    def downsample_factor(self) -> int:
        return 2 ** self.config.depth

    def forward(self, x: Tensor) -> Tensor:
        original_spatial = x.shape[-3:]
        x, crop_slices = self._pad_to_factor(x, self.downsample_factor)

        skips: list[Tensor] = []
        for encoder in self.encoders:
            x = encoder(x)
            skips.append(x)
            x = self.pool(x)

        x = self.bottleneck(x)

        for upconv, decoder, skip in zip(self.upconvs, self.decoders, reversed(skips)):
            x = upconv(x)
            skip = self._match_spatial(skip, x.shape[-3:])
            x = torch.cat((skip, x), dim=1)
            x = decoder(x)

        x = self.head(x)
        x = x[crop_slices]
        if x.shape[-3:] != original_spatial:
            raise RuntimeError(
                f"UNet3D output shape {tuple(x.shape[-3:])} does not match input "
                f"shape {tuple(original_spatial)}"
            )
        return x

    @staticmethod
    def _pad_to_factor(x: Tensor, factor: int) -> tuple[Tensor, tuple[slice, ...]]:
        spatial = x.shape[-3:]
        pads: list[int] = []
        crop_slices: list[slice] = [slice(None), slice(None)]

        for size in reversed(spatial):
            total_pad = (factor - size % factor) % factor
            before = total_pad // 2
            after = total_pad - before
            pads.extend([before, after])

        for axis, size in enumerate(spatial):
            before = pads[(2 - axis) * 2]
            crop_slices.append(slice(before, before + size))

        if any(pads):
            x = F.pad(x, pads)
        return x, tuple(crop_slices)

    @staticmethod
    def _match_spatial(x: Tensor, target: Iterable[int]) -> Tensor:
        target_size = tuple(target)
        if x.shape[-3:] == target_size:
            return x
        return F.interpolate(x, size=target_size, mode="trilinear", align_corners=False)


def count_parameters(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)


def predict_binary_mask(logits: Tensor, threshold: float = 0.5) -> Tensor:
    """Convert one-channel logits into a binary mask."""

    if logits.shape[1] != 1:
        raise ValueError("predict_binary_mask expects logits with exactly one output channel")
    return (torch.sigmoid(logits) >= threshold).to(torch.uint8)

