"""Generate lightweight SVG artifacts for the 3D U-Net training run."""

from __future__ import annotations

import html
import json
import argparse
from pathlib import Path
from typing import Iterable, Sequence


def _svg_header(width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        "<defs>",
        '<marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">',
        '<path d="M0,0 L10,4 L0,8 Z" fill="#2f3a4a"/>',
        "</marker>",
        "</defs>",
        '<rect width="100%" height="100%" fill="#fbfcfe"/>',
    ]


def _box(x: int, y: int, w: int, h: int, title: str, lines: Sequence[str], fill: str = "#eef6ff") -> str:
    text = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" '
        'stroke="#58708d" stroke-width="1.4"/>',
        f'<text x="{x + w / 2:.1f}" y="{y + 24}" text-anchor="middle" '
        'font-family="Arial, Microsoft YaHei, sans-serif" font-size="15" '
        f'font-weight="700" fill="#1d2b3a">{html.escape(title)}</text>',
    ]
    for i, line in enumerate(lines):
        text.append(
            f'<text x="{x + w / 2:.1f}" y="{y + 48 + i * 18}" text-anchor="middle" '
            'font-family="Arial, Microsoft YaHei, sans-serif" font-size="12" '
            f'fill="#405064">{html.escape(line)}</text>'
        )
    return "\n".join(text)


def _arrow(x1: int, y1: int, x2: int, y2: int) -> str:
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#2f3a4a" '
        'stroke-width="1.8" marker-end="url(#arrow)"/>'
    )


def write_training_flow_svg(path: Path) -> None:
    width, height = 1220, 520
    parts = _svg_header(width, height)
    parts.append(
        '<text x="610" y="36" text-anchor="middle" font-family="Arial, Microsoft YaHei, sans-serif" '
        'font-size="24" font-weight="700" fill="#152333">金属伪影 3D U-Net 训练流程</text>'
    )

    boxes = [
        (40, 80, "配对数据", ["datasets/CT", "datasets/mask"]),
        (250, 80, "可复现划分", ["固定 seed", "train / val"]),
        (460, 80, "3D Patch 采样", ["阳性中心采样", "按 mask 权重采样"]),
        (670, 80, "训练增强", ["翻转 / 旋转", "强度扰动 / 噪声"]),
        (880, 80, "3D U-Net", ["encoder / skip", "decoder / logits"]),
        (670, 300, "优化目标", ["0.7 Dice + 0.3 BCE", "pos_weight 封顶"]),
        (880, 300, "验证评估", ["Dice / IoU", "Recall / Precision"]),
        (1090, 300, "训练产物", ["best / last checkpoint", "metrics + SVG 图表"]),
    ]
    for x, y, title, lines in boxes:
        parts.append(_box(x, y, 160, 110, title, lines))

    for x in [200, 410, 620, 830]:
        parts.append(_arrow(x, 135, x + 50, 135))
    parts.append(_arrow(960, 190, 740, 300))
    parts.append(_arrow(830, 355, 880, 355))
    parts.append(_arrow(1040, 355, 1090, 355))
    parts.append(_arrow(750, 300, 750, 210))
    parts.append(
        '<text x="610" y="480" text-anchor="middle" font-family="Arial, Microsoft YaHei, sans-serif" '
        'font-size="13" fill="#52616f">每轮训练前按 epoch+seed 重建 patch 计划：同配置可复现，同时避免长期重复同一批 patch。</text>'
    )
    parts.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def write_unet3d_architecture_svg(path: Path, base_channels: int, depth: int) -> None:
    width, height = 1320, 620
    parts = _svg_header(width, height)
    parts.append(
        '<text x="660" y="36" text-anchor="middle" font-family="Arial, Microsoft YaHei, sans-serif" '
        'font-size="24" font-weight="700" fill="#152333">3D U-Net 神经网络架构</text>'
    )

    enc_x = 70
    enc_y0 = 90
    step_y = 95
    channels = [base_channels * (2**i) for i in range(depth + 1)]
    for level in range(depth):
        y = enc_y0 + level * step_y
        in_ch = 1 if level == 0 else channels[level - 1]
        out_ch = channels[level]
        parts.append(
            _box(
                enc_x + level * 90,
                y,
                180,
                70,
                f"Encoder {level}",
                [f"{in_ch}->{out_ch}", "Conv3D x2 + Norm + ReLU"],
                fill="#eaf5ee",
            )
        )
        if level < depth - 1:
            parts.append(_arrow(enc_x + level * 90 + 90, y + 70, enc_x + (level + 1) * 90 + 90, y + step_y))
            parts.append(
                f'<text x="{enc_x + level * 90 + 132}" y="{y + 92}" font-family="Arial" '
                'font-size="12" fill="#596a7d">MaxPool3D 2x2x2</text>'
            )

    bottleneck_x = 540
    bottleneck_y = 455
    parts.append(
        _box(
            bottleneck_x,
            bottleneck_y,
            210,
            80,
            "Bottleneck",
            [f"{channels[-2]}->{channels[-1]}", "deep semantic features"],
            fill="#fff3e0",
        )
    )
    parts.append(_arrow(enc_x + (depth - 1) * 90 + 90, enc_y0 + (depth - 1) * step_y + 70, bottleneck_x, bottleneck_y + 40))

    dec_start_x = 900
    for i, level in enumerate(reversed(range(depth))):
        y = enc_y0 + level * step_y
        x = dec_start_x - i * 90
        in_ch = channels[level + 1]
        out_ch = channels[level]
        parts.append(
            _box(
                x,
                y,
                190,
                76,
                f"Decoder {level}",
                [f"UpConv {in_ch}->{out_ch}", "Concat skip + Conv3D x2"],
                fill="#edf0ff",
            )
        )
        parts.append(_arrow(enc_x + level * 90 + 180, y + 38, x, y + 38))
        parts.append(
            f'<text x="{(enc_x + level * 90 + 180 + x) / 2:.1f}" y="{y + 28}" text-anchor="middle" '
            'font-family="Arial, Microsoft YaHei, sans-serif" font-size="12" fill="#596a7d">skip connection</text>'
        )

    parts.append(_arrow(bottleneck_x + 210, bottleneck_y + 40, dec_start_x - (depth - 1) * 90 + 95, enc_y0 + (depth - 1) * step_y + 76))
    parts.append(_arrow(dec_start_x + 190, enc_y0 + 38, 1145, enc_y0 + 38))
    parts.append(
        _box(
            1145,
            enc_y0,
            130,
            76,
            "Head",
            ["Conv1x1x1", "1-channel logits"],
            fill="#ffeef0",
        )
    )
    parts.append(
        '<text x="660" y="585" text-anchor="middle" font-family="Arial, Microsoft YaHei, sans-serif" '
        'font-size="13" fill="#52616f">输入/输出张量: (B, C, D, H, W)。模型自动 padding 并裁回原始空间尺寸。</text>'
    )
    parts.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def _polyline(points: Iterable[tuple[float, float]], color: str) -> str:
    data = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<polyline points="{data}" fill="none" stroke="{color}" stroke-width="2.4"/>'


