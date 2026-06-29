"""Train the first-stage intracranial hemorrhage classifier."""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

try:
    from .config import (
        BATCH_SIZE,
        EPOCHS,
        GRAD_ACCUM_STEPS,
        INPUT_SHAPE,
        LABEL_MAP,
        LABELS_CSV,
        LR,
        NUM_WORKERS,
        RUN_DIR,
        SEED,
        THRESHOLD,
        WEIGHT_DECAY,
        WINDOW_MAX,
        WINDOW_MIN,
        parse_shape,
    )
    from .dataset import HemorrhageDataset, load_records, split_records, split_train_val
    from .metrics import classification_metrics
    from .model import Hemorrhage3DCNN, count_parameters
except ImportError:  # pragma: no cover - direct script fallback.
    from config import BATCH_SIZE, EPOCHS, GRAD_ACCUM_STEPS, INPUT_SHAPE, LABEL_MAP, LABELS_CSV, LR, NUM_WORKERS, RUN_DIR, SEED, THRESHOLD, WEIGHT_DECAY, WINDOW_MAX, WINDOW_MIN, parse_shape
    from dataset import HemorrhageDataset, load_records, split_records, split_train_val
    from metrics import classification_metrics
    from model import Hemorrhage3DCNN, count_parameters


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


def run_epoch(model: nn.Module, loader: DataLoader, criterion: nn.Module, device: torch.device, optimizer=None, accum_steps: int = 1) -> dict:
    training = optimizer is not None
    model.train(training)
    losses: list[float] = []
    labels: list[int] = []
    scores: list[float] = []
    if training:
        optimizer.zero_grad(set_to_none=True)
    for step, (images, targets) in enumerate(loader, start=1):
        images = images.to(device=device, dtype=torch.float32, non_blocking=True)
        targets = targets.to(device=device, dtype=torch.float32, non_blocking=True)
        with torch.set_grad_enabled(training):
            logits = model(images)
            loss = criterion(logits, targets)
            if training:
                (loss / max(accum_steps, 1)).backward()
                if step % max(accum_steps, 1) == 0 or step == len(loader):
                    optimizer.step()
                    optimizer.zero_grad(set_to_none=True)
        probs = torch.sigmoid(logits.detach()).cpu().numpy().reshape(-1)
        scores.extend(float(score) for score in probs)
        labels.extend(int(label) for label in targets.detach().cpu().numpy().reshape(-1))
        losses.append(float(loss.detach().cpu()))
    metrics = classification_metrics(labels, scores)
    metrics["loss"] = float(np.mean(losses)) if losses else 0.0
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train hemorrhage series/study classifier.")
    parser.add_argument("--labels-csv", type=Path, default=LABELS_CSV)
    parser.add_argument("--output-dir", type=Path, default=RUN_DIR)
    parser.add_argument("--input-shape", type=parse_shape, default=INPUT_SHAPE)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--lr", type=float, default=LR)
    parser.add_argument("--weight-decay", type=float, default=WEIGHT_DECAY)
    parser.add_argument("--num-workers", type=int, default=NUM_WORKERS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--base-channels", type=int, default=16)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--val-fraction", type=float, default=0.15)
    parser.add_argument("--accum-steps", type=int, default=GRAD_ACCUM_STEPS)
    parser.add_argument("--cache-dir", type=Path, default=None, help="optional preprocessed tensor cache directory")
    parser.add_argument("--resume", type=Path, default=None, help="resume from last.pt/interrupted.pt checkpoint")
    return parser.parse_args()


def load_training_checkpoint(path: Optional[Path], device: torch.device) -> Optional[dict]:
    if path is None:
        return None
    try:
        return torch.load(path, map_location=device, weights_only=True)
    except TypeError:
        return torch.load(path, map_location=device)


