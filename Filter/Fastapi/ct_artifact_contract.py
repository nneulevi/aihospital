"""Shared API contract helpers for CT artifact detection services."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

import numpy as np
import SimpleITK as sitk
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


API_PREFIX = "/api/ct-artifact"
ALLOWED_OUTPUT_FILES = {
    "mask.nii.gz",
    "corrected_ct.nii.gz",
    "result.json",
    "preview_axial.png",
    "preview_coronal.png",
    "preview_sagittal.png",
}


class ApiErrorCode:
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    INVALID_RESULT_FILE = "INVALID_RESULT_FILE"
    RESULT_NOT_FOUND = "RESULT_NOT_FOUND"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    INFERENCE_FAILED = "INFERENCE_FAILED"


def api_error(status_code: int, error_code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "status": "failed",
            "error_code": error_code,
            "message": message,
        },
    )


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error_code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "failed",
            "error_code": f"HTTP_{exc.status_code}",
            "message": str(exc.detail),
        },
    )


def validate_request_id(request_id: str) -> str:
    if not re.fullmatch(r"[0-9A-Za-z._-]+", request_id):
        raise api_error(400, ApiErrorCode.INVALID_RESULT_FILE, "非法 request_id")
    return request_id


def resolve_output_file(output_root: Path, request_id: str, file_name: str) -> Path:
    validate_request_id(request_id)
    clean_name = Path(file_name).name
    if clean_name != file_name or clean_name not in ALLOWED_OUTPUT_FILES:
        raise api_error(400, ApiErrorCode.INVALID_RESULT_FILE, "非法结果文件名")
    path = (output_root / request_id / clean_name).resolve()
    root = output_root.resolve()
    if root not in path.parents:
        raise api_error(400, ApiErrorCode.INVALID_RESULT_FILE, "非法结果路径")
    if not path.exists():
        raise api_error(404, ApiErrorCode.RESULT_NOT_FOUND, "结果文件不存在")
    return path


def find_file_by_name(output_root: Path, file_name: str) -> Path:
    clean_name = Path(file_name).name
    if clean_name != file_name:
        raise api_error(400, ApiErrorCode.INVALID_RESULT_FILE, "非法结果文件名")
    matches = list(output_root.glob(f"*/{clean_name}"))
    if not matches:
        raise api_error(404, ApiErrorCode.RESULT_NOT_FOUND, "结果文件不存在")
    return matches[-1]


def severity_from_ratio(ratio: float, positive_voxels: int) -> str:
    if positive_voxels <= 0 or ratio <= 0:
        return "none"
    if ratio < 0.005:
        return "mild"
    if ratio < 0.03:
        return "moderate"
    return "severe"


def report_suggestion(severity: str) -> str:
    suggestions = {
        "none": "未检测到明显金属伪影，建议结合原始 CT 继续常规阅片。",
        "mild": "存在轻度金属伪影，通常对整体阅片影响有限，建议关注邻近区域。",
        "moderate": "存在中度金属伪影，可能影响邻近区域判断，建议医生结合原始影像复核。",
        "severe": "存在重度金属伪影，可能明显影响局部结构判断，建议医生重点复核并谨慎使用自动结果。",
    }
    return suggestions.get(severity, suggestions["moderate"])


def affected_axial_slices(mask_array: np.ndarray) -> list[int]:
    if mask_array.ndim == 2:
        return [0] if np.any(mask_array > 0) else []
    z_positive = np.any(mask_array > 0, axis=(1, 2))
    return [int(index) for index in np.where(z_positive)[0]]


def _normalise_ct_slice(image: np.ndarray) -> np.ndarray:
    image = image.astype(np.float32, copy=False)
    finite = image[np.isfinite(image)]
    if finite.size == 0:
        return np.zeros(image.shape, dtype=np.uint8)
    low, high = np.percentile(finite, [1, 99])
    if high <= low:
        low, high = float(finite.min()), float(finite.max())
    if high <= low:
        return np.zeros(image.shape, dtype=np.uint8)
    clipped = np.clip(image, low, high)
    return ((clipped - low) / (high - low) * 255.0).astype(np.uint8)


def _overlay_slice(ct_slice: np.ndarray, mask_slice: np.ndarray) -> np.ndarray:
    gray = _normalise_ct_slice(ct_slice)
    rgb = np.repeat(gray[..., None], 3, axis=2)
    mask = mask_slice > 0
    if np.any(mask):
        rgb[mask, 0] = 255
        rgb[mask, 1] = (rgb[mask, 1] * 0.35).astype(np.uint8)
        rgb[mask, 2] = (rgb[mask, 2] * 0.35).astype(np.uint8)
    return rgb


def _best_index(mask_array: np.ndarray, axis: int) -> int:
    if mask_array.size == 0:
        return 0
    axes = tuple(i for i in range(mask_array.ndim) if i != axis)
    positive = np.where(np.sum(mask_array > 0, axis=axes) > 0)[0]
    if positive.size:
        return int(positive[len(positive) // 2])
    return int(mask_array.shape[axis] // 2)


def write_preview_images(ct_array: np.ndarray, mask_array: np.ndarray, output_dir: Path) -> dict[str, str]:
    if ct_array.ndim == 2:
        ct_array = ct_array[None, :, :]
    if mask_array.ndim == 2:
        mask_array = mask_array[None, :, :]

    z = _best_index(mask_array, 0)
    y = _best_index(mask_array, 1)
    x = _best_index(mask_array, 2)
    planes = {
        "axial": (ct_array[z, :, :], mask_array[z, :, :], "preview_axial.png"),
        "coronal": (ct_array[:, y, :], mask_array[:, y, :], "preview_coronal.png"),
        "sagittal": (ct_array[:, :, x], mask_array[:, :, x], "preview_sagittal.png"),
    }
    preview_files: dict[str, str] = {}
    for plane, (ct_slice, mask_slice, file_name) in planes.items():
        rgb = _overlay_slice(ct_slice, mask_slice)
        image = sitk.GetImageFromArray(rgb, isVector=True)
        sitk.WriteImage(image, str(output_dir / file_name))
        preview_files[plane] = file_name
    return preview_files


def build_detection_result(
    *,
    request_id: str,
    task_id: Optional[str] = None,
    backend: str,
    model_name: str,
    model_version: str,
    model_weight_path: Path,
    threshold: float,
    elapsed_ms: int,
    original_file: str,
    upload_path: Path,
    output_dir: Path,
    sitk_ct: sitk.Image,
    sitk_mask: sitk.Image,
    mask_array: np.ndarray,
    extra_input_metadata: Optional[dict[str, Any]] = None,
    artifact_reduction: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    ct_array = sitk.GetArrayFromImage(sitk_ct)
    positive_voxels = int(np.sum(mask_array > 0))
    total_voxels = int(mask_array.size)
    artifact_ratio = float(positive_voxels / max(total_voxels, 1))
    severity = severity_from_ratio(artifact_ratio, positive_voxels)
    preview_files = write_preview_images(ct_array, mask_array, output_dir)

    input_metadata: dict[str, Any] = {
        "original_file": original_file,
        "content_type": "application/octet-stream",
        "file_size_bytes": upload_path.stat().st_size if upload_path.exists() else None,
        "image_size_xyz": list(sitk_ct.GetSize()),
        "array_shape_zyx": list(ct_array.shape),
        "spacing": list(sitk_ct.GetSpacing()),
        "origin": list(sitk_ct.GetOrigin()),
        "direction": list(sitk_ct.GetDirection()),
    }
    if extra_input_metadata:
        input_metadata.update(extra_input_metadata)

    mask_url = f"{API_PREFIX}/files/{request_id}/mask.nii.gz"
    result_url = f"{API_PREFIX}/results/{request_id}"
    artifact_segmentation = {
        "backend": backend,
        "model_name": model_name,
        "model_version": model_version,
        "mask_file": "mask.nii.gz",
        "mask_url": mask_url,
        "artifact_detected": positive_voxels > 0,
        "artifact_ratio": artifact_ratio,
        "positive_voxels": positive_voxels,
        "affected_slices": affected_axial_slices(mask_array),
        "severity": severity,
        "threshold": threshold,
    }
    if artifact_reduction is None:
        artifact_reduction = {
            "enabled": False,
            "registered": False,
            "executable": False,
            "model_name": None,
            "task_type": None,
            "checkpoint_path": None,
            "checkpoint_exists": False,
            "correction_status": "not_configured",
            "corrected_ct_file": None,
            "corrected_ct_url": None,
            "use_for_lesion_input": False,
            "execution_blockers": [],
            "warning": "未配置金属伪影校正模型，本次病灶识别使用原始 CT。",
        }

    result = {
        "request_id": request_id,
        "task_id": task_id or request_id,
        "status": "success",
        "message": "CT金属伪影检测完成",
        "error_code": None,
        "module": "ct_artifact_filter",
        "backend": backend,
        "model_name": model_name,
        "model_version": model_version,
        "model_weight": Path(model_weight_path).name,
        "model_weight_path": str(Path(model_weight_path).resolve()),
        "artifact_detected": positive_voxels > 0,
        "artifact_ratio": artifact_ratio,
        "positive_voxels": positive_voxels,
        "affected_slices": affected_axial_slices(mask_array),
        "severity": severity,
        "threshold": threshold,
        "shape": list(sitk_mask.GetSize()),
        "array_shape_zyx": list(mask_array.shape),
        "spacing": list(sitk_ct.GetSpacing()),
        "origin": list(sitk_ct.GetOrigin()),
        "direction": list(sitk_ct.GetDirection()),
        "mask_file": "mask.nii.gz",
        "mask_save_path": str((output_dir / "mask.nii.gz").resolve()),
        "download_url": mask_url,
        "result_url": result_url,
        "preview_files": preview_files,
        "preview_urls": {
            plane: f"{API_PREFIX}/files/{request_id}/{file_name}" for plane, file_name in preview_files.items()
        },
        "artifact_segmentation": artifact_segmentation,
        "artifact_reduction": artifact_reduction,
        "report_suggestion": report_suggestion(severity),
        "elapsed_ms": elapsed_ms,
        "input_metadata": input_metadata,
    }
    (output_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