def _scale(values: Sequence[float], x0: int, y0: int, width: int, height: int) -> list[tuple[float, float]]:
    if not values:
        return []
    vmin = min(values)
    vmax = max(values)
    if abs(vmax - vmin) < 1e-9:
        vmax = vmin + 1.0
    count = max(len(values) - 1, 1)
    points = []
    for i, value in enumerate(values):
        x = x0 + width * i / count
        y = y0 + height - (value - vmin) * height / (vmax - vmin)
        points.append((x, y))
    return points


def write_metrics_curves_svg(metrics_path: Path, output_path: Path) -> None:
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    epochs = metrics.get("epochs", [])
    train_loss = [float(row["train"]["loss"]) for row in epochs]
    val_loss = [float(row["val"]["loss"]) for row in epochs]
    val_dice = [float(row["val"]["dice"]) for row in epochs]
    val_iou = [float(row["val"]["iou"]) for row in epochs]

    width, height = 980, 430
    parts = _svg_header(width, height)
    parts.append(
        '<text x="490" y="34" text-anchor="middle" font-family="Arial, Microsoft YaHei, sans-serif" '
        'font-size="22" font-weight="700" fill="#152333">训练指标曲线</text>'
    )

    plots = [
        (60, 75, "Loss", [("train", train_loss, "#2d6cdf"), ("val", val_loss, "#d94f45")]),
        (540, 75, "Validation Metrics", [("dice", val_dice, "#26966f"), ("iou", val_iou, "#8c61d3")]),
    ]
    for x, y, title, series in plots:
        parts.append(f'<rect x="{x}" y="{y}" width="380" height="260" fill="#ffffff" stroke="#c8d2df"/>')
        parts.append(
            f'<text x="{x + 190}" y="{y + 24}" text-anchor="middle" font-family="Arial" '
            f'font-size="15" font-weight="700" fill="#1d2b3a">{title}</text>'
        )
        parts.append(f'<line x1="{x + 42}" y1="{y + 220}" x2="{x + 350}" y2="{y + 220}" stroke="#75808c"/>')
        parts.append(f'<line x1="{x + 42}" y1="{y + 48}" x2="{x + 42}" y2="{y + 220}" stroke="#75808c"/>')
        for name, values, color in series:
            points = _scale(values, x + 42, y + 48, 308, 172)
            if points:
                parts.append(_polyline(points, color))
            legend_y = y + 248 + 18 * series.index((name, values, color))
            parts.append(f'<rect x="{x + 42}" y="{legend_y - 10}" width="14" height="4" fill="{color}"/>')
            parts.append(
                f'<text x="{x + 64}" y="{legend_y - 5}" font-family="Arial" font-size="12" '
                f'fill="#405064">{html.escape(name)}</text>'
            )
    parts.append("</svg>")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(parts), encoding="utf-8")


def write_all_artifacts(output_dir: Path, metrics_path: Path, base_channels: int, depth: int) -> None:
    figures = output_dir / "figures"
    write_training_flow_svg(figures / "training_flow.svg")
    write_unet3d_architecture_svg(figures / "unet3d_architecture.svg", base_channels, depth)
    if metrics_path.exists():
        write_metrics_curves_svg(metrics_path, figures / "training_curves.svg")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate training flow and 3D U-Net SVG artifacts.")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent / "runs" / "artifacts")
    parser.add_argument("--metrics", type=Path, default=None)
    parser.add_argument("--base-channels", type=int, default=16)
    parser.add_argument("--depth", type=int, default=3)
    args = parser.parse_args()

    metrics_path = args.metrics or args.output_dir / "metrics.json"
    write_all_artifacts(args.output_dir, metrics_path, args.base_channels, args.depth)
    print(f"saved figures={args.output_dir / 'figures'}")


if __name__ == "__main__":
    main()
