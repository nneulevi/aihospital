"""Run hemorrhage inference for a prepared manifest."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

try:
    from .infer import parse_float_csv, predict_vinbigdata_hemorrhage
except ImportError:  # pragma: no cover - direct script fallback.
    from infer import parse_float_csv, predict_vinbigdata_hemorrhage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VinBigData hemorrhage inference over manifest rows.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output-jsonl", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--image-size", type=int, default=512)
    parser.add_argument("--max-slices", type=int, default=64)
    parser.add_argument("--sampling-offsets", default="0")
    parser.add_argument("--tta-flip", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = []
    with args.manifest.open("r", encoding="utf-8-sig", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        for row in reader:
            if row.get("status") == "converted" and row.get("image_path"):
                rows.append(row)
    if args.limit > 0:
        rows = rows[: args.limit]
    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    offsets = parse_float_csv(args.sampling_offsets)
    with args.output_jsonl.open("w", encoding="utf-8") as file_obj:
        for row in rows:
            result = predict_vinbigdata_hemorrhage(
                Path(row["image_path"]),
                args.checkpoint,
                device=args.device,
                threshold=args.threshold,
                image_size=args.image_size,
                max_slices=args.max_slices,
                sampling_offsets=offsets,
                tta_flip=args.tta_flip,
            )
            payload = {
                "case_id": row["case_id"],
                "image_path": row["image_path"],
                "label": row.get("hemorrhage") or None,
                "positive_probability": result["confidence"],
                "detected": result["detected"],
                "decision_threshold": result.get("decision_threshold"),
                "subtype_probabilities": result.get("subtype_probabilities", {}),
                "inference_strategy": result.get("inference_strategy", {}),
                "checkpoint_framework": result.get("checkpoint_framework"),
            }
            file_obj.write(json.dumps(payload, ensure_ascii=False) + "\n")
            print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
