"""Run sliding-window inference with a trained 3D U-Net checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch

try:
  import SimpleITK as sitk
except ImportError as exc:  # pragma: no cover - dependency guard.
    raise SystemExit("SimpleITK is required. Install it with: pip install SimpleITK") from exc

from config import DEFAULT_OVERLAP, DEFAULT_PATCH_SIZE, DEFAULT_THRESHOLD, parse_patch_size
from metal_artifact_dataset import normalize_ct
from unet3d import UNet3D


def load_model(checkpoint_path: Path, device: torch.device) -> UNet3D:
    try:
        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    except TypeError:
        checkpoint = torch.load(checkpoint_path, map_location=device)
    config = checkpoint.get("model_config", {})
    model = UNet3D(
        in_channels=int(config.get("in_channels", 1)),
        out_channels=int(config.get("out_channels", 1)),
        base_channels=int(config.get("base_channels", 16)),
        depth=int(config.get("depth", 3)),
        norm=str(config.get("norm", "instance")),
    )
    model.load_state_dict(checkpoint["model_state"])
    model.to(device)
    model.eval()
    return model


def starts_for_axis(size: int, patch: int, stride: int) -> list[int]:
    if size <= patch:
        return [0]
    starts = list(range(0, size - patch + 1, stride))
    if starts[-1] != size - patch:
        starts.append(size - patch)
    return starts


def pad_to_patch(volume: np.ndarray, patch_size: tuple[int, int, int]) -> tuple[np.ndarray, tuple[slice, slice, slice]]:
    pads: list[tuple[int, int]] = []
    crop: list[slice] = []
    for size, patch in zip(volume.shape, patch_size):
        total = max(0, patch - int(size))
        before = total // 2
        after = total - before
        pads.append((before, after))
        crop.append(slice(before, before + size))
    if any(before or after for before, after in pads):
        volume = np.pad(volume, pads, mode="edge")
    return volume, (crop[0], crop[1], crop[2])


def predict_volume(
    model: UNet3D,
    volume: np.ndarray,
    patch_size: tuple[int, int, int],
    overlap: float,
    threshold: float,
    device: torch.device,
) -> np.ndarray:
    if not 0.0 <= overlap < 1.0:
        raise ValueError("overlap must be in [0, 1)")
    padded, crop = pad_to_patch(volume, patch_size)
    normalized = normalize_ct(padded, (-1000.0, 3000.0)).astype(np.float32, copy=False)

    stride = tuple(max(1, int(size * (1.0 - overlap))) for size in patch_size)
    starts = [starts_for_axis(size, patch, step) for size, patch, step in zip(normalized.shape, patch_size, stride)]
    prob_sum = np.zeros(normalized.shape, dtype=np.float32)
    count = np.zeros(normalized.shape, dtype=np.float32)

    with torch.no_grad():
        for z in starts[0]:
            for y in starts[1]:
                for x in starts[2]:
                    dz, dy, dx = patch_size
                    patch = normalized[z : z + dz, y : y + dy, x : x + dx]
                    tensor = torch.from_numpy(patch[None, None, ...].copy()).to(device=device, dtype=torch.float32)
                    logits = model(tensor)
                    probs = torch.sigmoid(logits).detach().cpu().numpy()[0, 0]
                    prob_sum[z : z + dz, y : y + dy, x : x + dx] += probs
                    count[z : z + dz, y : y + dy, x : x + dx] += 1.0

    probs = prob_sum / np.maximum(count, 1.0)
    probs = probs[crop]
    return (probs >= threshold).astype(np.uint8)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict metal artifact mask from a CT NIfTI volume.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--patch-size", type=parse_patch_size, default=DEFAULT_PATCH_SIZE)
    parser.add_argument("--overlap", type=float, default=DEFAULT_OVERLAP)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)

    image = sitk.ReadImage(str(args.input))
    volume = sitk.GetArrayFromImage(image).astype(np.float32, copy=False)
    model = load_model(args.checkpoint, device)
    mask = predict_volume(model, volume, args.patch_size, args.overlap, args.threshold, device)

    output = sitk.GetImageFromArray(mask)
    output.CopyInformation(image)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sitk.WriteImage(output, str(args.output))
    print(f"saved prediction={args.output} shape={tuple(mask.shape)} positive_voxels={int(mask.sum())}")


if __name__ == "__main__":
    main()
