"""Direct ICHSeg nnU-Net checkpoint inference for one NIfTI volume."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import numpy as np
import SimpleITK as sitk
import torch
import torch.nn.functional as F
from PIL import Image

from nnunetv2.utilities.get_network_from_plans import get_network_from_plans
from nnunetv2.utilities.label_handling.label_handling import determine_num_input_channels
from nnunetv2.utilities.plans_handling.plans_handler import PlansManager


def _resolve_device(device_arg: str) -> torch.device:
    if device_arg == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(device_arg)


def _load_checkpoint(path: Path) -> dict[str, Any]:
    try:
        return torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        return torch.load(path, map_location="cpu")


@lru_cache(maxsize=2)
def _load_network(checkpoint_path: str, plans_path: str, device_arg: str):
    checkpoint = _load_checkpoint(Path(checkpoint_path))
    plans = checkpoint.get("init_args", {}).get("plans")
    if not plans:
        import json

        plans = json.loads(Path(plans_path).read_text(encoding="utf-8"))
    dataset_json = checkpoint.get("init_args", {}).get("dataset_json") or {
        "channel_names": {"0": "CT"},
        "labels": {"background": 0, "ICH": 1},
        "file_ending": ".nii.gz",
    }
    configuration_name = checkpoint.get("init_args", {}).get("configuration") or "3d_fullres"
    plans_manager = PlansManager(plans)
    configuration_manager = plans_manager.get_configuration(configuration_name)
    input_channels = determine_num_input_channels(plans_manager, configuration_manager, dataset_json)
    output_channels = plans_manager.get_label_manager(dataset_json).num_segmentation_heads
    network = get_network_from_plans(
        configuration_manager.network_arch_class_name,
        configuration_manager.network_arch_init_kwargs,
        configuration_manager.network_arch_init_kwargs_req_import,
        input_channels,
        output_channels,
        allow_init=False,
        deep_supervision=False,
    )
    missing, unexpected = network.load_state_dict(checkpoint["network_weights"], strict=False)
    unexpected = [key for key in unexpected if not key.startswith(("head1.", "head2.", "head3."))]
    if missing or unexpected:
        raise RuntimeError(f"ICHSeg checkpoint load mismatch: missing={missing}, unexpected={unexpected}")
    device = _resolve_device(device_arg)
    network.to(device)
    network.eval()
    metadata = {
        "trainer_name": checkpoint.get("trainer_name"),
        "configuration": configuration_name,
        "inference_allowed_mirroring_axes": checkpoint.get("inference_allowed_mirroring_axes"),
        "device": str(device),
    }
    return network, metadata


def _normalize_ct(array: np.ndarray) -> np.ndarray:
    clipped = np.clip(array.astype(np.float32), 21.0, 78.0)
    return (clipped - 47.09904479980469) / 32.34728240966797


def _resize_tensor(array: np.ndarray, target_shape: tuple[int, int, int]) -> torch.Tensor:
    tensor = torch.from_numpy(array[None, None, ...].astype(np.float32))
    return F.interpolate(tensor, size=target_shape, mode="trilinear", align_corners=False)


def _bbox_from_mask(mask: np.ndarray) -> list[int]:
    positions = np.argwhere(mask > 0)
    if positions.size == 0:
        return []
    z0, y0, x0 = positions.min(axis=0).tolist()
    z1, y1, x1 = positions.max(axis=0).tolist()
    return [int(x0), int(y0), int(z0), int(x1), int(y1), int(z1)]


def _affected_slices(mask: np.ndarray, limit: int = 24) -> list[int]:
    slices = np.where(mask.reshape(mask.shape[0], -1).sum(axis=1) > 0)[0].astype(int).tolist()
    if len(slices) <= limit:
        return slices
    step = max(1, len(slices) // limit)
    return slices[::step][:limit]


def _write_mask(mask: np.ndarray, reference_image: sitk.Image, path: Path) -> None:
    mask_image = sitk.GetImageFromArray(mask.astype(np.uint8))
    mask_image.CopyInformation(reference_image)
    sitk.WriteImage(mask_image, str(path))


def _window_to_uint8(slice_array: np.ndarray) -> np.ndarray:
    arr = np.clip(slice_array.astype(np.float32), -100.0, 200.0)
    arr = (arr + 100.0) / 300.0
    return (arr * 255.0).clip(0, 255).astype(np.uint8)


def _overlay(gray: np.ndarray, mask: np.ndarray) -> Image.Image:
    rgb = np.stack([gray, gray, gray], axis=-1)
    if mask.any():
        rgb[mask > 0, 0] = 255
        rgb[mask > 0, 1] = (rgb[mask > 0, 1] * 0.35).astype(np.uint8)
        rgb[mask > 0, 2] = (rgb[mask > 0, 2] * 0.35).astype(np.uint8)
    return Image.fromarray(rgb)


def _middle_positive_or_center(mask: np.ndarray, axis: int) -> int:
    projection_axes = tuple(i for i in range(mask.ndim) if i != axis)
    positives = np.where(mask.sum(axis=projection_axes) > 0)[0]
    if len(positives):
        return int(positives[len(positives) // 2])
    return int(mask.shape[axis] // 2)


def _write_previews(image: np.ndarray, mask: np.ndarray, output_dir: Path, url_prefix: str) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    z = _middle_positive_or_center(mask, 0)
    y = _middle_positive_or_center(mask, 1)
    x = _middle_positive_or_center(mask, 2)
    previews = {
        "axial": (_window_to_uint8(image[z]), mask[z], "lesion_preview_axial.png"),
        "coronal": (_window_to_uint8(image[:, y, :]), mask[:, y, :], "lesion_preview_coronal.png"),
        "sagittal": (_window_to_uint8(image[:, :, x]), mask[:, :, x], "lesion_preview_sagittal.png"),
    }
    urls: dict[str, str] = {}
    for key, (gray, mask_slice, filename) in previews.items():
        _overlay(gray, mask_slice).save(output_dir / filename)
        urls[key] = f"{url_prefix}/{filename}"
    return urls


def predict_ichseg_nnunet(
    *,
    nifti_path: Path,
    checkpoint_path: Path,
    plans_path: Path,
    output_dir: Path,
    url_prefix: str,
    device: str = "auto",
    inference_shape: tuple[int, int, int] = (16, 192, 192),
    threshold: float = 0.5,
    quality_context: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    if len(inference_shape) != 3:
        raise ValueError("ICHSEG_INFERENCE_SHAPE must contain three integers: z,y,x")
    image = sitk.ReadImage(str(nifti_path))
    array = sitk.GetArrayFromImage(image).astype(np.float32)
    normalized = _normalize_ct(array)
    input_tensor = _resize_tensor(normalized, inference_shape)
    network, metadata = _load_network(str(checkpoint_path), str(plans_path), device)
    resolved_device = torch.device(metadata["device"])
    with torch.no_grad():
        logits = network(input_tensor.to(resolved_device))
        if isinstance(logits, (list, tuple)):
            logits = logits[0]
        probabilities = torch.softmax(logits, dim=1)[:, 1:2]
        probabilities = F.interpolate(probabilities.cpu(), size=array.shape, mode="trilinear", align_corners=False)
    prob_array = probabilities.numpy()[0, 0]
    mask = (prob_array >= threshold).astype(np.uint8)
    output_dir.mkdir(parents=True, exist_ok=True)
    mask_path = output_dir / "lesion_mask.nii.gz"
    _write_mask(mask, image, mask_path)
    preview_urls = _write_previews(array, mask, output_dir, url_prefix)
    positive_voxels = int(mask.sum())
    total_voxels = int(mask.size)
    max_probability = float(prob_array.max()) if prob_array.size else 0.0
    detected = positive_voxels > 0
    warnings = []
    severity = str((quality_context or {}).get("severity") or "none")
    if severity not in {"none", "normal"}:
        warnings.append("伪影可能影响病灶分割边界，建议医生结合原始影像复核。")
    return {
        "lesion_type": "intracranial_hemorrhage",
        "display_name": "颅内出血",
        "detected": detected,
        "confidence": max_probability,
        "decision_threshold": threshold,
        "severity": "suspected" if detected else "none",
        "affected_slices": _affected_slices(mask),
        "locations": [],
        "bbox": _bbox_from_mask(mask),
        "mask_url": f"{url_prefix}/lesion_mask.nii.gz",
        "preview_urls": preview_urls,
        "model_name": "ichseg_rank_nnunet",
        "model_version": "ichseg-nnunetv2-fold0",
        "provider": "ichseg_rank_nnunet",
        "task_type": "intracranial_hemorrhage_segmentation",
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_provenance": "mature_public_external",
        "checkpoint_fallback_used": False,
        "runtime_status": "executed_direct_network_forward",
        "inference_shape": list(inference_shape),
        "positive_voxel_count": positive_voxels,
        "positive_voxel_ratio": positive_voxels / total_voxels if total_voxels else 0.0,
        "reliability": "segmentation_mask_available",
        "warnings": warnings,
        "report_suggestion": (
            "ICHSeg 分割提示存在疑似颅内出血区域，请医生结合红色叠加预览、原始窗宽窗位和相邻层面复核。"
            if detected
            else "ICHSeg 分割未提示明确颅内出血区域，阴性结果仍需结合原始影像和临床表现复核。"
        ),
        "nnunet_metadata": metadata,
    }
