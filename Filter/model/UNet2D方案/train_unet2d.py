"""Train the standalone 2D U-Net baseline."""

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
from torch.utils.data import DataLoader, WeightedRandomSampler

from config_2d import (
    ACCUM_STEPS,
    BASE_CHANNELS,
    BATCH_SIZE,
    BCE_WEIGHT,
    CACHE_ITEMS,
    CT_DIR,
    DICE_WEIGHT,
    EPOCHS,
    GRAD_CLIP,
    LR,
    MASK_DIR,
    MAX_POS_WEIGHT,
    NUM_WORKERS,
    RUN_DIR,
    SEED,
    THRESHOLD,
    VAL_FRACTION,
    WEIGHT_DECAY,
    parse_size,
)
from dataset_2d import (
    CTArtifactSliceDataset,
    build_slice_index,
    compute_slice_pixel_balance,
    load_default_records,
    split_slice_records,
)
from unet2d import UNet2D, count_parameters


def set_reproducible(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    try:
        torch.use_deterministic_algorithms(True, warn_only=True)
    except TypeError:
        torch.use_deterministic_algorithms(True)


class DiceBCEWithLogitsLoss(nn.Module):
    def __init__(self, pos_weight: float, dice_weight: float, bce_weight: float) -> None:
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
        dice_loss = 1.0 - ((2.0 * intersection + 1.0) / (denominator + 1.0)).mean()
        return self.dice_weight * dice_loss + self.bce_weight * bce, dice_loss.detach(), bce.detach()


def metrics_from_logits(logits: Tensor, targets: Tensor, threshold: float) -> dict[str, float]:
    preds = (torch.sigmoid(logits) >= threshold).to(targets.dtype).reshape(-1)
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
    accum_steps: int = 1,
    grad_clip: float = 0.0,
) -> dict[str, float]:
    training = optimizer is not None
    model.train(training)
    total = {"loss": 0.0, "dice_loss": 0.0, "bce_loss": 0.0, "dice": 0.0, "iou": 0.0, "recall": 0.0, "precision": 0.0}
    batches = 0
    if training:
        optimizer.zero_grad(set_to_none=True)
    for step, (image, mask) in enumerate(loader, start=1):
        image = image.to(device=device, dtype=torch.float32, non_blocking=True)
        mask = mask.to(device=device, dtype=torch.float32, non_blocking=True)
        with torch.set_grad_enabled(training):
            logits = model(image)
            loss, dice_loss, bce_loss = criterion(logits, mask)
            if training:
                (loss / max(accum_steps, 1)).backward()
                if step % max(accum_steps, 1) == 0 or step == len(loader):
                    if grad_clip > 0:
                        torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
                    optimizer.step()
                    optimizer.zero_grad(set_to_none=True)
        batch_metrics = metrics_from_logits(logits.detach(), mask, threshold)
        total["loss"] += float(loss.detach().cpu())
        total["dice_loss"] += float(dice_loss.detach().cpu())
        total["bce_loss"] += float(bce_loss.detach().cpu())
        for key in ["dice", "iou", "recall", "precision"]:
            total[key] += batch_metrics[key]
        batches += 1
    total["batches"] = float(batches)
    return {key: value / max(batches, 1) for key, value in total.items()}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train 2D U-Net baseline on axial CT slices.")
    parser.add_argument("--ct-dir", type=Path, default=CT_DIR)
    parser.add_argument("--mask-dir", type=Path, default=MASK_DIR)
    parser.add_argument("--output-dir", type=Path, default=RUN_DIR)
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--size", type=parse_size, default=None, help="optional resize, e.g. 256,256")
    parser.add_argument("--base-channels", type=int, default=BASE_CHANNELS)
    parser.add_argument("--lr", type=float, default=LR)
    parser.add_argument("--weight-decay", type=float, default=WEIGHT_DECAY)
    parser.add_argument("--val-fraction", type=float, default=VAL_FRACTION)
    parser.add_argument("--keep-empty-fraction", type=float, default=0.25)
    parser.add_argument("--dice-weight", type=float, default=DICE_WEIGHT)
    parser.add_argument("--bce-weight", type=float, default=BCE_WEIGHT)
    parser.add_argument("--max-pos-weight", type=float, default=MAX_POS_WEIGHT)
    parser.add_argument("--threshold", type=float, default=THRESHOLD)
    parser.add_argument("--accum-steps", type=int, default=ACCUM_STEPS)
    parser.add_argument("--grad-clip", type=float, default=GRAD_CLIP)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--num-workers", type=int, default=NUM_WORKERS)
    parser.add_argument("--cache-items", type=int, default=CACHE_ITEMS, help="number of CT/mask volumes cached per dataset worker")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--no-augment", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    set_reproducible(args.seed)
    device = torch.device("cuda" if args.device == "auto" and torch.cuda.is_available() else ("cpu" if args.device == "auto" else args.device))
    records = load_default_records(args.ct_dir, args.mask_dir)
    slices = build_slice_index(records, args.keep_empty_fraction, args.seed)
    train_slices, val_slices = split_slice_records(slices, args.val_fraction, args.seed)
    pos_slices = sum(1 for item in train_slices if item.has_positive)
    weights = [5.0 if item.has_positive else 1.0 for item in train_slices]
    sampler_generator = torch.Generator()
    sampler_generator.manual_seed(args.seed)
    sampler = WeightedRandomSampler(weights, num_samples=len(weights), replacement=True, generator=sampler_generator)

    train_dataset = CTArtifactSliceDataset(
        records,
        train_slices,
        target_size=args.size,
        augment=not args.no_augment,
        seed=args.seed,
        max_cache_items=args.cache_items,
    )
    val_dataset = CTArtifactSliceDataset(
        records,
        val_slices or train_slices,
        target_size=args.size,
        augment=False,
        seed=args.seed + 1,
        max_cache_items=args.cache_items,
    )
    loader_options = {
        "num_workers": args.num_workers,
        "pin_memory": device.type == "cuda",
        "persistent_workers": args.num_workers > 0,
    }
    if args.num_workers > 0:
        loader_options["prefetch_factor"] = 2
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, sampler=sampler, **loader_options)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, **loader_options)

    positive_pixels, negative_pixels = compute_slice_pixel_balance(records, train_slices, args.size)
    pos_weight = min(args.max_pos_weight, negative_pixels / max(positive_pixels, 1))

    model = UNet2D(base_channels=args.base_channels).to(device)
    criterion = DiceBCEWithLogitsLoss(pos_weight, args.dice_weight, args.bce_weight)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(args.epochs, 1))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics: dict[str, object] = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "records": len(records),
        "slices": {"total": len(slices), "train": len(train_slices), "val": len(val_slices), "positive_train": pos_slices},
        "parameters": count_parameters(model),
        "cache_items": args.cache_items,
        "positive_pixels": positive_pixels,
        "negative_pixels": negative_pixels,
        "pos_weight": pos_weight,
        "threshold": args.threshold,
        "epochs": [],
    }
    best_dice = -1.0
    best_path = args.output_dir / "best_unet2d_metal.pt"
    last_path = args.output_dir / "last_unet2d_metal.pt"
    print(
        f"training 2D device={device} records={len(records)} train_slices={len(train_slices)} "
        f"val_slices={len(val_slices)} params={count_parameters(model):,} pos_weight={pos_weight:.3f}"
    )
    for epoch in range(1, args.epochs + 1):
        lr = float(optimizer.param_groups[0]["lr"])
        train_stats = run_epoch(model, train_loader, criterion, device, args.threshold, optimizer, args.accum_steps, args.grad_clip)
        with torch.inference_mode():
            val_stats = run_epoch(model, val_loader, criterion, device, args.threshold)
        row = {"epoch": epoch, "lr": lr, "train": train_stats, "val": val_stats}
        metrics["epochs"].append(row)
        print(
            f"epoch {epoch:03d} lr={lr:.6f} train_loss={train_stats['loss']:.4f} "
            f"val_dice={val_stats['dice']:.4f} val_iou={val_stats['iou']:.4f} "
            f"val_recall={val_stats['recall']:.4f} val_precision={val_stats['precision']:.4f}"
        )
        checkpoint = {
            "model_state": model.state_dict(),
            "model_config": {"in_channels": 1, "out_channels": 1, "base_channels": args.base_channels},
            "optimizer_state": optimizer.state_dict(),
            "scheduler_state": scheduler.state_dict(),
            "epoch": epoch,
            "metrics": row,
            "seed": args.seed,
        }
        torch.save(checkpoint, last_path)
        if val_stats["dice"] > best_dice:
            best_dice = val_stats["dice"]
            torch.save(checkpoint, best_path)
        scheduler.step()
    (args.output_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved best={best_path}")
    print(f"saved last={last_path}")
    print(f"saved metrics={args.output_dir / 'metrics.json'}")


if __name__ == "__main__":
    main()
