"""Thin nnU-Net v2 command wrapper for hemorrhage segmentation experiments.

This module does not implement nnU-Net itself. It standardizes the project
paths and command invocation for:

- planning/preprocessing
- training
- prediction

Use this only after voxel-level hemorrhage masks are available and
``segmentation_prepare.py`` has created an nnU-Net-style dataset.
"""

from __future__ import annotations

import argparse
import os
import shutil
import site
import subprocess
import sys
import sysconfig
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parents[2]

DEFAULT_RAW = REPO_ROOT / "nnUNet_raw"
DEFAULT_PREPROCESSED = REPO_ROOT / "nnUNet_preprocessed"
DEFAULT_RESULTS = REPO_ROOT / "nnUNet_results"


def resolve_executable(name: str) -> Path:
    found = shutil.which(name)
    if found:
        return Path(found)

    suffix = ".exe" if os.name == "nt" else ""
    scripts_paths = {
        sysconfig.get_path("scripts"),
        sysconfig.get_path("scripts", scheme="nt_user" if os.name == "nt" else "posix_user"),
    }
    candidates = [Path(path) / f"{name}{suffix}" for path in scripts_paths if path]
    candidates.extend(
        [
            Path(sys.prefix) / "Scripts" / f"{name}{suffix}",
            Path(site.USER_BASE) / "Scripts" / f"{name}{suffix}",
            Path(site.USER_BASE) / "bin" / name,
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Cannot find nnU-Net command: {name}. Install nnunetv2 or add Scripts to PATH.")


def nnunet_env(args: argparse.Namespace) -> dict[str, str]:
    env = os.environ.copy()
    env["nnUNet_raw"] = str(args.raw_dir.resolve())
    env["nnUNet_preprocessed"] = str(args.preprocessed_dir.resolve())
    env["nnUNet_results"] = str(args.results_dir.resolve())
    return env


def ensure_work_dirs(args: argparse.Namespace) -> None:
    args.raw_dir.mkdir(parents=True, exist_ok=True)
    args.preprocessed_dir.mkdir(parents=True, exist_ok=True)
    args.results_dir.mkdir(parents=True, exist_ok=True)


def print_env(args: argparse.Namespace) -> None:
    print("PowerShell environment:")
    print(f'$env:nnUNet_raw="{args.raw_dir.resolve()}"')
    print(f'$env:nnUNet_preprocessed="{args.preprocessed_dir.resolve()}"')
    print(f'$env:nnUNet_results="{args.results_dir.resolve()}"')


def run_command(command: list[str], args: argparse.Namespace) -> int:
    ensure_work_dirs(args)
    print_env(args)
    print("Command:")
    print(" ".join(f'"{part}"' if " " in part else part for part in command))
    if args.dry_run:
        return 0
    completed = subprocess.run(command, env=nnunet_env(args), check=False)
    return completed.returncode


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW, help="nnUNet_raw directory")
    parser.add_argument("--preprocessed-dir", type=Path, default=DEFAULT_PREPROCESSED, help="nnUNet_preprocessed directory")
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS, help="nnUNet_results directory")
    parser.add_argument("--dry-run", action="store_true", help="Print command without running it")


def cmd_env(args: argparse.Namespace) -> int:
    ensure_work_dirs(args)
    print_env(args)
    print("Resolved commands:")
    for name in ["nnUNetv2_plan_and_preprocess", "nnUNetv2_train", "nnUNetv2_predict"]:
        print(f"{name}: {resolve_executable(name)}")
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    command = [
        str(resolve_executable("nnUNetv2_plan_and_preprocess")),
        "-d",
        *[str(dataset_id) for dataset_id in args.dataset_ids],
        "-npfp",
        str(args.fingerprint_processes),
        "-np",
        *[str(value) for value in args.preprocess_processes],
    ]
    if args.verify_dataset_integrity:
        command.append("--verify_dataset_integrity")
    if args.no_preprocess:
        command.append("--no_pp")
    if args.clean:
        command.append("--clean")
    if args.configurations:
        command.extend(["-c", *args.configurations])
    return run_command(command, args)


def cmd_train(args: argparse.Namespace) -> int:
    command = [
        str(resolve_executable("nnUNetv2_train")),
        str(args.dataset),
        args.configuration,
        str(args.fold),
        "-tr",
        args.trainer,
        "-p",
        args.plans,
        "-device",
        args.device,
    ]
    if args.num_gpus is not None:
        command.extend(["-num_gpus", str(args.num_gpus)])
    if args.pretrained_weights:
        command.extend(["-pretrained_weights", str(args.pretrained_weights)])
    if args.continue_training:
        command.append("--c")
    if args.validation_only:
        command.append("--val")
    if args.validation_best:
        command.append("--val_best")
    if args.disable_checkpointing:
        command.append("--disable_checkpointing")
    if args.use_compressed:
        command.append("--use_compressed")
    if args.npz:
        command.append("--npz")
    return run_command(command, args)


