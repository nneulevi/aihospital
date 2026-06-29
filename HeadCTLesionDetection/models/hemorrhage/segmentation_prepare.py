"""Prepare hemorrhage segmentation data for nnU-Net-style training.

This is a data-layout helper only. It does not train nnU-Net. Use it when
pixel/voxel-level hemorrhage masks become available.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

try:
    from .dataset import load_records
except ImportError:  # pragma: no cover - direct script fallback.
    from dataset import load_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare nnU-Net style dataset from labels.csv and mask directory.")
    parser.add_argument("--labels-csv", type=Path, required=True)
    parser.add_argument("--mask-dir", type=Path, required=True, help="directory containing {case_id}.nii.gz masks")
    parser.add_argument("--output-dir", type=Path, required=True, help="nnUNet_raw/DatasetXXX_Hemorrhage")
    parser.add_argument("--dataset-name", default="Dataset501_Hemorrhage")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_records(args.labels_csv)
    images_tr = args.output_dir / "imagesTr"
    labels_tr = args.output_dir / "labelsTr"
    images_ts = args.output_dir / "imagesTs"
    images_tr.mkdir(parents=True, exist_ok=True)
    labels_tr.mkdir(parents=True, exist_ok=True)
    images_ts.mkdir(parents=True, exist_ok=True)

    training = []
    test_count = 0
    for index, record in enumerate(records):
        case_name = f"{record.case_id}"
        image_target = images_ts / f"{case_name}_0000.nii.gz" if record.split == "test" else images_tr / f"{case_name}_0000.nii.gz"
        shutil.copy2(record.image_path, image_target)
        if record.split == "test":
            test_count += 1
            continue
        mask_path = args.mask_dir / f"{record.case_id}.nii.gz"
        if not mask_path.exists():
            raise FileNotFoundError(f"missing segmentation mask for {record.case_id}: {mask_path}")
        label_target = labels_tr / f"{case_name}.nii.gz"
        shutil.copy2(mask_path, label_target)
        training.append({"image": f"./imagesTr/{case_name}_0000.nii.gz", "label": f"./labelsTr/{case_name}.nii.gz"})

    dataset_json = {
        "channel_names": {"0": "CT"},
        "labels": {"background": 0, "hemorrhage": 1},
        "numTraining": len(training),
        "numTest": test_count,
        "file_ending": ".nii.gz",
        "name": args.dataset_name,
        "description": "Head CT hemorrhage segmentation dataset prepared from project labels.csv.",
        "training": training,
    }
    (args.output_dir / "dataset.json").write_text(json.dumps(dataset_json, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"prepared nnU-Net dataset: {args.output_dir}")


if __name__ == "__main__":
    main()
