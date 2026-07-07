"""Generate a CQ500 review template from manifest and model predictions.

The output is intentionally not a training labels file. Human-reviewed label
columns are left blank so they cannot be mistaken for negative labels.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


SUBTYPE_COLUMNS = ["epidural", "intraparenchymal", "intraventricular", "subarachnoid", "subdural"]


def load_predictions(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    predictions: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as file_obj:
        for line in file_obj:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            case_id = str(payload.get("case_id", "")).strip()
            if case_id:
                predictions[case_id] = payload
    return predictions


def review_priority(probability: float | None, rank: int, total: int) -> str:
    if probability is None or total <= 0:
        return "unknown"
    if rank <= max(1, int(total * 0.2)):
        return "top_probability_review"
    if probability >= 0.2:
        return "high_probability"
    if probability >= 0.05:
        return "borderline_probability"
    return "low_probability"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a CQ500 label review template.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--predictions-jsonl", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    predictions = load_predictions(args.predictions_jsonl)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "case_id",
        "image_path",
        "series_dir",
        "slice_count",
        "source",
        "split",
        "positive_probability",
        "probability_rank",
        "pseudo_hemorrhage_at_0_5",
        "review_priority",
        "hemorrhage",
        *SUBTYPE_COLUMNS,
        "reviewer",
        "review_note",
    ]
    rows = []
    manifest_rows = []
    with args.manifest.open("r", encoding="utf-8-sig", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        for row in reader:
            if row.get("status") != "converted":
                continue
            pred = predictions.get(row["case_id"], {})
            probability = pred.get("positive_probability")
            probability_float = float(probability) if probability is not None else None
            manifest_rows.append((row, probability_float))
    ranked = {
        row["case_id"]: rank
        for rank, (row, _) in enumerate(
            sorted(manifest_rows, key=lambda item: -1.0 if item[1] is None else item[1], reverse=True),
            start=1,
        )
    }
    total = len(manifest_rows)
    for row, probability_float in manifest_rows:
            pred = predictions.get(row["case_id"], {})
            subtype_probs = pred.get("subtype_probabilities") or {}
            rank = ranked.get(row["case_id"], 0)
            rows.append(
                {
                    "case_id": row["case_id"],
                    "image_path": row["image_path"],
                    "series_dir": row.get("series_dir", ""),
                    "slice_count": row.get("slice_count", ""),
                    "source": "CQ500",
                    "split": "val",
                    "positive_probability": "" if probability_float is None else f"{probability_float:.8f}",
                    "probability_rank": rank or "",
                    "pseudo_hemorrhage_at_0_5": "" if probability_float is None else int(probability_float >= 0.5),
                    "review_priority": review_priority(probability_float, rank, total),
                    "hemorrhage": "",
                    "epidural": "",
                    "intraparenchymal": "",
                    "intraventricular": "",
                    "subarachnoid": "",
                    "subdural": "",
                    "reviewer": "",
                    "review_note": "",
                }
            )

    with args.output_csv.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"review_template={args.output_csv}")
    print(f"rows={len(rows)}")
    print("label_columns=blank; fill hemorrhage/subtype columns before calibration or training.")


if __name__ == "__main__":
    main()
