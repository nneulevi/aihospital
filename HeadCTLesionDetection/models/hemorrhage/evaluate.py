"""Evaluate a trained hemorrhage classifier on a split from labels.csv."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

try:
    from .config import LABELS_CSV, RUN_DIR, THRESHOLD
    from .dataset import load_records, split_records
    from .infer import predict_hemorrhage
    from .metrics import classification_metrics
except ImportError:  # pragma: no cover - direct script fallback.
    from config import LABELS_CSV, RUN_DIR, THRESHOLD
    from dataset import load_records, split_records
    from infer import predict_hemorrhage
    from metrics import classification_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate hemorrhage classifier.")
    parser.add_argument("--labels-csv", type=Path, default=LABELS_CSV)
    parser.add_argument("--checkpoint", type=Path, default=RUN_DIR / "best.pt")
    parser.add_argument("--split", choices=["train", "val", "test", "all"], default="test")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--output-dir", type=Path, default=RUN_DIR / "eval")
    parser.add_argument("--threshold", type=float, default=THRESHOLD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_records(args.labels_csv)
    if args.split != "all":
        records = split_records(records, args.split)
    if not records:
        raise ValueError(f"no records for split={args.split}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    labels: list[int] = []
    scores: list[float] = []
    rows = []
    for record in records:
        result = predict_hemorrhage(record.image_path, args.checkpoint, args.device)
        score = float(result["confidence"])
        labels.append(record.label)
        scores.append(score)
        rows.append(
            {
                "case_id": record.case_id,
                "image_path": str(record.image_path),
                "label": record.label,
                "confidence": score,
                "pred": int(score >= args.threshold),
            }
        )
    metrics = classification_metrics(labels, scores, args.threshold)
    (args.output_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    with (args.output_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=["case_id", "image_path", "label", "confidence", "pred"])
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
