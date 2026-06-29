"""DICOM/RSNA upload normalization for the Head CT orchestrator."""

from __future__ import annotations

import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class DicomIngestError(RuntimeError):
    """Raised when an uploaded DICOM object cannot be normalized."""


@dataclass(frozen=True)
class NormalizedCtInput:
    original_filename: str
    original_format: str
    source_path: Path
    input_path: Path
    input_filename: str
    content_type: Optional[str]
    metadata: dict[str, object]


def is_nifti_file(filename: str) -> bool:
    return filename.lower().endswith((".nii", ".nii.gz"))


def is_dicom_file(filename: str) -> bool:
    lower = filename.lower()
    name = Path(lower).name
    return bool(name) and (lower.endswith((".dcm", ".dicom")) or "." not in name)


def is_dicom_zip_file(filename: str) -> bool:
    return filename.lower().endswith(".zip")


def is_supported_ct_upload(filename: str) -> bool:
    return is_nifti_file(filename) or is_dicom_file(filename) or is_dicom_zip_file(filename)


def strip_medical_suffix(filename: str) -> str:
    lower = filename.lower()
    for suffix in (".nii.gz", ".nii", ".dicom", ".dcm", ".zip"):
        if lower.endswith(suffix):
            return filename[: -len(suffix)]
    return Path(filename).stem


def safe_original_name(filename: Optional[str]) -> str:
    name = Path(filename or "ct.nii.gz").name
    lower = name.lower()
    if lower.endswith(".nii.gz"):
        suffix = ".nii.gz"
    else:
        suffix = Path(name).suffix
    stem = strip_medical_suffix(name)
    safe = "".join(char if char.isalnum() or char in "._-" else "_" for char in stem).strip("._-") or "ct"
    return f"{safe}{suffix}"


def task_input_name(filename: str) -> str:
    return "input.nii.gz" if filename.lower().endswith(".nii.gz") else "input.nii"


def save_upload_stream(source, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as dst:
        shutil.copyfileobj(source, dst)


def _require_sitk():
    try:
        import SimpleITK as sitk  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on optional runtime dependency.
        raise DicomIngestError("DICOM 接入需要安装 SimpleITK。") from exc
    return sitk


def _read_dicom_series_from_dir(directory: Path):
    sitk = _require_sitk()
    reader = sitk.ImageSeriesReader()
    candidates: list[tuple[int, str, list[str], Path]] = []
    for folder in [directory] + [path for path in directory.rglob("*") if path.is_dir()]:
        try:
            series_ids = reader.GetGDCMSeriesIDs(str(folder)) or []
        except Exception:
            continue
        for series_id in series_ids:
            names = list(reader.GetGDCMSeriesFileNames(str(folder), series_id))
            if names:
                candidates.append((len(names), series_id, names, folder))
    if not candidates:
        raise DicomIngestError("未在上传内容中识别到可读取的 DICOM Series。")
    _, series_id, names, folder = max(candidates, key=lambda item: item[0])
    reader.SetFileNames(names)
    image = reader.Execute()
    return image, {
        "dicom_series_id": series_id,
        "dicom_series_dir": str(folder),
        "dicom_file_count": len(names),
    }


def _extract_zip_safely(zip_path: Path, extract_dir: Path) -> int:
    extract_dir.mkdir(parents=True, exist_ok=True)
    root = extract_dir.resolve()
    count = 0
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            target = (extract_dir / member.filename).resolve()
            if root not in target.parents:
                raise DicomIngestError("DICOM ZIP 包含非法路径。")
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            count += 1
    if count == 0:
        raise DicomIngestError("DICOM ZIP 中没有可读取文件。")
    return count


def convert_dicom_file_to_nifti(dicom_path: Path, output_path: Path) -> dict[str, object]:
    sitk = _require_sitk()
    image = sitk.ReadImage(str(dicom_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sitk.WriteImage(image, str(output_path))
    return {
        "normalization": "dicom_file_to_nifti",
        "dicom_file_count": 1,
        "image_size_xyz": list(image.GetSize()),
        "spacing": list(image.GetSpacing()),
    }


def convert_dicom_zip_to_nifti(zip_path: Path, extract_dir: Path, output_path: Path) -> dict[str, object]:
    sitk = _require_sitk()
    extracted_files = _extract_zip_safely(zip_path, extract_dir)
    image, series_metadata = _read_dicom_series_from_dir(extract_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sitk.WriteImage(image, str(output_path))
    return {
        "normalization": "dicom_zip_to_nifti",
        "zip_file_count": extracted_files,
        "image_size_xyz": list(image.GetSize()),
        "spacing": list(image.GetSpacing()),
        **series_metadata,
    }


def normalize_saved_upload(original_filename: str, source_path: Path, output_dir: Path, content_type: Optional[str]) -> NormalizedCtInput:
    source_dir = output_dir / "source"
    if is_nifti_file(original_filename):
        input_filename = task_input_name(original_filename)
        input_path = output_dir / input_filename
        if source_path.resolve() != input_path.resolve():
            shutil.copyfile(source_path, input_path)
        metadata: dict[str, object] = {"normalization": "none", "source_format": "nifti"}
        original_format = "nifti"
    elif is_dicom_zip_file(original_filename):
        input_filename = "input.nii.gz"
        input_path = output_dir / input_filename
        metadata = convert_dicom_zip_to_nifti(source_path, source_dir / "dicom_zip", input_path)
        metadata["source_format"] = "dicom_zip"
        original_format = "dicom_zip"
    elif is_dicom_file(original_filename):
        input_filename = "input.nii.gz"
        input_path = output_dir / input_filename
        metadata = convert_dicom_file_to_nifti(source_path, input_path)
        metadata["source_format"] = "dicom_file"
        original_format = "dicom_file"
    else:
        raise DicomIngestError("不支持的 CT 上传格式。")
    return NormalizedCtInput(
        original_filename=original_filename,
        original_format=original_format,
        source_path=source_path,
        input_path=input_path,
        input_filename=input_filename,
        content_type=content_type,
        metadata=metadata,
    )
