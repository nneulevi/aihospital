import argparse
import json
from collections import deque
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np

try:
    import SimpleITK as sitk  # type: ignore
except ImportError:
    sitk = None


Offset3D = Tuple[int, int, int]


def build_offsets(radius: int, include_center: bool = True) -> List[Offset3D]:
    if radius <= 0:
        return [(0, 0, 0)] if include_center else []
    offsets: List[Offset3D] = []
    for dz in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if max(abs(dz), abs(dy), abs(dx)) <= radius:
                    if include_center or (dz, dy, dx) != (0, 0, 0):
                        offsets.append((dz, dy, dx))
    return offsets


def shift_bool(mask: np.ndarray, offset: Offset3D) -> np.ndarray:
    dz, dy, dx = offset
    z0_src = max(0, -dz)
    z1_src = mask.shape[0] - max(0, dz)
    y0_src = max(0, -dy)
    y1_src = mask.shape[1] - max(0, dy)
    x0_src = max(0, -dx)
    x1_src = mask.shape[2] - max(0, dx)

    z0_dst = max(0, dz)
    z1_dst = z0_dst + (z1_src - z0_src)
    y0_dst = max(0, dy)
    y1_dst = y0_dst + (y1_src - y0_src)
    x0_dst = max(0, dx)
    x1_dst = x0_dst + (x1_src - x0_src)

    shifted = np.zeros_like(mask, dtype=bool)
    if z1_src > z0_src and y1_src > y0_src and x1_src > x0_src:
        shifted[z0_dst:z1_dst, y0_dst:y1_dst, x0_dst:x1_dst] = mask[z0_src:z1_src, y0_src:y1_src, x0_src:x1_src]
    return shifted


