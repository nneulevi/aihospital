"""Create a mask acquisition template for hemorrhage segmentation training."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate expected mask paths for future hemorrhage segmentation labels.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--mask-dir", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.mask_dir.mkdir(parents=True, exist_ok=True)
    fieldnames = ["case_id", "image_path", "expected_mask_path", "mask_exists", "annotation_status", "review_note"]
    rows = []
    with args.manifest.open("r", encoding="utf-8-sig", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        for row in reader:
            if row.get("status") != "converted":
                continue
            mask_path = args.mask_dir / f"{row['case_id']}.nii.gz"
            rows.append(
                {
                    "case_id": row["case_id"],
                    "image_path": row["image_path"],
                    "expected_mask_path": str(mask_path),
                    "mask_exists": int(mask_path.exists()),
                    "annotation_status": "ready" if mask_path.exists() else "mask_required",
                    "review_note": "",
                }
            )
    with args.output_csv.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"segmentation_template={args.output_csv}")
    print(f"rows={len(rows)}")
    print(f"mask_dir={args.mask_dir}")


if __name__ == "__main__":
    main()