def save_checkpoint(
    path: Path,
    *,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler.LRScheduler,
    args: argparse.Namespace,
    epoch: int,
    metrics: dict,
    history: list[dict],
    best_score: float,
    checkpoint_type: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "scheduler_state": scheduler.state_dict(),
            "input_shape": tuple(args.input_shape),
            "base_channels": args.base_channels,
            "dropout": args.dropout,
            "threshold": THRESHOLD,
            "label_map": LABEL_MAP,
            "epoch": epoch,
            "metrics": metrics,
            "history": history,
            "best_score": best_score,
            "seed": args.seed,
            "checkpoint_type": checkpoint_type,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        },
        path,
    )


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

    cache_dir = args.cache_dir
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
    train_dataset = HemorrhageDataset(train_records, args.input_shape, WINDOW_MIN, WINDOW_MAX, cache_dir=cache_dir)
    val_dataset = HemorrhageDataset(val_records, args.input_shape, WINDOW_MIN, WINDOW_MAX, cache_dir=cache_dir)
    loader_options = {
        "num_workers": args.num_workers,
        "pin_memory": device.type == "cuda",
        "persistent_workers": args.num_workers > 0,
    }
    if args.num_workers > 0:
        loader_options["prefetch_factor"] = 2
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, **loader_options)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, **loader_options)

    model = Hemorrhage3DCNN(base_channels=args.base_channels, dropout=args.dropout).to(device)
    pos_weight = torch.tensor([compute_pos_weight(train_records)], device=device, dtype=torch.float32)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(args.epochs, 1))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    best_score = -1.0
    history = []
    start_epoch = 1
    resumed = load_training_checkpoint(args.resume, device)
    if resumed is not None:
        model.load_state_dict(resumed["model_state"])
        if "optimizer_state" in resumed:
            optimizer.load_state_dict(resumed["optimizer_state"])
        if "scheduler_state" in resumed:
            scheduler.load_state_dict(resumed["scheduler_state"])
        history = list(resumed.get("history", []))
        best_score = float(resumed.get("best_score", best_score))
        start_epoch = int(resumed.get("epoch", 0)) + 1
        print(f"resumed from {args.resume} at epoch={start_epoch}")

    last_path = args.output_dir / "last.pt"
    best_path = args.output_dir / "best.pt"
    interrupted_path = args.output_dir / "interrupted.pt"
    last_row: dict = {}
    try:
        for epoch in range(start_epoch, args.epochs + 1):
            train_metrics = run_epoch(model, train_loader, criterion, device, optimizer, args.accum_steps)
            with torch.inference_mode():
                val_metrics = run_epoch(model, val_loader, criterion, device)
            scheduler.step()
            score = val_metrics["auc"] if val_metrics["auc"] is not None else val_metrics["sensitivity"]
            row = {"epoch": epoch, "train": train_metrics, "val": val_metrics}
            last_row = row
            history.append(row)
            print(f"epoch={epoch:03d} train_loss={train_metrics['loss']:.4f} val_loss={val_metrics['loss']:.4f} val_auc={val_metrics['auc']}")
            save_checkpoint(
                last_path,
                model=model,
                optimizer=optimizer,
                scheduler=scheduler,
                args=args,
                epoch=epoch,
                metrics=row,
                history=history,
                best_score=best_score,
                checkpoint_type="last",
            )
            if float(score or 0.0) >= best_score:
                best_score = float(score or 0.0)
                save_checkpoint(
                    best_path,
                    model=model,
                    optimizer=optimizer,
                    scheduler=scheduler,
                    args=args,
                    epoch=epoch,
                    metrics=row,
                    history=history,
                    best_score=best_score,
                    checkpoint_type="best",
                )
    except KeyboardInterrupt:
        save_checkpoint(
            interrupted_path,
            model=model,
            optimizer=optimizer,
            scheduler=scheduler,
            args=args,
            epoch=max(start_epoch - 1, history[-1]["epoch"] if history else 0),
            metrics=last_row,
            history=history,
            best_score=best_score,
            checkpoint_type="interrupted",
        )
        print(f"training interrupted; saved checkpoint={interrupted_path}")
        raise

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "labels_csv": str(args.labels_csv.resolve()),
        "cache_dir": str(cache_dir.resolve()) if cache_dir else None,
        "train_records": len(train_records),
        "val_records": len(val_records),
        "parameters": count_parameters(model),
        "device": str(device),
        "best_score": best_score,
        "history": history,
    }
    (args.output_dir / "metrics.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output_dir / "label_map.json").write_text(json.dumps(LABEL_MAP, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output_dir / "train_config.json").write_text(json.dumps(vars(args), ensure_ascii=False, indent=2, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
