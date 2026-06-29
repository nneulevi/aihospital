"""Train hemorrhage classifier with MONAI transforms and networks."""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

try:
    from .config import BATCH_SIZE, EPOCHS, INPUT_SHAPE, LABELS_CSV, LR, RUN_DIR, SEED, THRESHOLD, WEIGHT_DECAY, parse_shape
    from .dataset import load_records, split_records, split_train_val
    from .metrics import classification_metrics
    from .monai_pipeline import build_monai_classifier, build_monai_dataset
except ImportError:  # pragma: no cover - direct script fallback.
    from config import BATCH_SIZE, EPOCHS, INPUT_SHAPE, LABELS_CSV, LR, RUN_DIR, SEED, THRESHOLD, WEIGHT_DECAY, parse_shape
    from dataset import load_records, split_records, split_train_val
    from metrics import classification_metrics
    from monai_pipeline import build_monai_classifier, build_monai_dataset


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def resolve_device(device_arg: str) -> torch.device:
    if device_arg == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(device_arg)


def compute_pos_weight(records) -> float:
    pos = sum(record.label == 1 for record in records)
    neg = sum(record.label == 0 for record in records)
    return float(neg / max(pos, 1)) if pos > 0 else 1.0


def run_epoch(model: nn.Module, loader: DataLoader, criterion: nn.Module, device: torch.device, optimizer=None) -> dict:
    training = optimizer is not None
    model.train(training)
    losses: list[float] = []
    labels: list[int] = []
    scores: list[float] = []
    for batch in loader:
        images = batch["image"].to(device=device, dtype=torch.float32, non_blocking=True)
        targets = batch["label"].to(device=device, dtype=torch.float32, non_blocking=True)
        with torch.set_grad_enabled(training):
            logits = model(images)
            loss = criterion(logits, targets)
            if training:
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                optimizer.step()
        probs = torch.sigmoid(logits.detach()).cpu().numpy().reshape(-1)
        scores.extend(float(score) for score in probs)
        labels.extend(int(label) for label in targets.detach().cpu().numpy().reshape(-1))
        losses.append(float(loss.detach().cpu()))
    metrics = classification_metrics(labels, scores, THRESHOLD)
    metrics["loss"] = float(np.mean(losses)) if losses else 0.0
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train hemorrhage classifier with MONAI.")
    parser.add_argument("--labels-csv", type=Path, default=LABELS_CSV)
    parser.add_argument("--output-dir", type=Path, default=RUN_DIR / "monai_densenet121")
    parser.add_argument("--input-shape", type=parse_shape, default=INPUT_SHAPE)
    parser.add_argument("--network", choices=["densenet121", "densenet169"], default="densenet121")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--lr", type=float, default=LR)
    parser.add_argument("--weight-decay", type=float, default=WEIGHT_DECAY)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--cache-rate", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--val-fraction", type=float, default=0.15)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    device = resolve_device(args.device)
    records = load_records(args.labels_csv)
    train_records = split_records(records, "train")
    val_records = split_records(records, "val")
    if not train_records:
        train_records, val_records = split_train_val(records, args.val_fraction, args.seed)
    if not val_records:
        val_records = train_records

    train_dataset = build_monai_dataset(train_records, args.input_shape, training=True, cache_rate=args.cache_rate)
    val_dataset = build_monai_dataset(val_records, args.input_shape, training=False, cache_rate=args.cache_rate)
    loader_options = {
        "num_workers": args.num_workers,
        "pin_memory": device.type == "cuda",
        "persistent_workers": args.num_workers > 0,
    }
    if args.num_workers > 0:
        loader_options["prefetch_factor"] = 2
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, **loader_options)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, **loader_options)

    model = build_monai_classifier(args.network).to(device)
    pos_weight = torch.tensor([compute_pos_weight(train_records)], device=device, dtype=torch.float32)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(args.epochs, 1))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    best_score = -1.0
    history = []
    for epoch in range(1, args.epochs + 1):
        train_metrics = run_epoch(model, train_loader, criterion, device, optimizer)
        with torch.inference_mode():
            val_metrics = run_epoch(model, val_loader, criterion, device)
        scheduler.step()
        score = val_metrics["auc"] if val_metrics["auc"] is not None else val_metrics["sensitivity"]
        history.append({"epoch": epoch, "train": train_metrics, "val": val_metrics})
        print(f"epoch={epoch:03d} train_loss={train_metrics['loss']:.4f} val_loss={val_metrics['loss']:.4f} val_auc={val_metrics['auc']}")
        if float(score or 0.0) >= best_score:
            best_score = float(score or 0.0)
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "input_shape": tuple(args.input_shape),
                    "network": args.network,
                    "threshold": THRESHOLD,
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                    "framework": "monai",
                },
                args.output_dir / "best.pt",
            )

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "framework": "monai",
        "network": args.network,
        "labels_csv": str(args.labels_csv.resolve()),
        "train_records": len(train_records),
        "val_records": len(val_records),
        "device": str(device),
        "best_score": best_score,
        "history": history,
    }
    (args.output_dir / "metrics.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output_dir / "train_config.json").write_text(json.dumps(vars(args), ensure_ascii=False, indent=2, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
