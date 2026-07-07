"""VinBigData-style CNN-LSTM model and preprocessing utilities.

The public VinBigData MIDL 2020 model uses a CNN as a slice feature extractor
and an LSTM to model relationships across CT slices. This module keeps that
contract local so the service can load a real checkpoint without falling back
to mock inference.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Sequence

import numpy as np
import SimpleITK as sitk
import torch
from torch import nn
import torch.nn.functional as F


VINBIGDATA_CLASSES = ["any", "epidural", "intraparenchymal", "intraventricular", "subarachnoid", "subdural"]


@dataclass(frozen=True)
class VinBigDataLoadInfo:
    framework: str
    checkpoint_path: str
    missing_keys: list[str]
    unexpected_keys: list[str]
    inference_strategy: Optional[dict[str, Any]] = None


def resolve_device(device_arg: str) -> torch.device:
    if device_arg == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(device_arg)


def window_image(volume: np.ndarray, center: float, width: float) -> np.ndarray:
    lower = center - width / 2.0
    upper = center + width / 2.0
    clipped = np.clip(volume.astype(np.float32, copy=False), lower, upper)
    return (clipped - lower) / max(width, 1e-6)


def read_volume(path: Path) -> np.ndarray:
    image = sitk.ReadImage(str(path))
    volume = sitk.GetArrayFromImage(image).astype(np.float32, copy=False)
    if volume.ndim == 2:
        volume = volume[None, :, :]
    if volume.ndim != 3:
        raise ValueError(f"expected 2D/3D CT volume, got shape={volume.shape}")
    return volume


def sample_slices(volume: np.ndarray, max_slices: int, offset: float = 0.0) -> np.ndarray:
    if volume.shape[0] <= max_slices:
        return volume
    positions = np.linspace(0, volume.shape[0] - 1, max_slices)
    if max_slices > 1:
        step = (volume.shape[0] - 1) / (max_slices - 1)
        positions = positions + offset * step
    indices = np.clip(positions, 0, volume.shape[0] - 1).round().astype(np.int64)
    return volume[indices]


def preprocess_vinbigdata_volume(
    path: Path,
    *,
    image_size: int = 512,
    max_slices: int = 64,
    slice_offset: float = 0.0,
    horizontal_flip: bool = False,
) -> torch.Tensor:
    volume = sample_slices(read_volume(path), max_slices, offset=slice_offset)
    channels = [
        window_image(volume, center=40.0, width=80.0),
        window_image(volume, center=80.0, width=200.0),
        window_image(volume, center=600.0, width=2800.0),
    ]
    array = np.stack(channels, axis=1).astype(np.float32, copy=False)  # T, C, H, W
    tensor = torch.from_numpy(array)
    if tensor.shape[-2:] != (image_size, image_size):
        tensor = F.interpolate(tensor, size=(image_size, image_size), mode="bilinear", align_corners=False)
    if horizontal_flip:
        tensor = torch.flip(tensor, dims=[-1])
    return tensor


class VinBigDataCnnLstm(nn.Module):
    def __init__(
        self,
        backbone: str = "resnet50",
        num_classes: int = 6,
        hidden_size: int = 256,
        lstm_layers: int = 1,
        bidirectional: bool = True,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        try:
            from torchvision import models
        except Exception as exc:  # pragma: no cover - dependency guard.
            raise RuntimeError("torchvision is required for VinBigData CNN-LSTM inference.") from exc
        if backbone != "resnet50":
            raise ValueError(f"unsupported VinBigData backbone: {backbone}")
        cnn = models.resnet50(weights=None)
        feature_dim = int(cnn.fc.in_features)
        cnn.fc = nn.Identity()
        self.cnn = cnn
        self.lstm = nn.LSTM(
            input_size=feature_dim,
            hidden_size=hidden_size,
            num_layers=lstm_layers,
            batch_first=True,
            bidirectional=bidirectional,
            dropout=dropout if lstm_layers > 1 else 0.0,
        )
        lstm_dim = hidden_size * (2 if bidirectional else 1)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(lstm_dim, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.ndim != 5:
            raise ValueError(f"expected input [B,T,3,H,W], got {tuple(x.shape)}")
        batch, slices, channels, height, width = x.shape
        features = self.cnn(x.reshape(batch * slices, channels, height, width))
        features = features.reshape(batch, slices, -1)
        sequence, _ = self.lstm(features)
        logits = self.classifier(self.dropout(sequence))
        return logits


class VinBigDataLayer0(nn.Module):
    def __init__(self, template: nn.Module) -> None:
        super().__init__()
        self.conv1 = template.conv1
        self.bn1 = template.bn1
        self.relu = template.relu
        self.maxpool = template.maxpool

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.maxpool(self.relu(self.bn1(self.conv1(x))))


class VinBigDataDecoder(nn.Module):
    def __init__(self, input_size: int, hidden_size: int, num_layers: int, bidirectional: bool, num_classes: int) -> None:
        super().__init__()
        self.recurrent = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=bidirectional,
        )
        self.fc = nn.Linear(hidden_size * (2 if bidirectional else 1), num_classes)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        sequence, _ = self.recurrent(features)
        return self.fc(sequence)


class VinBigDataBaselineResnet50(nn.Module):
    """Architecture used by the public `baseline_resnet50` checkpoint.

    The checkpoint stores ResNet blocks at top-level keys (`layer0`, `layer1`,
    ... `layer4`) and a sequence decoder under `decoder.recurrent`/`decoder.fc`.
    """

    def __init__(self, hidden_size: int = 512, num_layers: int = 2, bidirectional: bool = True, num_classes: int = 6) -> None:
        super().__init__()
        try:
            from torchvision import models
        except Exception as exc:  # pragma: no cover - dependency guard.
            raise RuntimeError("torchvision is required for VinBigData baseline_resnet50 inference.") from exc
        template = models.resnet50(weights=None)
        self.layer0 = VinBigDataLayer0(template)
        self.layer1 = template.layer1
        self.layer2 = template.layer2
        self.layer3 = template.layer3
        self.layer4 = template.layer4
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.decoder = VinBigDataDecoder(
            input_size=2048,
            hidden_size=hidden_size,
            num_layers=num_layers,
            bidirectional=bidirectional,
            num_classes=num_classes,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.ndim != 5:
            raise ValueError(f"expected input [B,T,3,H,W], got {tuple(x.shape)}")
        batch, slices, channels, height, width = x.shape
        image = x.reshape(batch * slices, channels, height, width)
        features = self.layer4(self.layer3(self.layer2(self.layer1(self.layer0(image)))))
        pooled = self.pool(features).flatten(1).reshape(batch, slices, -1)
        return self.decoder(pooled)


def _checkpoint_state_dict(checkpoint: Any) -> dict[str, torch.Tensor]:
    if isinstance(checkpoint, dict):
        for key in ("model_state", "state_dict", "model", "net"):
            candidate = checkpoint.get(key)
            if isinstance(candidate, dict):
                return candidate
        if all(isinstance(value, torch.Tensor) for value in checkpoint.values()):
            return checkpoint
    raise ValueError("checkpoint does not contain a recognizable state_dict")


def _normalize_state_dict_keys(state_dict: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    normalized: dict[str, torch.Tensor] = {}
    prefixes = ("module.", "model.", "net.")
    for key, value in state_dict.items():
        new_key = key
        changed = True
        while changed:
            changed = False
            for prefix in prefixes:
                if new_key.startswith(prefix):
                    new_key = new_key[len(prefix) :]
                    changed = True
        normalized[new_key] = value
    return normalized


def _is_baseline_resnet50_state_dict(state_dict: dict[str, torch.Tensor], metadata: dict[str, Any]) -> bool:
    return (
        str(metadata.get("arch", "")).lower() == "baseline_resnet50"
        or "layer0.conv1.weight" in state_dict
        or "decoder.recurrent.weight_ih_l0" in state_dict
    )


def _baseline_decoder_config(state_dict: dict[str, torch.Tensor]) -> dict[str, int | bool]:
    fc_weight = state_dict.get("decoder.fc.weight")
    recurrent_hh = state_dict.get("decoder.recurrent.weight_hh_l0")
    hidden_size = int(recurrent_hh.shape[1]) if recurrent_hh is not None else 512
    num_classes = int(fc_weight.shape[0]) if fc_weight is not None else 6
    bidirectional = "decoder.recurrent.weight_ih_l0_reverse" in state_dict
    layer_indices = {
        int(key.split("_l", 1)[1].split("_", 1)[0])
        for key in state_dict
        if key.startswith("decoder.recurrent.weight_ih_l") and "_reverse" not in key
    }
    num_layers = (max(layer_indices) + 1) if layer_indices else 2
    return {
        "hidden_size": hidden_size,
        "num_layers": num_layers,
        "bidirectional": bidirectional,
        "num_classes": num_classes,
    }


def load_vinbigdata_model(
    checkpoint_path: Path,
    device: torch.device,
    *,
    backbone: str = "resnet50",
    image_size: int = 512,
    max_slices: int = 64,
    hidden_size: int = 256,
    lstm_layers: int = 1,
    bidirectional: bool = True,
    dropout: float = 0.2,
) -> tuple[nn.Module, VinBigDataLoadInfo, dict[str, Any]]:
    try:
        scripted = torch.jit.load(str(checkpoint_path), map_location=device)
        scripted.to(device)
        scripted.eval()
        return scripted, VinBigDataLoadInfo("torchscript", str(checkpoint_path), [], []), {
            "image_size": image_size,
            "max_slices": max_slices,
        }
    except Exception:
        pass

    try:
        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    except TypeError:
        checkpoint = torch.load(checkpoint_path, map_location=device)
    except Exception:
        checkpoint = torch.load(checkpoint_path, map_location=device)

    metadata = checkpoint if isinstance(checkpoint, dict) else {}
    state_dict = _normalize_state_dict_keys(_checkpoint_state_dict(checkpoint))
    if _is_baseline_resnet50_state_dict(state_dict, metadata):
        config = _baseline_decoder_config(state_dict)
        model = VinBigDataBaselineResnet50(
            hidden_size=int(config["hidden_size"]),
            num_layers=int(config["num_layers"]),
            bidirectional=bool(config["bidirectional"]),
            num_classes=int(config["num_classes"]),
        )
        incompatible = model.load_state_dict(state_dict, strict=False)
        missing = list(incompatible.missing_keys)
        unexpected = list(incompatible.unexpected_keys)
        if missing or unexpected:
            raise ValueError(
                "VinBigData baseline_resnet50 checkpoint is incompatible; "
                f"missing={missing[:5]}, unexpected={unexpected[:5]}"
            )
        model.to(device)
        model.eval()
        return model, VinBigDataLoadInfo("state_dict", str(checkpoint_path), missing, unexpected), {
            "image_size": image_size,
            "max_slices": max_slices,
            "arch": str(metadata.get("arch", "baseline_resnet50")),
        }

    model = VinBigDataCnnLstm(
        backbone=str(metadata.get("backbone", backbone)),
        hidden_size=int(metadata.get("hidden_size", hidden_size)),
        lstm_layers=int(metadata.get("lstm_layers", lstm_layers)),
        bidirectional=bool(metadata.get("bidirectional", bidirectional)),
        dropout=float(metadata.get("dropout", dropout)),
    )
    incompatible = model.load_state_dict(state_dict, strict=False)
    missing = list(incompatible.missing_keys)
    unexpected = list(incompatible.unexpected_keys)
    total_keys = len(model.state_dict())
    loaded_keys = total_keys - len(missing)
    if loaded_keys <= max(3, total_keys // 3):
        raise ValueError(
            "VinBigData checkpoint is incompatible with the local CNN-LSTM architecture; "
            f"loaded_keys={loaded_keys}, total_keys={total_keys}, missing={missing[:5]}, unexpected={unexpected[:5]}"
        )
    model.to(device)
    model.eval()
    return model, VinBigDataLoadInfo("state_dict", str(checkpoint_path), missing, unexpected), {
        "image_size": int(metadata.get("image_size", image_size)),
        "max_slices": int(metadata.get("max_slices", max_slices)),
    }


def aggregate_logits(logits: torch.Tensor) -> torch.Tensor:
    if logits.ndim == 3:
        return logits.max(dim=1).values
    if logits.ndim == 2:
        return logits
    raise ValueError(f"unexpected VinBigData output shape: {tuple(logits.shape)}")


def predict_vinbigdata_probabilities(
    nifti_path: Path,
    checkpoint_path: Path,
    *,
    device: str = "auto",
    image_size: int = 512,
    max_slices: int = 64,
    sampling_offsets: Sequence[float] = (0.0,),
    tta_flip: bool = False,
) -> tuple[dict[str, float], VinBigDataLoadInfo]:
    resolved_device = resolve_device(device)
    model, load_info, metadata = load_vinbigdata_model(
        checkpoint_path,
        resolved_device,
        image_size=image_size,
        max_slices=max_slices,
    )
    offsets = [float(item) for item in sampling_offsets] or [0.0]
    flip_flags = [False, True] if tta_flip else [False]
    probability_rows: list[np.ndarray] = []
    with torch.inference_mode():
        for offset in offsets:
            for flip in flip_flags:
                image = preprocess_vinbigdata_volume(
                    nifti_path,
                    image_size=int(metadata.get("image_size", image_size)),
                    max_slices=int(metadata.get("max_slices", max_slices)),
                    slice_offset=offset,
                    horizontal_flip=flip,
                )
                logits = model(image[None, ...].to(resolved_device, dtype=torch.float32))
                row = torch.sigmoid(aggregate_logits(logits)).detach().cpu().numpy().reshape(-1)
                probability_rows.append(row)
    probabilities = np.mean(np.stack(probability_rows, axis=0), axis=0)
    strategy = {
        "name": "tta_flip_multi_offset" if tta_flip or len(offsets) > 1 else "single_center_sampling",
        "sampling_offsets": offsets,
        "horizontal_flip": bool(tta_flip),
        "variant_count": len(probability_rows),
        "image_size": int(metadata.get("image_size", image_size)),
        "max_slices": int(metadata.get("max_slices", max_slices)),
    }
    load_info = VinBigDataLoadInfo(
        load_info.framework,
        load_info.checkpoint_path,
        load_info.missing_keys,
        load_info.unexpected_keys,
        strategy,
    )
    return {
        label: float(probabilities[index])
        for index, label in enumerate(VINBIGDATA_CLASSES[: len(probabilities)])
    }, load_info
