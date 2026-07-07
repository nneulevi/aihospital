"""Prepare CQ500 DICOM studies for hemorrhage inference/evaluation.

The script converts a bounded subset of CQ500 DICOM folders to NIfTI and writes
a manifest. If a label CSV is supplied, labels are merged into the manifest;
otherwise the output remains usable for real inference smoke and later labeling.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import SimpleITK as sitk


CASE_PATTERN = re.compile(r"^(CQ500CT\d+)\b", re.IGNORECASE)


@dataclass(frozen=True)
class CaseSeries:
    case_id: str
    case_dir: Path
    series_dir: Path
    dicom_files: list[Path]


def discover_case_dirs(dicom_root: Path) -> list[Path]:
    cases = []
    for item in dicom_root.iterdir():
        if item.is_dir() and CASE_PATTERN.match(item.name):
            cases.append(item)
    return sorted(cases, key=lambda path: path.name.lower())


def case_id_from_dir(case_dir: Path) -> str:
    match = CASE_PATTERN.match(case_dir.name)
    if not match:
        raise ValueError(f"Cannot parse CQ500 case id from {case_dir}")
    return match.group(1).upper()


def dicom_files_in(folder: Path) -> list[Path]:
    files = [path for path in folder.iterdir() if path.is_file() and path.suffix.lower() == ".dcm"]
    return sorted(files)


def score_series(path: Path, files: list[Path]) -> tuple[int, int, int, int, str]:
    name = path.name.lower()
    contrast_terms = ("contrast", "cect", "angio", "cta", "post")
    non_contrast = 0 if any(term in name for term in contrast_terms) else 1
    plain_bonus = 1 if "plain" in name or "non" in name else 0
    routine_bonus = 0 if "thin" in name else 1
    return (non_contrast, plain_bonus, routine_bonus, len(files), name)


def select_largest_series(case_dir: Path) -> Optional[CaseSeries]:
    best: Optional[tuple[tuple[int, int, str], Path, list[Path]]] = None
    for folder in case_dir.rglob("*"):
        if not folder.is_dir():
            continue
        files = dicom_files_in(folder)
        if not files:
            continue
        current = (score_series(folder, files), folder, files)
        if best is None or current[0] > best[0]:
            best = current
    if best is None:
        return None
    return CaseSeries(case_id_from_dir(case_dir), case_dir, best[1], best[2])


def read_dicom_series(series_dir: Path, files: list[Path]) -> sitk.Image:
    reader = sitk.ImageSeriesReader()
    series_ids = reader.GetGDCMSeriesIDs(str(series_dir))
    if series_ids:
        names = reader.GetGDCMSeriesFileNames(str(series_dir), series_ids[0])
    else:
        names = [str(path) for path in files]
    reader.SetFileNames(list(names))
    return reader.Execute()


def load_labels(path: Optional[Path], case_column: str, label_column: str) -> dict[str, int]:
    if not path:
        return {}
    labels: dict[str, int] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        if case_column not in (reader.fieldnames or []) or label_column not in (reader.fieldnames or []):
            raise ValueError(f"label CSV must contain columns: {case_column}, {label_column}")
        for row in reader:
            case_id = str(row.get(case_column, "")).strip().upper()
            label_text = str(row.get(label_column, "")).strip()
            if case_id and label_text:
                labels[case_id] = 1 if label_text.lower() in {"1", "true", "yes", "positive"} else 0
    return labels


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert CQ500 DICOM folders to NIfTI manifest.")
    parser.add_argument("--dicom-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--labels-csv", type=Path, default=None)
    parser.add_argument("--case-column", default="case_id")
    parser.add_argument("--label-column", default="hemorrhage")
    parser.add_argument("--limit", type=int, default=0, help="0 means all discovered cases")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.dicom_root.exists():
        raise FileNotFoundError(f"DICOM root does not exist: {args.dicom_root}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    labels = load_labels(args.labels_csv, args.case_column, args.label_column)

    case_dirs = discover_case_dirs(args.dicom_root)
    if args.limit > 0:
        case_dirs = case_dirs[: args.limit]
    rows = []
    for case_dir in case_dirs:
        selected = select_largest_series(case_dir)
        if selected is None:
            rows.append(
                {
                    "case_id": case_id_from_dir(case_dir),
                    "case_dir": str(case_dir),
                    "series_dir": "",
                    "image_path": "",
                    "slice_count": 0,
                    "split": "",
                    "hemorrhage": labels.get(case_id_from_dir(case_dir), ""),
                    "status": "no_dicom_series",
                }
            )
            continue
        output_path = args.output_dir / f"{selected.case_id}.nii.gz"
        if args.overwrite or not output_path.exists():
            image = read_dicom_series(selected.series_dir, selected.dicom_files)
            sitk.WriteImage(image, str(output_path))
        rows.append(
            {
                "case_id": selected.case_id,
                "case_dir": str(selected.case_dir),
                "series_dir": str(selected.series_dir),
                "image_path": str(output_path),
                "slice_count": len(selected.dicom_files),
                "split": "",
                "hemorrhage": labels.get(selected.case_id, ""),
                "status": "converted",
            }
        )

    fieldnames = ["case_id", "case_dir", "series_dir", "image_path", "slice_count", "split", "hemorrhage", "status"]
    with args.manifest.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    converted = sum(1 for row in rows if row["status"] == "converted")
    labeled = sum(1 for row in rows if str(row["hemorrhage"]) != "")
    print(f"manifest={args.manifest}")
    print(f"cases={len(rows)} converted={converted} labeled={labeled}")
    if converted and not labeled:
        print("labels=missing; use manifest for real inference, supply labels CSV for supervised metrics/training.")


if __name__ == "__main__":
    main()
