"""Create result visualizations for a trained 3D U-Net run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError as exc:  # pragma: no cover - dependency guard.
    raise SystemExit("matplotlib is required for visualization. Install it with: pip install matplotlib") from exc

try:
    import SimpleITK as sitk
except ImportError as exc:  # pragma: no cover - dependency guard.
    raise SystemExit("SimpleITK is required. Install it with: pip install SimpleITK") from exc

from config import (
    CT_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OVERLAP,
    DEFAULT_PATCH_SIZE,
    DEFAULT_THRESHOLD,
    MASK_DIR,
    parse_patch_size,
)
from metal_artifact_dataset import load_directory_records
from predict_unet3d import load_model, predict_volume


def read_volume(path: Path) -> np.ndarray:
    return sitk.GetArrayFromImage(sitk.ReadImage(str(path)))


def normalize_slice(image: np.ndarray, low: float = -1000.0, high: float = 3000.0) -> np.ndarray:
    image = np.clip(image.astype(np.float32, copy=False), low, high)
    return (image - low) / max(high - low, 1e-6)


def plot_loss_curves(metrics_path: Path, output_path: Path) -> None:
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    epochs = metrics.get("epochs", [])
    if not epochs:
        raise ValueError(f"No epoch metrics found in {metrics_path}")

    xs = [int(row["epoch"]) for row in epochs]
    train_loss = [float(row["train"]["loss"]) for row in epochs]
    val_loss = [float(row["val"]["loss"]) for row in epochs]
    train_dice_loss = [float(row["train"].get("dice_loss", 0.0)) for row in epochs]
    val_dice = [float(row["val"].get("dice", 0.0)) for row in epochs]

    fig, ax1 = plt.subplots(figsize=(8.5, 5), dpi=140)
    ax1.plot(xs, train_loss, marker="o", label="train loss", color="#2d6cdf")
    ax1.plot(xs, val_loss, marker="o", label="val loss", color="#d94f45")
    ax1.plot(xs, train_dice_loss, marker="o", label="train dice loss", color="#f0a12b")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.grid(True, alpha=0.25)

    ax2 = ax1.twinx()
    ax2.plot(xs, val_dice, marker="s", label="val dice", color="#26966f")
    ax2.set_ylabel("Dice")
    ax2.set_ylim(0.0, 1.0)

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="best")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)


def confusion_counts(pred: np.ndarray, target: np.ndarray) -> np.ndarray:
    pred_bool = pred.astype(bool)
    target_bool = target.astype(bool)
    tn = int(np.count_nonzero(~pred_bool & ~target_bool))
    fp = int(np.count_nonzero(pred_bool & ~target_bool))
    fn = int(np.count_nonzero(~pred_bool & target_bool))
    tp = int(np.count_nonzero(pred_bool & target_bool))
    return np.array([[tn, fp], [fn, tp]], dtype=np.int64)


def plot_confusion_matrix(matrix: np.ndarray, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5.2, 4.6), dpi=140)
    im = ax.imshow(matrix, cmap="Blues")
    ax.set_title("Voxel Confusion Matrix")
    ax.set_xticks([0, 1], labels=["Pred 0", "Pred 1"])
    ax.set_yticks([0, 1], labels=["GT 0", "GT 1"])
    max_value = int(matrix.max()) if matrix.size else 1
    for y in range(2):
        for x in range(2):
            value = int(matrix[y, x])
            color = "white" if value > max_value * 0.5 else "#1b2a38"
            ax.text(x, y, f"{value:,}", ha="center", va="center", color=color, fontsize=10)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)


def choose_slice(mask: np.ndarray, pred: np.ndarray) -> int:
    scores = mask.reshape(mask.shape[0], -1).sum(axis=1) + pred.reshape(pred.shape[0], -1).sum(axis=1)
    if np.max(scores) <= 0:
        return mask.shape[0] // 2
    return int(np.argmax(scores))


def make_overlay(gray: np.ndarray, mask: np.ndarray, color: tuple[float, float, float]) -> np.ndarray:
    rgb = np.repeat(gray[:, :, None], 3, axis=2)
    overlay = mask.astype(bool)
    rgb[overlay] = rgb[overlay] * 0.35 + np.array(color, dtype=np.float32) * 0.65
    return np.clip(rgb, 0.0, 1.0)


def plot_sample_prediction(ct: np.ndarray, gt: np.ndarray, pred: np.ndarray, output_path: Path) -> None:
    z = choose_slice(gt, pred)
    gray = normalize_slice(ct[z])
    gt_overlay = make_overlay(gray, gt[z], (1.0, 0.1, 0.1))
    pred_overlay = make_overlay(gray, pred[z], (0.0, 0.65, 1.0))

    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2), dpi=140)
    panels = [
        ("CT", gray, "gray"),
        ("GT mask", gt_overlay, None),
        ("Prediction", pred_overlay, None),
    ]
    for ax, (title, image, cmap) in zip(axes, panels):
        ax.imshow(image, cmap=cmap)
        ax.set_title(f"{title} z={z}" if title == "CT" else title)
        ax.axis("off")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize training curves and sample segmentation results.")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--metrics", type=Path, default=None)
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--ct", type=Path, default=None)
    parser.add_argument("--mask", type=Path, default=None)
    parser.add_argument("--ct-dir", type=Path, default=CT_DIR)
    parser.add_argument("--mask-dir", type=Path, default=MASK_DIR)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--patch-size", type=parse_patch_size, default=DEFAULT_PATCH_SIZE)
    parser.add_argument("--overlap", type=float, default=DEFAULT_OVERLAP)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = args.run_dir
    output_dir = args.output_dir or run_dir / "visualizations"
    metrics_path = args.metrics or run_dir / "metrics.json"
    checkpoint_path = args.checkpoint or run_dir / "best_unet3d_metal.pt"

    if args.ct is None or args.mask is None:
        record = load_directory_records(args.ct_dir, args.mask_dir)[0]
        ct_path = args.ct or record.ct_path
        mask_path = args.mask or record.mask_path
    else:
        ct_path = args.ct
        mask_path = args.mask

    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)

    plot_loss_curves(metrics_path, output_dir / "loss_curves.png")

    ct = read_volume(ct_path).astype(np.float32, copy=False)
    gt = (read_volume(mask_path) > 0).astype(np.uint8)
    model = load_model(checkpoint_path, device)
    pred = predict_volume(model, ct, args.patch_size, args.overlap, args.threshold, device)

    matrix = confusion_counts(pred, gt)
    plot_confusion_matrix(matrix, output_dir / "confusion_matrix.png")
    plot_sample_prediction(ct, gt, pred, output_dir / "sample_ct_gt_pred.png")

    summary = {
        "metrics": str(metrics_path.resolve()),
        "checkpoint": str(checkpoint_path.resolve()),
        "ct": str(ct_path.resolve()),
        "mask": str(mask_path.resolve()),
        "threshold": args.threshold,
        "confusion_matrix": matrix.tolist(),
        "outputs": {
            "loss_curves": str((output_dir / "loss_curves.png").resolve()),
            "confusion_matrix": str((output_dir / "confusion_matrix.png").resolve()),
            "sample_ct_gt_pred": str((output_dir / "sample_ct_gt_pred.png").resolve()),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "visualization_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"saved visualizations={output_dir}")


if __name__ == "__main__":
    main()

