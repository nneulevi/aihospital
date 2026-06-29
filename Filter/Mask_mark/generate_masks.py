import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from metal_artifact_mask_tool import run_pipeline, sitk  # noqa: E402


def safe_name(text: str, fallback: str = "item") -> str:
    name = re.sub(r"[^0-9A-Za-z._-]+", "_", text.strip())
    return name.strip("._-") or fallback


def find_dicom_folders(dataset_root: Path) -> Iterable[Path]:
    for folder in sorted(p for p in dataset_root.rglob("*") if p.is_dir()):
        if any(child.suffix.lower() == ".dcm" for child in folder.iterdir() if child.is_file()):
            yield folder


def read_dicom_series(folder: Path, series_id: str) -> Tuple[np.ndarray, object, List[str]]:
    if sitk is None:
        raise RuntimeError("SimpleITK is required to read DICOM series.")
    reader = sitk.ImageSeriesReader()
    files = reader.GetGDCMSeriesFileNames(str(folder), series_id)
    if not files:
        raise RuntimeError(f"empty DICOM series: {folder} series={series_id}")
    reader.SetFileNames(files)
    image = reader.Execute()
    volume = sitk.GetArrayFromImage(image).astype(np.float32, copy=False)
    return volume, image, list(files)


def write_image_like(array: np.ndarray, template: object, path: Path) -> None:
    if sitk is None:
        return
    image = sitk.GetImageFromArray(array)
    image.CopyInformation(template)
    sitk.WriteImage(image, str(path))


def process_series(
    folder: Path,
    series_id: str,
    output_root: Path,
    params: Dict[str, float],
    save_npy: bool,
) -> Dict[str, object]:
    volume, template, files = read_dicom_series(folder, series_id)

    mask, stats, _ = run_pipeline(
        volume=volume,
        threshold_low=float(params["threshold_low"]),
        threshold_high=float(params["threshold_high"]),
        gradient_threshold=float(params["gradient_threshold"]),
        opening_radius=int(params["opening_radius"]),
        closing_radius=int(params["closing_radius"]),
        min_component_size=int(params["min_component_size"]),
    )

    case_name = safe_name(folder.parents[1].name if len(folder.parents) > 1 else folder.name, "case")
    series_name = safe_name(folder.name, "series")
    series_key = safe_name(series_id[-16:] if series_id else "series", "series")
    out_dir = output_root / case_name / f"{series_name}_{series_key}"
    out_dir.mkdir(parents=True, exist_ok=True)

    ct_nii = out_dir / "ct_volume.nii.gz"
    mask_nii = out_dir / "metal_mask.nii.gz"
    stats_path = out_dir / "stats.json"

    write_image_like(volume.astype(np.int16), template, ct_nii)
    write_image_like(mask.astype(np.uint8), template, mask_nii)

    outputs = {
        "ct_volume_nii": str(ct_nii),
        "metal_mask_nii": str(mask_nii),
        "stats": str(stats_path),
    }
    if save_npy:
        ct_npy = out_dir / "ct_volume.npy"
        mask_npy = out_dir / "metal_mask.npy"
        np.save(ct_npy, volume)
        np.save(mask_npy, mask.astype(np.uint8))
        outputs["ct_volume_npy"] = str(ct_npy)
        outputs["metal_mask_npy"] = str(mask_npy)

    record = {
        "input_folder": str(folder),
        "series_id": series_id,
        "dicom_files": len(files),
        "outputs": outputs,
        "stats": stats,
    }
    stats_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch-generate CT metal artifact masks for dataset DICOM series.")
    parser.add_argument("--dataset", type=Path, default=ROOT / "dataset", help="dataset root containing DICOM folders")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "output", help="paired output root")
    parser.add_argument("--threshold-low", type=float, default=800.0)
    parser.add_argument("--threshold-high", type=float, default=4000.0)
    parser.add_argument("--gradient-threshold", type=float, default=120.0)
    parser.add_argument("--opening-radius", type=int, default=1)
    parser.add_argument("--closing-radius", type=int, default=2)
    parser.add_argument("--min-component-size", type=int, default=50)
    parser.add_argument("--limit", type=int, default=0, help="process only the first N series; 0 means all")
    parser.add_argument("--save-npy", action="store_true", help="also save uncompressed .npy pairs")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if sitk is None:
        raise SystemExit("SimpleITK is not installed; cannot read DICOM data.")
    if not args.dataset.exists():
        raise SystemExit(f"dataset not found: {args.dataset}")

    params = {
        "threshold_low": args.threshold_low,
        "threshold_high": args.threshold_high,
        "gradient_threshold": args.gradient_threshold,
        "opening_radius": args.opening_radius,
        "closing_radius": args.closing_radius,
        "min_component_size": args.min_component_size,
    }

    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "dataset": str(args.dataset),
        "output": str(args.output),
        "parameters": params,
        "items": [],
        "errors": [],
    }

    processed = 0
    for folder in find_dicom_folders(args.dataset):
        series_ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(str(folder)) or []
        for series_id in series_ids:
            if args.limit and processed >= args.limit:
                break
            try:
                record = process_series(folder, series_id, args.output, params, args.save_npy)
                manifest["items"].append(record)
                processed += 1
                print(f"[ok] {processed}: {folder} -> final_voxels={record['stats']['final_voxels']}")
            except Exception as exc:
                error = {"folder": str(folder), "series_id": series_id, "error": repr(exc)}
                manifest["errors"].append(error)
                print(f"[error] {folder}: {exc}")
        if args.limit and processed >= args.limit:
            break

    manifest_path = args.output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"processed={processed} errors={len(manifest['errors'])} manifest={manifest_path}")


if __name__ == "__main__":
    main()
