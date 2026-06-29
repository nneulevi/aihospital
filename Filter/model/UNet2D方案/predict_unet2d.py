"""Predict a 3D mask by applying a trained 2D U-Net to axial slices."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np
import torch

try:
    import SimpleITK as sitk
except ImportError as exc:  # pragma: no cover
    raise SystemExit("SimpleITK is required. Install it with: pip install SimpleITK") from exc

from config_2d import RUN_DIR, THRESHOLD
from dataset_2d import normalize_ct_slice
from unet2d import UNet2D


def load_model(checkpoint_path: Path, device: torch.device) -> UNet2D:
    try:
        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    except TypeError:
        checkpoint = torch.load(checkpoint_path, map_location=device)
    config = checkpoint.get("model_config", {})
    model = UNet2D(base_channels=int(config.get("base_channels", 64)))
    model.load_state_dict(checkpoint["model_state"])
    model.to(device)
    model.eval()
    return model


def predict_volume(model: UNet2D, volume: np.ndarray, threshold: float, device: torch.device) -> np.ndarray:
    masks = []
    with torch.no_grad():
        for z in range(volume.shape[0]):
            image = normalize_ct_slice(volume[z])
            tensor = torch.from_numpy(image[None, None, ...].copy()).to(device=device, dtype=torch.float32)
            probs = torch.sigmoid(model(tensor)).cpu().numpy()[0, 0]
            masks.append((probs >= threshold).astype(np.uint8))
    return np.stack(masks, axis=0)


def write_image_safe(image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        str(path).encode("ascii")
        sitk.WriteImage(image, str(path))
        return
    except UnicodeEncodeError:
        pass

    suffix = ".nii.gz" if path.name.lower().endswith(".nii.gz") else path.suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = Path(tmp.name)
    try:
        sitk.WriteImage(image, str(tmp_path))
        path.write_bytes(tmp_path.read_bytes())
    finally:
        tmp_path.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run 2D U-Net axial-slice inference.")
    parser.add_argument("--checkpoint", type=Path, default=RUN_DIR / "best_unet2d_metal.pt")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=THRESHOLD)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    device = torch.device("cuda" if args.device == "auto" and torch.cuda.is_available() else ("cpu" if args.device == "auto" else args.device))
    image = sitk.ReadImage(str(args.input))
    volume = sitk.GetArrayFromImage(image).astype(np.float32, copy=False)
    if volume.ndim == 2:
        volume = volume[None, :, :]
    model = load_model(args.checkpoint, device)
    mask = predict_volume(model, volume, args.threshold, device)
    output = sitk.GetImageFromArray(mask)
    output.CopyInformation(image)
    write_image_safe(output, args.output)
    print(f"saved prediction={args.output} shape={tuple(mask.shape)} positive_voxels={int(mask.sum())}")


if __name__ == "__main__":
    main()
