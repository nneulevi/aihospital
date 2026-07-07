"""Convert CQ500 official reads.csv into project labels.csv."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Any


SUBTYPE_COLUMNS = {
    "epidural": ("EDH", "Epidural"),
    "intraparenchymal": ("IPH", "Intraparenchymal", "Intra parenchymal"),
    "intraventricular": ("IVH", "Intraventricular"),
    "subarachnoid": ("SAH", "Subarachnoid"),
    "subdural": ("SDH", "Subdural"),
}


def normalize_case_id(value: str) -> str:
    digits = re.findall(r"\d+", value)
    if not digits:
        return value.strip().upper().replace("-", "")
    return f"CQ500CT{digits[-1]}"


def _binary(value: Any) -> int | None:
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "positive"}:
        return 1
    if text in {"0", "false", "no", "negative"}:
        return 0
    return None


def _matching_columns(fieldnames: list[str], terms: tuple[str, ...]) -> list[str]:
    matches = []
    for field in fieldnames:
        normalized = field.lower().replace("_", " ").replace("-", " ")
        if any(term.lower() in normalized for term in terms):
            matches.append(field)
    return matches


def majority_vote(row: dict[str, str], columns: list[str]) -> int:
    values = [_binary(row.get(column, "")) for column in columns]
    votes = [value for value in values if value is not None]
    if not votes:
        return 0
    return 1 if sum(votes) >= 2 else 0


def load_reads(reads_csv: Path) -> dict[str, dict[str, int]]:
    with reads_csv.open("r", encoding="utf-8-sig", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        fieldnames = reader.fieldnames or []
        if "name" not in fieldnames:
            raise ValueError("CQ500 reads.csv must contain a name column")
        ich_columns = _matching_columns(fieldnames, ("ICH", "Hemorrhage", "Haemorrhage"))
        subtype_columns = {
            subtype: _matching_columns(fieldnames, terms)
            for subtype, terms in SUBTYPE_COLUMNS.items()
        }
        labels = {}
        for row in reader:
            case_id = normalize_case_id(row.get("name", ""))
            subtype_votes = {
                subtype: majority_vote(row, columns)
                for subtype, columns in subtype_columns.items()
            }
            hemorrhage = majority_vote(row, ich_columns) if ich_columns else int(any(subtype_votes.values()))
            labels[case_id] = {"hemorrhage": hemorrhage, **subtype_votes}
        return labels


def build_labels(manifest_csv: Path, reads_csv: Path) -> list[dict[str, Any]]:
    labels = load_reads(reads_csv)
    rows = []
    with manifest_csv.open("r", encoding="utf-8-sig", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        for row in reader:
            if row.get("status") and row.get("status") != "converted":
                continue
            case_id = normalize_case_id(row.get("case_id", ""))
            label = labels.get(case_id)
            if label is None:
                continue
            rows.append(
                {
                    "case_id": case_id,
                    "image_path": row.get("image_path", ""),
                    "hemorrhage": label["hemorrhage"],
                    "source": "CQ500_reads_majority_vote",
                    "split": row.get("split") or "val",
                    "epidural": label["epidural"],
                    "intraparenchymal": label["intraparenchymal"],
                    "intraventricular": label["intraventricular"],
                    "subarachnoid": label["subarachnoid"],
                    "subdural": label["subdural"],
                }
            )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build labels.csv from CQ500 manifest and official reads.csv.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--reads-csv", type=Path, required=True)
    parser.add_argument("--output-labels-csv", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = build_labels(args.manifest, args.reads_csv)
    if not rows:
        raise ValueError("no manifest rows matched CQ500 reads labels")
    args.output_labels_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "case_id",
        "image_path",
        "hemorrhage",
        "source",
        "split",
        "epidural",
        "intraparenchymal",
        "intraventricular",
        "subarachnoid",
        "subdural",
    ]
    with args.output_labels_csv.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"labels_csv={args.output_labels_csv}")
    print(f"rows={len(rows)}")


if __name__ == "__main__":
    main()
