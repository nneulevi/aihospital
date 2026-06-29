"""Prepare RSNA Intracranial Hemorrhage DICOM slices for local training.

The RSNA Kaggle label file uses rows like:

    ID_000012eaf_any,0
    ID_000012eaf_epidural,0

This script groups those rows by DICOM image ID, converts each slice to
NIfTI, and writes a labels.csv compatible with train.py/train_monai.py.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path


SUBTYPES = ["epidural", "intraparenchymal", "intraventricular", "subarachnoid", "subdural"]
ALL_COLUMNS = ["any", *SUBTYPES]


@dataclass
class RsnaSliceLabel:
    image_id: str
    labels: dict[str, int]

    @property
    def hemorrhage(self) -> int:
        if "any" in self.labels:
            return int(self.labels["any"])
        return int(any(self.labels.get(column, 0) for column in SUBTYPES))


def _to_binary(value: object) -> int:
    try:
        return 1 if float(str(value).strip()) > 0 else 0
    except ValueError:
        return 0


def parse_rsna_label_id(raw_id: str) -> tuple[str, str]:
    parts = raw_id.rsplit("_", 1)
    if len(parts) != 2 or parts[1] not in ALL_COLUMNS:
        raise ValueError(f"invalid RSNA label id: {raw_id}")
    return parts[0], parts[1]


def load_rsna_labels(labels_csv: Path) -> list[RsnaSliceLabel]:
    grouped: dict[str, dict[str, int]] = {}
    with labels_csv.open("r", encoding="utf-8-sig", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        if not {"ID", "Label"}.issubset(set(reader.fieldnames or [])):
            raise ValueError("RSNA labels CSV must contain ID and Label columns")
        for row in reader:
            image_id, column = parse_rsna_label_id(row["ID"])
            grouped.setdefault(image_id, {})[column] = _to_binary(row.get("Label", 0))
    return [RsnaSliceLabel(image_id=image_id, labels=labels) for image_id, labels in sorted(grouped.items())]


def deterministic_split(case_id: str, val_fraction: float, test_fraction: float, seed: int) -> str:
    digest = hashlib.sha1(f"{seed}:{case_id}".encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) / 0xFFFFFFFF
    if bucket < test_fraction:
        return "test"
    if bucket < test_fraction + val_fraction:
        return "val"
    return "train"


def find_dicom_path(dicom_root: Path, image_id: str) -> Path | None:
    direct = dicom_root / f"{image_id}.dcm"
    if direct.exists():
        return direct
    matches = list(dicom_root.rglob(f"{image_id}.dcm"))
    return matches[0] if matches else None


def convert_dicom_to_nifti(dicom_path: Path, output_path: Path) -> dict[str, object]:
    try:
        import SimpleITK as sitk  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency guard.
        raise RuntimeError("SimpleITK is required to convert RSNA DICOM files.") from exc
    image = sitk.ReadImage(str(dicom_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sitk.WriteImage(image, str(output_path))
    return {
        "image_size_xyz": "x".join(str(v) for v in image.GetSize()),
        "spacing": "x".join(f"{float(v):g}" for v in image.GetSpacing()),
    }


def prepare_rsna_dataset(
    *,
    labels_csv: Path,
    dicom_root: Path,
    output_dir: Path,
    val_fraction: float,
    test_fraction: float,
    seed: int,
    limit: int | None,
    skip_existing: bool,
) -> dict[str, int]:
    records = load_rsna_labels(labels_csv)
    if limit is not None:
        records = records[: max(limit, 0)]
    images_dir = output_dir / "images"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_rows: list[dict[str, object]] = []
    missing = 0
    converted = 0
    skipped_existing = 0
    for record in records:
        dicom_path = find_dicom_path(dicom_root, record.image_id)
        if dicom_path is None:
            missing += 1
            continue
        image_name = f"{record.image_id}.nii.gz"
        image_path = images_dir / image_name
        metadata: dict[str, object] = {}
        if skip_existing and image_path.exists():
            skipped_existing += 1
        else:
            metadata = convert_dicom_to_nifti(dicom_path, image_path)
            converted += 1
        split = deterministic_split(record.image_id, val_fraction, test_fraction, seed)
        output_rows.append(
            {
                "case_id": record.image_id,
                "image_path": f"images/{image_name}",
                "hemorrhage": record.hemorrhage,
                **{column: record.labels.get(column, 0) for column in SUBTYPES},
                "source": "RSNA-IHD",
                "split": split,
                "patient_id": "",
                "study_id": "",
                "series_id": "",
                "dicom_path": str(dicom_path),
                **metadata,
            }
        )

    output_csv = output_dir / "labels.csv"
    fieldnames = [
        "case_id",
        "image_path",
        "hemorrhage",
        *SUBTYPES,
        "source",
        "split",
        "patient_id",
        "study_id",
        "series_id",
        "dicom_path",
        "image_size_xyz",
        "spacing",
    ]
    with output_csv.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    return {
        "labels": len(records),
        "written": len(output_rows),
        "missing_dicom": missing,
        "converted": converted,
        "skipped_existing": skipped_existing,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare RSNA ICH DICOM slices as NIfTI training records.")
    parser.add_argument("--rsna-labels-csv", type=Path, required=True, help="RSNA stage_2_train.csv style label file")
    parser.add_argument("--dicom-root", type=Path, required=True, help="directory containing RSNA *.dcm files")
    parser.add_argument("--output-dir", type=Path, default=Path("HeadCTLesionDetection/datasets/hemorrhage_rsna"))
    parser.add_argument("--val-fraction", type=float, default=0.1)
    parser.add_argument("--test-fraction", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--limit", type=int, default=None, help="optional limit for quick smoke conversion")
    parser.add_argument("--skip-existing", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = prepare_rsna_dataset(
        labels_csv=args.rsna_labels_csv,
        dicom_root=args.dicom_root,
        output_dir=args.output_dir,
        val_fraction=args.val_fraction,
        test_fraction=args.test_fraction,
        seed=args.seed,
        limit=args.limit,
        skip_existing=args.skip_existing,
    )
    print(summary)


if __name__ == "__main__":
    main()