def cmd_predict(args: argparse.Namespace) -> int:
    command = [
        str(resolve_executable("nnUNetv2_predict")),
        "-i",
        str(args.input_dir),
        "-o",
        str(args.output_dir),
        "-d",
        str(args.dataset),
        "-c",
        args.configuration,
        "-p",
        args.plans,
        "-tr",
        args.trainer,
        "-chk",
        args.checkpoint,
        "-device",
        args.device,
    ]
    if args.folds:
        command.extend(["-f", *[str(fold) for fold in args.folds]])
    if args.disable_tta:
        command.append("--disable_tta")
    if args.save_probabilities:
        command.append("--save_probabilities")
    if args.continue_prediction:
        command.append("--continue_prediction")
    return run_command(command, args)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Project wrapper for nnU-Net v2 hemorrhage segmentation training.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    env_parser = subparsers.add_parser("env", help="Create work dirs and print required nnU-Net environment variables.")
    add_common_args(env_parser)
    env_parser.set_defaults(func=cmd_env)

    plan_parser = subparsers.add_parser("plan", help="Run nnUNetv2_plan_and_preprocess.")
    add_common_args(plan_parser)
    plan_parser.add_argument("-d", "--dataset-ids", nargs="+", required=True, help="Dataset IDs, for example 501.")
    plan_parser.add_argument("--fingerprint-processes", type=int, default=4)
    plan_parser.add_argument("--preprocess-processes", type=int, nargs="+", default=[4])
    plan_parser.add_argument("--verify-dataset-integrity", action="store_true")
    plan_parser.add_argument("--no-preprocess", action="store_true")
    plan_parser.add_argument("--clean", action="store_true")
    plan_parser.add_argument("-c", "--configurations", nargs="+", default=None, help="Optional configurations, such as 3d_fullres.")
    plan_parser.set_defaults(func=cmd_plan)

    train_parser = subparsers.add_parser("train", help="Run nnUNetv2_train.")
    add_common_args(train_parser)
    train_parser.add_argument("-d", "--dataset", required=True, help="Dataset name or ID, for example 501.")
    train_parser.add_argument("-c", "--configuration", default="3d_fullres")
    train_parser.add_argument("-f", "--fold", default="0")
    train_parser.add_argument("--trainer", default="nnUNetTrainer")
    train_parser.add_argument("--plans", default="nnUNetPlans")
    train_parser.add_argument("--device", choices=["cuda", "cpu", "mps"], default="cuda")
    train_parser.add_argument("--num-gpus", type=int, default=None)
    train_parser.add_argument("--pretrained-weights", type=Path, default=None)
    train_parser.add_argument("--continue-training", action="store_true")
    train_parser.add_argument("--validation-only", action="store_true")
    train_parser.add_argument("--validation-best", action="store_true")
    train_parser.add_argument("--disable-checkpointing", action="store_true")
    train_parser.add_argument("--use-compressed", action="store_true")
    train_parser.add_argument("--npz", action="store_true")
    train_parser.set_defaults(func=cmd_train)

    predict_parser = subparsers.add_parser("predict", help="Run nnUNetv2_predict.")
    add_common_args(predict_parser)
    predict_parser.add_argument("-i", "--input-dir", type=Path, required=True)
    predict_parser.add_argument("-o", "--output-dir", type=Path, required=True)
    predict_parser.add_argument("-d", "--dataset", required=True)
    predict_parser.add_argument("-c", "--configuration", default="3d_fullres")
    predict_parser.add_argument("-f", "--folds", nargs="+", default=None)
    predict_parser.add_argument("--trainer", default="nnUNetTrainer")
    predict_parser.add_argument("--plans", default="nnUNetPlans")
    predict_parser.add_argument("--checkpoint", default="checkpoint_final.pth")
    predict_parser.add_argument("--device", choices=["cuda", "cpu", "mps"], default="cuda")
    predict_parser.add_argument("--disable-tta", action="store_true")
    predict_parser.add_argument("--save-probabilities", action="store_true")
    predict_parser.add_argument("--continue-prediction", action="store_true")
    predict_parser.set_defaults(func=cmd_predict)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
