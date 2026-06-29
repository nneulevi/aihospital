"""Train 3D U-Net to detect metal artifact masks.

The script consumes the paired CT/mask data generated under
``Filter/model/datasets`` and writes a reproducible checkpoint plus metrics.
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from torch import Tensor, nn
from torch.utils.data import DataLoader

from config import (
    CT_DIR,
    DATA_DIR,
    DEFAULT_BASE_CHANNELS,
    DEFAULT_BATCH_SIZE,
    DEFAULT_BCE_WEIGHT,
    DEFAULT_DEPTH,
    DEFAULT_DICE_WEIGHT,
    DEFAULT_EPOCHS,
    DEFAULT_GRAD_CLIP,
    DEFAULT_LR,
    DEFAULT_MAX_POS_WEIGHT,
    DEFAULT_NUM_WORKERS,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PATCH_SIZE,
    DEFAULT_POSITIVE_FRACTION,
    DEFAULT_SEED,
    DEFAULT_THRESHOLD,
    DEFAULT_TRAIN_PATCHES,
    DEFAULT_VAL_FRACTION,
    DEFAULT_VAL_PATCHES,
    DEFAULT_WEIGHT_DECAY,
    MASK_DIR,
    parse_patch_size,
)
from metal_artifact_dataset import (
    MetalArtifactPatchDataset,
    compute_mask_balance,
    compute_record_weights,
    load_directory_records,
    load_records,
    split_records,
)
from training_artifacts import write_all_artifacts
from unet3d import UNet3D, count_parameters


def set_reproducible(seed: int, deterministic: bool = True) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    if deterministic:
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
        try:
            torch.use_deterministic_algorithms(True, warn_only=True)
        except TypeError:
            torch.use_deterministic_algorithms(True)


class DiceBCEWithLogitsLoss(nn.Module):
    def __init__(self, pos_weight: float, dice_weight: float = 0.7, bce_weight: float = 0.3) -> None:
        super().__init__()
        self.register_buffer("pos_weight_tensor", torch.tensor(float(pos_weight), dtype=torch.float32))
        self.dice_weight = float(dice_weight)
        self.bce_weight = float(bce_weight)

    def forward(self, logits: Tensor, targets: Tensor) -> tuple[Tensor, Tensor, Tensor]:
        bce = nn.functional.binary_cross_entropy_with_logits(
            logits,
            targets,
            pos_weight=self.pos_weight_tensor.to(device=logits.device, dtype=logits.dtype),
        )
        probs = torch.sigmoid(logits)
        dims = tuple(range(1, probs.ndim))
        intersection = torch.sum(probs * targets, dim=dims)
        denominator = torch.sum(probs, dim=dims) + torch.sum(targets, dim=dims)
        dice = (2.0 * intersection + 1.0) / (denominator + 1.0)
        dice_loss = 1.0 - dice.mean()
        loss = self.bce_weight * bce + self.dice_weight * dice_loss
        return loss, dice_loss.detach(), bce.detach()


def segmentation_metrics_from_logits(logits: Tensor, targets: Tensor, threshold: float = 0.35) -> dict[str, float]:
    preds = (torch.sigmoid(logits) >= threshold).to(targets.dtype)
    preds = preds.reshape(-1)
    targets = targets.reshape(-1)
    intersection = torch.sum(preds * targets)
    pred_sum = torch.sum(preds)
    target_sum = torch.sum(targets)
    union = pred_sum + target_sum - intersection
    eps = torch.tensor(1e-6, device=logits.device, dtype=logits.dtype)
    return {
        "dice": float(((2.0 * intersection + eps) / (pred_sum + target_sum + eps)).detach().cpu()),
        "iou": float(((intersection + eps) / (union + eps)).detach().cpu()),
        "recall": float(((intersection + eps) / (target_sum + eps)).detach().cpu()),
        "precision": float(((intersection + eps) / (pred_sum + eps)).detach().cpu()),
    }


def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    threshold: float,
    optimizer: Optional[torch.optim.Optimizer] = None,
    grad_clip: float = 0.0,
) -> dict[str, float]:
    training = optimizer is not None
    model.train(training)
    total_loss = 0.0
    total_dice_loss = 0.0
    total_bce_loss = 0.0
    total_dice = 0.0
    total_iou = 0.0
    total_recall = 0.0
    total_precision = 0.0
    batches = 0

    for volume, mask in loader:
        volume = volume.to(device=device, dtype=torch.float32, non_blocking=True)
        mask = mask.to(device=device, dtype=torch.float32, non_blocking=True)

        with torch.set_grad_enabled(training):
            logits = model(volume)
            loss, dice_loss, bce_loss = criterion(logits, mask)
            if training:
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                if grad_clip > 0:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
                optimizer.step()

        total_loss += float(loss.detach().cpu())
        total_dice_loss += float(dice_loss.detach().cpu())
        total_bce_loss += float(bce_loss.detach().cpu())
        batch_metrics = segmentation_metrics_from_logits(logits.detach(), mask, threshold=threshold)
        total_dice += batch_metrics["dice"]
        total_iou += batch_metrics["iou"]
        total_recall += batch_metrics["recall"]
        total_precision += batch_metrics["precision"]
        batches += 1

    return {
        "loss": total_loss / max(batches, 1),
        "dice_loss": total_dice_loss / max(batches, 1),
        "bce_loss": total_bce_loss / max(batches, 1),
        "dice": total_dice / max(batches, 1),
        "iou": total_iou / max(batches, 1),
        "recall": total_recall / max(batches, 1),
        "precision": total_precision / max(batches, 1),
        "batches": float(batches),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train 3D U-Net on metal artifact mask pairs.")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR, help="directory containing CT/ and mask/")
    parser.add_argument("--ct-dir", type=Path, default=None, help=f"raw CT directory; defaults to {CT_DIR}")
    parser.add_argument("--mask-dir", type=Path, default=None, help=f"label mask directory; defaults to {MASK_DIR}")
    parser.add_argument("--manifest", type=Path, default=None, help="optional legacy Mask_mark/output manifest.json")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--patch-size", type=parse_patch_size, default=DEFAULT_PATCH_SIZE)
    parser.add_argument("--train-patches", type=int, default=DEFAULT_TRAIN_PATCHES)
    parser.add_argument("--val-patches", type=int, default=DEFAULT_VAL_PATCHES)
    parser.add_argument("--positive-fraction", type=float, default=DEFAULT_POSITIVE_FRACTION)
    parser.add_argument("--val-fraction", type=float, default=DEFAULT_VAL_FRACTION)
    parser.add_argument("--base-channels", type=int, default=DEFAULT_BASE_CHANNELS)
    parser.add_argument("--depth", type=int, default=DEFAULT_DEPTH)
    parser.add_argument("--lr", type=float, default=DEFAULT_LR)
    parser.add_argument("--weight-decay", type=float, default=DEFAULT_WEIGHT_DECAY)
    parser.add_argument("--dice-weight", type=float, default=DEFAULT_DICE_WEIGHT)
    parser.add_argument("--bce-weight", type=float, default=DEFAULT_BCE_WEIGHT)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--grad-clip", type=float, default=DEFAULT_GRAD_CLIP)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--num-workers", type=int, default=DEFAULT_NUM_WORKERS)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--max-pos-weight", type=float, default=DEFAULT_MAX_POS_WEIGHT)
    parser.add_argument("--no-augment", action="store_true")
    parser.add_argument("--sample-by-mask", action="store_true", help="sample records by positive mask volume")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    set_reproducible(args.seed)

    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)

    if args.manifest is not None:
        records = load_records(args.manifest)
        data_source = {"type": "manifest", "manifest": str(args.manifest.resolve())}
    else:
        ct_dir = args.ct_dir or args.data_dir / "CT"
        mask_dir = args.mask_dir or args.data_dir / "mask"
        records = load_directory_records(ct_dir, mask_dir)
        data_source = {
            "type": "paired_directories",
            "ct_dir": str(ct_dir.resolve()),
            "mask_dir": str(mask_dir.resolve()),
        }
    train_records, val_records = split_records(records, args.val_fraction, args.seed)
    positive, negative = compute_mask_balance(train_records)
    pos_weight = min(args.max_pos_weight, negative / max(positive, 1))
    record_weights = compute_record_weights(train_records) if args.sample_by_mask else None

    train_dataset = MetalArtifactPatchDataset(
        train_records,
        patch_size=args.patch_size,
        length=args.train_patches,
        positive_fraction=args.positive_fraction,
        seed=args.seed,
        augment=not args.no_augment,
        record_weights=record_weights,
    )
    val_dataset = MetalArtifactPatchDataset(
        val_records or train_records,
        patch_size=args.patch_size,
        length=args.val_patches,
        positive_fraction=args.positive_fraction,
        seed=args.seed + 1,
        augment=False,
    )

    generator = torch.Generator()
    generator.manual_seed(args.seed)
    loader_options = {
        "num_workers": args.num_workers,
        "pin_memory": device.type == "cuda",
        "persistent_workers": args.num_workers > 0,
    }
    if args.num_workers > 0:
        loader_options["prefetch_factor"] = 2
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        generator=generator,
        **loader_options,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        **loader_options,
    )

    model = UNet3D(
        in_channels=1,
        out_channels=1,
        base_channels=args.base_channels,
        depth=args.depth,
        norm="instance",
    ).to(device)
    criterion = DiceBCEWithLogitsLoss(
        pos_weight=pos_weight,
        dice_weight=args.dice_weight,
        bce_weight=args.bce_weight,
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(args.epochs, 1))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics: dict[str, object] = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "data_source": data_source,
        "device": str(device),
        "seed": args.seed,
        "records": {"total": len(records), "train": len(train_records), "val": len(val_records)},
        "patch_size": args.patch_size,
        "positive_voxels": positive,
        "negative_voxels": negative,
        "pos_weight": pos_weight,
        "loss_weights": {"dice": args.dice_weight, "bce": args.bce_weight},
        "threshold": args.threshold,
        "augment": not args.no_augment,
        "sample_by_mask": args.sample_by_mask,
        "parameters": count_parameters(model),
        "epochs": [],
    }

    best_val_dice = -1.0
    best_path = args.output_dir / "best_unet3d_metal.pt"
    last_path = args.output_dir / "last_unet3d_metal.pt"

    print(
        "training "
        f"device={device} records={len(records)} train={len(train_records)} val={len(val_records)} "
        f"source={data_source['type']} "
        f"patch={args.patch_size} params={count_parameters(model):,} pos_weight={pos_weight:.3f} "
        f"threshold={args.threshold:.2f}"
    )

    for epoch in range(1, args.epochs + 1):
        current_lr = float(optimizer.param_groups[0]["lr"])
        train_dataset.set_epoch(epoch)
        train_stats = run_epoch(
            model,
            train_loader,
            criterion,
            device,
            threshold=args.threshold,
            optimizer=optimizer,
            grad_clip=args.grad_clip,
        )
        with torch.inference_mode():
            val_stats = run_epoch(model, val_loader, criterion, device, threshold=args.threshold)

        row = {"epoch": epoch, "lr": current_lr, "train": train_stats, "val": val_stats}
        metrics["epochs"].append(row)
        print(
            f"epoch {epoch:03d} "
            f"lr={current_lr:.6f} "
            f"train_loss={train_stats['loss']:.4f} "
            f"train_dice_loss={train_stats['dice_loss']:.4f} train_bce={train_stats['bce_loss']:.4f} "
            f"val_dice={val_stats['dice']:.4f} val_iou={val_stats['iou']:.4f} "
            f"val_recall={val_stats['recall']:.4f} val_precision={val_stats['precision']:.4f}"
        )

        checkpoint = {
            "model_state": model.state_dict(),
            "model_config": model.config.__dict__,
            "optimizer_state": optimizer.state_dict(),
            "scheduler_state": scheduler.state_dict(),
            "epoch": epoch,
            "metrics": row,
            "seed": args.seed,
        }
        torch.save(checkpoint, last_path)
        if val_stats["dice"] > best_val_dice:
            best_val_dice = val_stats["dice"]
            torch.save(checkpoint, best_path)
        scheduler.step()

    metrics_path = args.output_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    write_all_artifacts(args.output_dir, metrics_path, args.base_channels, args.depth)
    print(f"saved best={best_path}")
    print(f"saved last={last_path}")
    print(f"saved metrics={metrics_path}")
    print(f"saved figures={args.output_dir / 'figures'}")


if __name__ == "__main__":
    main()
