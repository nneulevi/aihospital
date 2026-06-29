"""Create a temporary hemorrhage checkpoint for service integration smoke tests.

This checkpoint uses random weights. It is only for verifying that the
LesionDetection service can load a model checkpoint and complete the API flow.
It must not be used for model quality evaluation or clinical validation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

try:
    from .config import INPUT_SHAPE, RUN_DIR, THRESHOLD, parse_shape
    from .model import Hemorrhage3DCNN, count_parameters
except ImportError:  # pragma: no cover - direct script fallback.
    from config import INPUT_SHAPE, RUN_DIR, THRESHOLD, parse_shape
    from model import Hemorrhage3DCNN, count_parameters


def create_smoke_checkpoint(
    output_path: Path,
    *,
    seed: int = 42,
    base_channels: int = 16,
    dropout: float = 0.2,
    input_shape: tuple[int, int, int] = INPUT_SHAPE,
) -> dict:
    torch.manual_seed(seed)
    model = Hemorrhage3DCNN(base_channels=base_channels, dropout=dropout)
    checkpoint = {
        "model_state": model.state_dict(),
        "base_channels": base_channels,
        "dropout": dropout,
        "input_shape": input_shape,
        "threshold": THRESHOLD,
        "model_name": "head_ct_hemorrhage_classifier",
        "model_version": "smoke-random-v1.0.0",
        "checkpoint_type": "smoke_random_weights",
        "intended_use": "technical integration smoke test only",
        "seed": seed,
        "parameter_count": count_parameters(model),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, output_path)
    return {
        "checkpoint": str(output_path),
        "checkpoint_type": checkpoint["checkpoint_type"],
        "intended_use": checkpoint["intended_use"],
        "input_shape": list(input_shape),
        "base_channels": base_channels,
        "dropout": dropout,
        "seed": seed,
        "parameter_count": checkpoint["parameter_count"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a random-weight checkpoint for API smoke testing.")
    parser.add_argument("--output", type=Path, default=RUN_DIR / "smoke_best.pt")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--base-channels", type=int, default=16)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--input-shape", default=",".join(str(item) for item in INPUT_SHAPE), help="Z,H,W, for example 32,160,160")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metadata = create_smoke_checkpoint(
        args.output,
        seed=args.seed,
        base_channels=args.base_channels,
        dropout=args.dropout,
        input_shape=parse_shape(args.input_shape),
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
