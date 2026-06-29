"""Export hemorrhage classifier checkpoint to TorchScript."""

from __future__ import annotations

import argparse
from pathlib import Path

import torch

try:
    from .config import INPUT_SHAPE, RUN_DIR
    from .infer import load_checkpoint, resolve_device
except ImportError:  # pragma: no cover - direct script fallback.
    from config import INPUT_SHAPE, RUN_DIR
    from infer import load_checkpoint, resolve_device


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export hemorrhage classifier to TorchScript.")
    parser.add_argument("--checkpoint", type=Path, default=RUN_DIR / "best.pt")
    parser.add_argument("--output", type=Path, default=RUN_DIR / "hemorrhage_classifier.ts")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    device = resolve_device(args.device)
    model, checkpoint = load_checkpoint(args.checkpoint, device)
    input_shape = tuple(checkpoint.get("input_shape", INPUT_SHAPE))
    example = torch.zeros((1, 1, *input_shape), dtype=torch.float32, device=device)
    traced = torch.jit.trace(model, example)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    traced.save(str(args.output))
    print(f"exported: {args.output}")


if __name__ == "__main__":
    main()
