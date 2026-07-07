from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def file_info(path: Path) -> dict[str, Any]:
    exists = path.exists()
    return {
        "path": str(path),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else 0,
    }


def choose_checkpoint(candidates: list[tuple[str, Path]]) -> dict[str, Any]:
    for provenance, path in candidates:
        if path.exists():
            return {
                "selected_path": str(path),
                "selected_provenance": provenance,
                "selected_exists": True,
                "fallback_used": provenance == "smoke_fallback",
                "formal_weight_ready": provenance != "smoke_fallback",
            }
    provenance, path = candidates[-1]
    return {
        "selected_path": str(path),
        "selected_provenance": provenance,
        "selected_exists": path.exists(),
        "fallback_used": True,
        "formal_weight_ready": False,
    }


def build_report() -> dict[str, Any]:
    filter_mature = ROOT / "Filter" / "model" / "external_weights" / "metal_artifact_segmentation" / "mature_metal_artifact_unet3d.pt"
    filter_mar_mature = ROOT / "Filter" / "model" / "external_weights" / "metal_artifact_reduction" / "InDuDoNet_latest.pt"
    filter_local = ROOT / "Filter" / "model" / "runs" / "metal_unet3d" / "best_unet3d_metal.pt"
    filter_smoke = ROOT / "Filter" / "model" / "runs" / "config_visual_smoke" / "best_unet3d_metal.pt"

    vinbig_dir = ROOT / "HeadCTLesionDetection" / "models" / "hemorrhage" / "external_weights"
    vinbig_scripted = vinbig_dir / "vinbigdata_midl2020_cnn_lstm.pt"
    vinbig_torchscript = vinbig_dir / "vinbigdata_midl2020_cnn_lstm.torchscript.pt"
    vinbig_raw = vinbig_dir / "best_resnet50.pth"
    lesion_local = ROOT / "HeadCTLesionDetection" / "models" / "hemorrhage" / "runs" / "hemorrhage_v1" / "best.pt"
    lesion_smoke = ROOT / "HeadCTLesionDetection" / "models" / "hemorrhage" / "runs" / "hemorrhage_v1" / "smoke_best.pt"
    ichseg_dir = vinbig_dir / "ichseg_rank_nnunet"
    ichseg_checkpoint = ichseg_dir / "fold_0" / "checkpoint_final.pth"
    ichseg_plans = ichseg_dir / "nnUNetPlans.json"
    ichseg_manifest = ichseg_dir / "manifest.json"

    segmentation_dataset_candidates = [
        ROOT / "HeadCTLesionDetection" / "datasets" / "physionet_ct_ich",
        ROOT / "HeadCTLesionDetection" / "datasets" / "instance2022",
    ]

    return {
        "policy": "mature_public_external > local_project_trained > smoke_fallback",
        "filter_metal_artifact_segmentation": {
            "task_type": "segmentation",
            "purpose": "metal_artifact_mask",
            "mature_model_reference": {
                "status": "not_found_as_public_direct_segmentation_checkpoint",
                "note": "InDuDoNet/DuDoNet/U-DuDoNet are metal artifact reduction or reconstruction models, not mask segmentation checkpoints.",
            },
            "selection": choose_checkpoint(
                [
                    ("mature_public_external", filter_mature),
                    ("local_project_trained", filter_local),
                    ("smoke_fallback", filter_smoke),
                ]
            ),
            "candidates": {
                "mature_public_external": file_info(filter_mature),
                "local_project_trained": file_info(filter_local),
                "smoke_fallback": file_info(filter_smoke),
            },
        },
        "filter_metal_artifact_reduction": {
            "task_type": "reduction",
            "purpose": "metal_artifact_reduction",
            "mature_model_reference": {
                "name": "InDuDoNet",
                "paper": "An Interpretable Dual Domain Network for CT Metal Artifact Reduction, MICCAI 2021",
                "code_url": "https://github.com/hongwang01/InDuDoNet",
                "weight_url": "https://github.com/hongwang01/InDuDoNet/blob/main/pretrained_model/InDuDoNet_latest.pt",
                "note": "This is a mature MAR checkpoint. It is registered for artifact reduction capability, but it is not used as a U-Net metal artifact mask segmentation checkpoint.",
            },
            "selection": choose_checkpoint(
                [
                    ("mature_public_external", filter_mar_mature),
                ]
            ),
            "candidates": {
                "mature_public_external": file_info(filter_mar_mature),
            },
        },
        "lesion_hemorrhage_classification": {
            "task_type": "classification",
            "purpose": "intracranial_hemorrhage_detection",
            "mature_model_reference": {
                "name": "VinBigData MIDL2020 CNN-LSTM ICH",
                "code_url": "https://github.com/vinbigdata-medical/midl2020-cnnlstm-ich",
                "weight_url": "https://www.kaggle.com/dattran2346/midl2020-cnn-lstm",
            },
            "selection": choose_checkpoint(
                [
                    ("mature_public_external", vinbig_scripted),
                    ("mature_public_external", vinbig_torchscript),
                    ("mature_public_external_raw", vinbig_raw),
                    ("local_project_trained", lesion_local),
                    ("smoke_fallback", lesion_smoke),
                ]
            ),
            "candidates": {
                "vinbigdata_scripted": file_info(vinbig_scripted),
                "vinbigdata_torchscript": file_info(vinbig_torchscript),
                "vinbigdata_raw_resnet50": file_info(vinbig_raw),
                "local_project_trained": file_info(lesion_local),
                "smoke_fallback": file_info(lesion_smoke),
            },
        },
        "lesion_hemorrhage_segmentation": {
            "task_type": "segmentation",
            "purpose": "intracranial_hemorrhage_mask",
            "mature_model_reference": {
                "name": "ICHSeg learning-to-rank nnU-Net variant",
                "paper": "Segmentation of Tiny Intracranial Hemorrhage via Learning-to-Rank Local Feature Enhancement, ISBI 2024",
                "code_url": "https://github.com/med-air/ICHSeg",
                "checkpoint_url": "SharePoint public folder linked by the ICHSeg README",
            },
            "selection": choose_checkpoint(
                [
                    ("mature_public_external", ichseg_checkpoint),
                ]
            ),
            "mature_checkpoint_ready": ichseg_checkpoint.exists() and ichseg_plans.exists(),
            "runtime_integration_status": "checkpoint_registered_not_yet_executed_by_lesion_service",
            "required_runtime": "nnU-Net v2 with nnUNetTrainer_rank",
            "candidates": {
                "ichseg_fold0_checkpoint": file_info(ichseg_checkpoint),
                "ichseg_plans": file_info(ichseg_plans),
                "ichseg_manifest": file_info(ichseg_manifest),
            },
            "recommended_public_datasets": [
                {
                    "name": "PhysioNet CT-ICH",
                    "url": "https://physionet.org/content/ct-ich/1.3.1/",
                },
                {
                    "name": "INSTANCE 2022 Intracranial Hemorrhage Segmentation Challenge",
                    "url": "https://instance.grand-challenge.org/",
                },
            ],
            "dataset_candidates": [file_info(path) for path in segmentation_dataset_candidates],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate mature checkpoint readiness and fallback selection.")
    parser.add_argument("--strict-mature", action="store_true", help="exit 2 if no mature public checkpoint is present")
    args = parser.parse_args()

    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.strict_mature:
        mature_ready = (
            report["filter_metal_artifact_segmentation"]["selection"]["selected_provenance"] == "mature_public_external"
            or report["filter_metal_artifact_reduction"]["selection"]["selected_provenance"] == "mature_public_external"
            or report["lesion_hemorrhage_classification"]["selection"]["selected_provenance"].startswith("mature_public_external")
        )
        if not mature_ready:
            raise SystemExit(2)


if __name__ == "__main__":
    main()
