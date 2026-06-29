"""Run a minimal 3D U-Net smoke test.

This script builds the model, sends a synthetic CT-like volume through it,
and prints the resulting tensor shapes and parameter count.
"""

from __future__ import annotations

import torch

from unet3d import UNet3D, count_parameters, predict_binary_mask


def main() -> None:
    torch.manual_seed(42)

    model = UNet3D(
        in_channels=1,
        out_channels=1,
        base_channels=16,
        depth=4,
        norm="instance",
    )
    model.eval()

    volume = torch.randn(1, 1, 33, 96, 128)
    with torch.no_grad():
        logits = model(volume)
        mask = predict_binary_mask(logits)

    print("UNet3D smoke test")
    print(f"input shape:  {tuple(volume.shape)}")
    print(f"logits shape: {tuple(logits.shape)}")
    print(f"mask shape:   {tuple(mask.shape)}")
    print(f"parameters:   {count_parameters(model):,}")
    print(f"mask values:  {sorted(mask.unique().tolist())}")


if __name__ == "__main__":
    main()

