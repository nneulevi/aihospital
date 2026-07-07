"""Single-case inference for the hemorrhage classifier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Optional

import torch

try:
    from .calibration import calibrated_suggestion_prefix, confidence_band, load_probability_calibration
    from .config import DISPLAY_NAME, INPUT_SHAPE, LESION_TYPE, MODEL_NAME, MODEL_VERSION, THRESHOLD, WINDOW_MAX, WINDOW_MIN
    from .dataset import preprocess_nifti
    from .monai_pipeline import build_monai_classifier
    from .model import Hemorrhage3DCNN
    from .vinbigdata_cnn_lstm import predict_vinbigdata_probabilities
except ImportError:  # pragma: no cover - direct script fallback.
    from calibration import calibrated_suggestion_prefix, confidence_band, load_probability_calibration
    from config import DISPLAY_NAME, INPUT_SHAPE, LESION_TYPE, MODEL_NAME, MODEL_VERSION, THRESHOLD, WINDOW_MAX, WINDOW_MIN
    from dataset import preprocess_nifti
    from monai_pipeline import build_monai_classifier
    from model import Hemorrhage3DCNN
    from vinbigdata_cnn_lstm import predict_vinbigdata_probabilities


def resolve_device(device_arg: str) -> torch.device:
    if device_arg == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(device_arg)


def load_checkpoint(checkpoint_path: Path, device: torch.device) -> tuple[Hemorrhage3DCNN, dict[str, Any]]:
    try:
        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    except TypeError:
        checkpoint = torch.load(checkpoint_path, map_location=device)
    if checkpoint.get("framework") == "monai":
        model = build_monai_classifier(str(checkpoint.get("network", "densenet121")))
    else:
        model = Hemorrhage3DCNN(
            base_channels=int(checkpoint.get("base_channels", 16)),
            dropout=float(checkpoint.get("dropout", 0.2)),
        )
    model.load_state_dict(checkpoint["model_state"])
    model.to(device)
    model.eval()
    return model, checkpoint


def reliability_from_quality(quality_context: Optional[dict[str, Any]]) -> tuple[str, list[str]]:
    severity = str((quality_context or {}).get("severity") or "none")
    if severity == "none":
        return "normal", []
    if severity == "mild":
        return "slightly_limited_by_artifact", ["存在轻度金属伪影，建议结合原始影像复核。"]
    if severity == "moderate":
        return "limited_by_artifact", ["存在中度金属伪影，受影响层面附近结果需谨慎解释。"]
    return "strongly_limited_by_artifact", ["存在重度金属伪影，病灶识别结果可信度可能明显受限。"]


def result_from_probability(
    probability: float,
    threshold: float,
    quality_context: Optional[dict[str, Any]] = None,
    *,
    calibration_path: Optional[Path] = None,
) -> dict[str, Any]:
    calibration = load_probability_calibration(calibration_path, default_threshold=threshold)
    threshold = float(calibration["threshold"])
    band = confidence_band(probability, threshold, float(calibration["uncertainty_margin"]))
    detected = probability >= threshold
    reliability, warnings = reliability_from_quality(quality_context)
    if detected:
        suggestion = f"{calibrated_suggestion_prefix(band)}：疑似颅内出血，请医生结合原始影像复核。"
        severity = "suspected"
    else:
        suggestion = f"{calibrated_suggestion_prefix(band)}：未见明确颅内出血征象，建议医生结合原始影像复核。"
        severity = "none"
    if band.startswith("borderline"):
        suggestion += " 当前概率接近阈值，建议重点复核脑实质、脑沟脑池及硬膜下/蛛网膜下腔高密度影。"
    return {
        "lesion_type": LESION_TYPE,
        "display_name": DISPLAY_NAME,
        "detected": detected,
        "confidence": probability,
        "decision_threshold": threshold,
        "confidence_band": band,
        "calibration": calibration,
        "severity": severity,
        "affected_slices": [],
        "locations": [],
        "bbox": [],
        "mask_url": None,
        "preview_urls": {},
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "reliability": reliability,
        "warnings": warnings,
        "report_suggestion": suggestion,
    }


def predict_hemorrhage(
    nifti_path: Path,
    checkpoint_path: Path,
    device: str = "auto",
    quality_context: Optional[dict[str, Any]] = None,
    calibration_path: Optional[Path] = None,
) -> dict[str, Any]:
    resolved_device = resolve_device(device)
    model, checkpoint = load_checkpoint(checkpoint_path, resolved_device)
    input_shape = tuple(checkpoint.get("input_shape", INPUT_SHAPE))
    image = preprocess_nifti(nifti_path, input_shape, WINDOW_MIN, WINDOW_MAX)
    with torch.no_grad():
        logits = model(image[None, ...].to(resolved_device))
        probability = float(torch.sigmoid(logits).cpu().numpy().reshape(-1)[0])
    threshold = float(checkpoint.get("threshold", THRESHOLD))
    return result_from_probability(probability, threshold, quality_context, calibration_path=calibration_path)


def predict_vinbigdata_hemorrhage(
    nifti_path: Path,
    checkpoint_path: Path,
    device: str = "auto",
    quality_context: Optional[dict[str, Any]] = None,
    threshold: float = THRESHOLD,
    image_size: int = 512,
    max_slices: int = 64,
    sampling_offsets: tuple[float, ...] = (0.0,),
    tta_flip: bool = False,
    calibration_path: Optional[Path] = None,
) -> dict[str, Any]:
    probabilities, load_info = predict_vinbigdata_probabilities(
        nifti_path,
        checkpoint_path,
        device=device,
        image_size=image_size,
        max_slices=max_slices,
        sampling_offsets=sampling_offsets,
        tta_flip=tta_flip,
    )
    probability = float(probabilities.get("any", max(probabilities.values(), default=0.0)))
    result = result_from_probability(probability, threshold, quality_context, calibration_path=calibration_path)
    result.update(
        {
            "model_name": "vinbigdata_midl2020_cnn_lstm_ich",
            "model_version": "midl2020-rsna",
            "provider": "vinbigdata",
            "subtype_probabilities": probabilities,
            "checkpoint_framework": load_info.framework,
            "checkpoint_missing_keys": load_info.missing_keys[:20],
            "checkpoint_unexpected_keys": load_info.unexpected_keys[:20],
            "inference_strategy": load_info.inference_strategy or {},
        }
    )
    return result


def parse_float_csv(text: str) -> tuple[float, ...]:
    values = []
    for item in text.split(","):
        item = item.strip()
        if item:
            values.append(float(item))
    return tuple(values) or (0.0,)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run hemorrhage classifier inference on one NIfTI.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--provider", choices=["local", "vinbigdata"], default="local")
    parser.add_argument("--vinbigdata-tta-flip", action="store_true", help="average original and horizontally flipped inference")
    parser.add_argument("--vinbigdata-sampling-offsets", default="0", help="comma-separated slice sampling offsets, e.g. -0.25,0,0.25")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.provider == "vinbigdata":
        result = predict_vinbigdata_hemorrhage(
            args.input,
            args.checkpoint,
            args.device,
            sampling_offsets=parse_float_csv(args.vinbigdata_sampling_offsets),
            tta_flip=args.vinbigdata_tta_flip,
        )
    else:
        result = predict_hemorrhage(args.input, args.checkpoint, args.device)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