def binary_dilation(mask: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return mask.copy()
    result = np.zeros_like(mask, dtype=bool)
    for offset in build_offsets(radius):
        result |= shift_bool(mask, offset)
    return result


def binary_erosion(mask: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return mask.copy()
    result = np.ones_like(mask, dtype=bool)
    for offset in build_offsets(radius):
        result &= shift_bool(mask, offset)
    return result


def binary_opening(mask: np.ndarray, radius: int) -> np.ndarray:
    return binary_dilation(binary_erosion(mask, radius), radius)


def binary_closing(mask: np.ndarray, radius: int) -> np.ndarray:
    return binary_erosion(binary_dilation(mask, radius), radius)


def connected_components_filter(mask: np.ndarray, min_size: int) -> Tuple[np.ndarray, List[int]]:
    if min_size <= 1:
        return mask.copy(), []

    visited = np.zeros_like(mask, dtype=bool)
    kept = np.zeros_like(mask, dtype=bool)
    component_sizes: List[int] = []
    neighbors = build_offsets(1, include_center=False)

    depth, height, width = mask.shape
    for z in range(depth):
        for y in range(height):
            for x in range(width):
                if not mask[z, y, x] or visited[z, y, x]:
                    continue

                queue: deque[Tuple[int, int, int]] = deque([(z, y, x)])
                visited[z, y, x] = True
                component: List[Tuple[int, int, int]] = []

                while queue:
                    cz, cy, cx = queue.popleft()
                    component.append((cz, cy, cx))
                    for dz, dy, dx in neighbors:
                        nz, ny, nx = cz + dz, cy + dy, cx + dx
                        if 0 <= nz < depth and 0 <= ny < height and 0 <= nx < width:
                            if mask[nz, ny, nx] and not visited[nz, ny, nx]:
                                visited[nz, ny, nx] = True
                                queue.append((nz, ny, nx))

                component_sizes.append(len(component))
                if len(component) >= min_size:
                    for cz, cy, cx in component:
                        kept[cz, cy, cx] = True

    return kept, sorted(component_sizes, reverse=True)


def refine_by_gradient(candidate_mask: np.ndarray, gradient_magnitude: np.ndarray, gradient_threshold: float) -> np.ndarray:
    if gradient_threshold <= 0:
        return candidate_mask.copy()

    strong_edges = binary_dilation(gradient_magnitude >= gradient_threshold, radius=1)
    visited = np.zeros_like(candidate_mask, dtype=bool)
    kept = np.zeros_like(candidate_mask, dtype=bool)
    neighbors = build_offsets(1, include_center=False)
    depth, height, width = candidate_mask.shape

    for z in range(depth):
        for y in range(height):
            for x in range(width):
                if not candidate_mask[z, y, x] or visited[z, y, x]:
                    continue

                queue: deque[Tuple[int, int, int]] = deque([(z, y, x)])
                visited[z, y, x] = True
                component: List[Tuple[int, int, int]] = []
                touches_edge = False

                while queue:
                    cz, cy, cx = queue.popleft()
                    component.append((cz, cy, cx))
                    touches_edge = touches_edge or bool(strong_edges[cz, cy, cx])
                    for dz, dy, dx in neighbors:
                        nz, ny, nx = cz + dz, cy + dy, cx + dx
                        if 0 <= nz < depth and 0 <= ny < height and 0 <= nx < width:
                            if candidate_mask[nz, ny, nx] and not visited[nz, ny, nx]:
                                visited[nz, ny, nx] = True
                                queue.append((nz, ny, nx))

                if touches_edge:
                    for cz, cy, cx in component:
                        kept[cz, cy, cx] = True

    return kept


def run_pipeline(
    volume: np.ndarray,
    threshold_low: float,
    threshold_high: float,
    gradient_threshold: float,
    opening_radius: int,
    closing_radius: int,
    min_component_size: int,
) -> Tuple[np.ndarray, dict, Dict[str, np.ndarray]]:
    volume = volume.astype(np.float32, copy=False)
    candidate_mask = (volume >= threshold_low) & (volume <= threshold_high)

    gradients = np.gradient(volume)
    gradient_magnitude = np.sqrt(sum(np.square(g, dtype=np.float32) for g in gradients))
    refined = refine_by_gradient(candidate_mask, gradient_magnitude, gradient_threshold)
    opened = binary_opening(refined, opening_radius)
    closed = binary_closing(opened, closing_radius)
    filtered, component_sizes = connected_components_filter(closed, min_component_size)

    stages = {
        "original": volume.copy(),
        "threshold": candidate_mask.astype(np.uint8),
        "gradient": refined.astype(np.uint8),
        "opening": opened.astype(np.uint8),
        "closing": closed.astype(np.uint8),
        "final": filtered.astype(np.uint8),
        "gradient_magnitude": gradient_magnitude.astype(np.float32),
    }

    stats = {
        "shape": list(volume.shape),
        "intensity_min": float(volume.min()),
        "intensity_max": float(volume.max()),
        "candidate_voxels": int(candidate_mask.sum()),
        "gradient_voxels": int(refined.sum()),
        "opened_voxels": int(opened.sum()),
        "closed_voxels": int(closed.sum()),
        "final_voxels": int(filtered.sum()),
        "component_count_before_filter": len(component_sizes),
        "largest_components_before_filter": component_sizes[:10],
        "parameters": {
            "threshold_low": threshold_low,
            "threshold_high": threshold_high,
            "gradient_threshold": gradient_threshold,
            "opening_radius": opening_radius,
            "closing_radius": closing_radius,
            "min_component_size": min_component_size,
        },
    }
    return filtered.astype(np.uint8), stats, stages


def create_demo_volume(shape: Sequence[int] = (32, 64, 64), seed: int = 1) -> np.ndarray:
    rng = np.random.default_rng(seed)
    z, y, x = np.indices(shape)
    volume = rng.normal(loc=20.0, scale=18.0, size=shape).astype(np.float32)

    bone_1 = ((y - 20) ** 2 + (x - 20) ** 2 <= 11 ** 2)
    bone_2 = ((y - 42) ** 2 + (x - 42) ** 2 <= 9 ** 2)
    volume[bone_1] += 180
    volume[bone_2] += 220

    metal_1 = ((z - 16) ** 2 + (y - 24) ** 2 + (x - 24) ** 2 <= 5 ** 2)
    metal_2 = ((z - 10) ** 2 + (y - 40) ** 2 + (x - 45) ** 2 <= 4 ** 2)
    volume[metal_1] = 2800
    volume[metal_2] = 3400

    streak = np.abs((x - y) + 8) <= 1
    volume[streak] += 360

    bright_noise = rng.random(shape) < 0.0015
    volume[bright_noise] = rng.uniform(600, 1500, size=bright_noise.sum())
    return volume


def load_volume(path: Path) -> Tuple[np.ndarray, object]:
    suffix = path.suffix.lower()
    if suffix == ".npy":
        return np.load(path), None

    if sitk is None:
        raise RuntimeError(
            "Only .npy input is supported without SimpleITK. Install SimpleITK to read medical image formats such as .nii, .nii.gz, .mha, .mhd."
        )

    image = sitk.ReadImage(str(path))
    array = sitk.GetArrayFromImage(image)
    return array, image


def save_mask(mask: np.ndarray, output_path: Path, image_template: object = None) -> None:
    suffix = output_path.suffix.lower()
    if suffix == ".npy":
        np.save(output_path, mask)
        return

    if sitk is None or image_template is None:
        raise RuntimeError("Saving non-.npy outputs requires SimpleITK and a non-.npy input image template.")

    image = sitk.GetImageFromArray(mask.astype(np.uint8))
    image.CopyInformation(image_template)
    sitk.WriteImage(image, str(output_path))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CT 金属伪影掩码生成工具")
    parser.add_argument("--input", type=Path, help="输入体数据路径，支持 .npy；安装 SimpleITK 后也支持 .nii/.nii.gz/.mha/.mhd")
    parser.add_argument("--output", type=Path, help="输出掩码路径，默认根据输入或 demo 名称自动生成 .npy")
    parser.add_argument("--threshold-low", type=float, default=800.0, help="阈值下限，默认 800")
    parser.add_argument("--threshold-high", type=float, default=4000.0, help="阈值上限，默认 4000")
    parser.add_argument("--gradient-threshold", type=float, default=120.0, help="梯度阈值，默认 120")
    parser.add_argument("--opening-radius", type=int, default=1, help="开运算半径，默认 1")
    parser.add_argument("--closing-radius", type=int, default=2, help="闭运算半径，默认 2")
    parser.add_argument("--min-component-size", type=int, default=50, help="最小连通域体素数，默认 50")
    parser.add_argument("--demo", action="store_true", help="运行内置合成示例，不依赖真实 CT 数据")
    parser.add_argument("--demo-seed", type=int, default=1, help="demo 随机种子")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.demo and args.input is None:
        raise SystemExit("请提供 --input，或使用 --demo 运行内置示例。")

    if args.demo:
        volume = create_demo_volume(seed=args.demo_seed)
        template = None
        source_name = f"demo_seed_{args.demo_seed}"
    else:
        volume, template = load_volume(args.input)
        source_name = args.input.stem

    mask, stats, _ = run_pipeline(
        volume=volume,
        threshold_low=args.threshold_low,
        threshold_high=args.threshold_high,
        gradient_threshold=args.gradient_threshold,
        opening_radius=args.opening_radius,
        closing_radius=args.closing_radius,
        min_component_size=args.min_component_size,
    )

    output_path = args.output or Path(f"{source_name}_metal_mask.npy")
    save_mask(mask, output_path, template)

    stats["output_path"] = str(output_path)
    stats["mask_unique_values"] = [int(v) for v in np.unique(mask)]
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
