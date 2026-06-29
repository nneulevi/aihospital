from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import streamlit as st

from metal_artifact_mask_tool import create_demo_volume, load_volume, run_pipeline, save_mask


st.set_page_config(page_title="CT金属伪影检测系统", layout="wide")


STAGE_TITLES = [
    ("original", "原始CT图像"),
    ("threshold", "二值化阈值滤波"),
    ("gradient", "梯度幅值滤波"),
    ("opening", "形态学开运算"),
    ("closing", "形态学闭运算"),
    ("final", "连通域过滤结果"),
]


def normalize_for_display(array2d: np.ndarray) -> np.ndarray:
    array2d = array2d.astype(np.float32)
    lo = float(np.min(array2d))
    hi = float(np.max(array2d))
    if hi - lo < 1e-6:
        return np.zeros_like(array2d, dtype=np.float32)
    return (array2d - lo) / (hi - lo)


def get_slice(volume: np.ndarray, slice_idx: int) -> np.ndarray:
    slice_idx = max(0, min(slice_idx, volume.shape[0] - 1))
    return volume[slice_idx]


def prepare_display(stage_name: str, slice_data: np.ndarray) -> Tuple[np.ndarray, str]:
    if stage_name == "original":
        return normalize_for_display(slice_data), "gray"
    return slice_data.astype(np.float32), "gray"


def load_input_volume(mode: str, uploaded_file, demo_seed: int):
    if mode == "内置Demo":
        return create_demo_volume(seed=demo_seed), None, f"demo_seed_{demo_seed}"

    if uploaded_file is None:
        return None, None, None

    suffix = Path(uploaded_file.name).suffix.lower()
    temp_path = Path(st.session_state.get("temp_input_path", "uploaded_ct.npy"))
    temp_path.write_bytes(uploaded_file.getbuffer())
    st.session_state["temp_input_path"] = str(temp_path)

    volume, template = load_volume(temp_path)
    source_name = Path(uploaded_file.name).stem
    return volume, template, source_name


def render_stage_card(title: str, image: np.ndarray, caption: str):
    st.markdown(f"### {title}")
    st.image(image, caption=caption, use_container_width=True, clamp=True)


def main() -> None:
    st.title("CT金属伪影检测系统")
    st.caption("专业医学影像分析 | 智能金属区域定位")

    with st.sidebar:
        st.header("处理参数")
        input_mode = st.radio("数据来源", ["内置Demo", "上传文件"], index=0)
        demo_seed = st.number_input("Demo随机种子", min_value=1, max_value=9999, value=1, step=1)
        uploaded_file = st.file_uploader("上传体数据", type=["npy", "nii", "gz", "mha", "mhd"])

        st.subheader("二值化阈值滤波")
        threshold_low = st.slider("阈值下限 (HU)", min_value=0, max_value=3000, value=800, step=10)
        threshold_high = st.slider("阈值上限 (HU)", min_value=1000, max_value=5000, value=4000, step=10)

        st.subheader("梯度幅值滤波")
        gradient_threshold = st.slider("梯度阈值", min_value=0, max_value=1000, value=120, step=10)

        st.subheader("形态学处理")
        opening_radius = st.slider("开运算半径", min_value=0, max_value=5, value=1, step=1)
        closing_radius = st.slider("闭运算半径", min_value=0, max_value=10, value=2, step=1)
        min_component_size = st.slider("最小连通域面积", min_value=1, max_value=5000, value=50, step=1)

    volume, template, source_name = load_input_volume(input_mode, uploaded_file, int(demo_seed))
    if volume is None:
        st.info("请在左侧选择内置 Demo，或者上传一个 `.npy/.nii/.nii.gz/.mha/.mhd` 体数据文件。")
        return

    mask, stats, stages = run_pipeline(
        volume=volume,
        threshold_low=float(threshold_low),
        threshold_high=float(threshold_high),
        gradient_threshold=float(gradient_threshold),
        opening_radius=int(opening_radius),
        closing_radius=int(closing_radius),
        min_component_size=int(min_component_size),
    )

    depth = int(volume.shape[0])
    default_slice = min(depth // 2, depth - 1)
    slice_idx = st.slider("切片选择", min_value=0, max_value=depth - 1, value=default_slice, step=1)

    st.success(f"数据加载成功: {tuple(volume.shape)}")

    cols = st.columns(3)
    preview_stages = STAGE_TITLES[:3]
    for col, (stage_name, stage_title) in zip(cols, preview_stages):
        with col:
            slice_data = get_slice(stages[stage_name], slice_idx)
            image, cmap = prepare_display(stage_name, slice_data)
            render_stage_card(stage_title, image, f"第 {slice_idx} 层")

    cols2 = st.columns(3)
    remain_stages = STAGE_TITLES[3:]
    for col, (stage_name, stage_title) in zip(cols2, remain_stages):
        with col:
            slice_data = get_slice(stages[stage_name], slice_idx)
            image, cmap = prepare_display(stage_name, slice_data)
            render_stage_card(stage_title, image, f"第 {slice_idx} 层")

    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    stat_col1.metric("候选体素", stats["candidate_voxels"])
    stat_col2.metric("梯度后体素", stats["gradient_voxels"])
    stat_col3.metric("闭运算后体素", stats["closed_voxels"])
    stat_col4.metric("最终体素", stats["final_voxels"])

    with st.expander("查看详细统计信息", expanded=False):
        st.json(stats)

    output_path = Path(f"{source_name}_metal_mask.npy")
    save_mask(mask, output_path, template)
    st.download_button(
        label="下载最终掩码 (.npy)",
        data=output_path.read_bytes(),
        file_name=output_path.name,
        mime="application/octet-stream",
    )


if __name__ == "__main__":
    main()
