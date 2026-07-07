"""Convert a reviewed label template into labels.csv for evaluation/training."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


LABEL_COLUMNS = ["hemorrhage", "epidural", "intraparenchymal", "intraventricular", "subarachnoid", "subdural"]


def has_reviewed_label(row: dict[str, str]) -> bool:
    return any(str(row.get(column, "")).strip() != "" for column in LABEL_COLUMNS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Filter reviewed CQ500 template rows into labels.csv.")
    parser.add_argument("--review-csv", type=Path, required=True)
    parser.add_argument("--output-labels-csv", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with args.review_csv.open("r", encoding="utf-8-sig", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        if not reader.fieldnames:
            raise ValueError("review CSV has no header")
        required = {"case_id", "image_path", "split"}
        missing = required - set(reader.fieldnames)
        if missing:
            raise ValueError(f"review CSV missing required columns: {sorted(missing)}")
        rows = [row for row in reader if has_reviewed_label(row)]

    if not rows:
        raise ValueError("no reviewed labels found; fill hemorrhage or subtype columns before finalizing labels.csv")

    fieldnames = ["case_id", "image_path", "hemorrhage", "source", "split", *LABEL_COLUMNS[1:]]
    args.output_labels_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_labels_csv.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            output = {
                "case_id": row["case_id"],
                "image_path": row["image_path"],
                "hemorrhage": row.get("hemorrhage", ""),
                "source": row.get("source") or "CQ500",
                "split": row.get("split") or "val",
                "epidural": row.get("epidural", ""),
                "intraparenchymal": row.get("intraparenchymal", ""),
                "intraventricular": row.get("intraventricular", ""),
                "subarachnoid": row.get("subarachnoid", ""),
                "subdural": row.get("subdural", ""),
            }
            writer.writerow(output)
    print(f"labels_csv={args.output_labels_csv}")
    print(f"reviewed_rows={len(rows)}")


if __name__ == "__main__":
    main()
