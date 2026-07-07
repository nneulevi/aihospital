"""Evaluate a trained hemorrhage classifier on a split from labels.csv."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

try:
    from .config import LABELS_CSV, RUN_DIR, THRESHOLD
    from .dataset import load_records, split_records
    from .infer import predict_hemorrhage, predict_vinbigdata_hemorrhage
    from .metrics import classification_metrics
except ImportError:  # pragma: no cover - direct script fallback.
    from config import LABELS_CSV, RUN_DIR, THRESHOLD
    from dataset import load_records, split_records
    from infer import predict_hemorrhage, predict_vinbigdata_hemorrhage
    from metrics import classification_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate hemorrhage classifier.")
    parser.add_argument("--labels-csv", type=Path, default=LABELS_CSV)
    parser.add_argument("--checkpoint", type=Path, default=RUN_DIR / "best.pt")
    parser.add_argument("--provider", choices=["local", "vinbigdata"], default="local")
    parser.add_argument("--split", choices=["train", "val", "test", "all"], default="test")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--output-dir", type=Path, default=RUN_DIR / "eval")
    parser.add_argument("--threshold", type=float, default=THRESHOLD)
    parser.add_argument("--calibrate-threshold", action="store_true", help="scan thresholds on the selected split and write calibration.json")
    parser.add_argument("--vinbigdata-image-size", type=int, default=512)
    parser.add_argument("--vinbigdata-max-slices", type=int, default=64)
    parser.add_argument("--vinbigdata-sampling-offsets", default="0", help="comma-separated slice sampling offsets, e.g. -0.25,0,0.25")
    parser.add_argument("--vinbigdata-tta-flip", action="store_true", help="average original and horizontally flipped inference")
    return parser.parse_args()


def parse_float_csv(text: str) -> tuple[float, ...]:
    values = []
    for item in text.split(","):
        item = item.strip()
        if item:
            values.append(float(item))
    return tuple(values) or (0.0,)


def threshold_grid() -> list[float]:
    return [round(index / 100, 2) for index in range(1, 100)]


def choose_threshold(labels: list[int], scores: list[float]) -> dict[str, object]:
    rows = []
    for threshold in threshold_grid():
        metrics = classification_metrics(labels, scores, threshold)
        youden = float(metrics["sensitivity"] or 0.0) + float(metrics["specificity"] or 0.0) - 1.0
        row = dict(metrics)
        row["youden"] = youden
        rows.append(row)
    best_f1 = max(rows, key=lambda item: (float(item["f1"] or 0.0), float(item["sensitivity"] or 0.0)))
    best_youden = max(rows, key=lambda item: (float(item["youden"] or 0.0), float(item["sensitivity"] or 0.0)))
    return {
        "best_f1": best_f1,
        "best_youden": best_youden,
        "thresholds": rows,
    }


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
        if args.provider == "vinbigdata":
            result = predict_vinbigdata_hemorrhage(
                record.image_path,
                args.checkpoint,
                args.device,
                threshold=args.threshold,
                image_size=args.vinbigdata_image_size,
                max_slices=args.vinbigdata_max_slices,
                sampling_offsets=parse_float_csv(args.vinbigdata_sampling_offsets),
                tta_flip=args.vinbigdata_tta_flip,
            )
        else:
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
    metrics["provider"] = args.provider
    metrics["checkpoint"] = str(args.checkpoint)
    if args.provider == "vinbigdata":
        metrics["inference_strategy"] = {
            "sampling_offsets": list(parse_float_csv(args.vinbigdata_sampling_offsets)),
            "tta_flip": bool(args.vinbigdata_tta_flip),
            "image_size": args.vinbigdata_image_size,
            "max_slices": args.vinbigdata_max_slices,
        }
    if args.calibrate_threshold:
        calibration = choose_threshold(labels, scores)
        (args.output_dir / "calibration.json").write_text(json.dumps(calibration, ensure_ascii=False, indent=2), encoding="utf-8")
        metrics["calibration"] = {
            "best_f1_threshold": calibration["best_f1"]["threshold"],
            "best_youden_threshold": calibration["best_youden"]["threshold"],
        }
    (args.output_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    with (args.output_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=["case_id", "image_path", "label", "confidence", "pred"])
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
