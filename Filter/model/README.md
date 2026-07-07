# 3D U-Net 金属伪影识别模型

本目录实现了一个 PyTorch 版 3D U-Net，结构参考 `M.png` 中的经典 U-Net：
编码端使用两层 `3x3x3` 卷积和 ReLU，随后 `2x2x2` 最大池化；解码端使用
`2x2x2` 转置卷积上采样，拼接同层编码特征，最后用 `1x1x1` 卷积输出分割 logits。
训练数据来自 `datasets/CT` 与 `datasets/mask` 中的同名 NIfTI 配对文件：
`CT` 为原始 CT 体数据，`mask` 为金属伪影标注数据。

## 文件

- `unet3d.py`: 模型定义、参数统计、二值 mask 预测工具。
- `datasets/CT/`: 原始 CT NIfTI 体数据。
- `datasets/mask/`: 与 CT 同名的金属伪影标注 mask。
- `config.py`: 集中管理默认路径、训练超参数、推理阈值和 patch 配置。
- `metal_artifact_dataset.py`: 读取 `datasets/CT` 与 `datasets/mask` 配对数据，并确定性采样 3D patch。
- `train_unet3d.py`: 可复现训练脚本，保存 checkpoint 与训练指标。
- `predict_unet3d.py`: 加载训练好的 checkpoint，对 CT NIfTI 做滑窗推理并输出 mask。
- `training_artifacts.py`: 生成训练流程图、3D U-Net 架构图和训练指标曲线。
- `visualize_results.py`: 输出 loss 曲线、混淆矩阵、CT/GT/Pred 样本图。
- `Detection/CTArtifactInfer.py`: 桌面工具使用的 AI 推理封装，支持 `predict_slice`、`predict_from_nii`、`predict_from_sitk`。
- `Detection/CTArtGui.py`: PySide6 桌面标注工具，支持 CT 加载、规则分割、AI 分割、三平面查看、可选 VTK 3D 视图和 mask 保存。
- `docs/figures/`: 已生成的流程图、网络架构图和训练曲线 SVG。
- `demo_unet3d.py`: 最小可运行示例，用随机 3D 体数据验证输入输出尺寸。
- `M.png`: 参考网络结构图。

## 运行

需要 PyTorch：

```powershell
pip install torch
python Filter/model/demo_unet3d.py
```

期望输出包含输入形状、logits 形状、mask 形状、参数量和 mask 取值。模型会自动对输入
空间尺寸做对称 padding，并在输出阶段裁回原始尺寸，因此输出分割图尺寸与输入体数据一致。

## 使用示例

```python
import torch
from unet3d import UNet3D

model = UNet3D(in_channels=1, out_channels=1, base_channels=32, depth=4)
volume = torch.randn(2, 1, 64, 128, 128)
logits = model(volume)
print(logits.shape)  # torch.Size([2, 1, 64, 128, 128])
```

多类别分割时，将 `out_channels` 设置为类别数，并对输出 logits 使用
`torch.softmax(logits, dim=1)`。

## 训练金属伪影识别

快速验证整条训练链路：

```powershell
python Filter/model/train_unet3d.py --epochs 1 --train-patches 2 --val-patches 1 --patch-size 16,64,64 --base-channels 4 --depth 2 --device cpu --sample-by-mask
```

正式训练可使用更大的 patch 和更多 epoch，例如：

```powershell
python Filter/model/train_unet3d.py --epochs 30 --train-patches 200 --val-patches 50 --patch-size 32,128,128 --base-channels 16 --depth 3 --sample-by-mask
```

默认读取：

```text
Filter/model/datasets/CT
Filter/model/datasets/mask
```

若数据放在其他位置，可使用 `--data-dir`，或分别指定 `--ct-dir` 与 `--mask-dir`。旧的
`Mask_mark/output/manifest.json` 仍可通过 `--manifest` 显式使用。

训练脚本会固定随机种子，确定性划分训练/验证集，并按 epoch 生成可复现的 patch 采样计划。
输出目录默认为 `runs/metal_unet3d/`，包含：

- `best_unet3d_metal.pt`: 验证 Dice 最高的模型。
- `last_unet3d_metal.pt`: 最后一个 epoch 的模型。
- `metrics.json`: 训练配置、数据统计、每轮 loss 与 Dice。
- `figures/training_flow.svg`: 基于训练要件和流程生成的流程图。
- `figures/unet3d_architecture.svg`: 神经网络架构图。
- `figures/training_curves.svg`: 训练 loss 与验证指标曲线。
- `visualizations/loss_curves.png`: 训练/验证 loss 曲线。
- `visualizations/confusion_matrix.png`: 体素级混淆矩阵。
- `visualizations/sample_ct_gt_pred.png`: CT、GT 标注和模型预测样本图。

由于金属伪影 mask 只占少量体素，训练过程做了以下优化：

- 损失函数使用 Dice 主导的 `0.7 * DiceLoss + 0.3 * BCEWithLogitsLoss`。
- 根据训练集 mask 比例自动设置正类权重，并用 `--max-pos-weight` 封顶，默认最大 `30`。
- 默认启用轻量 3D 增强：随机翻转、轴向 90 度旋转、强度缩放/平移和少量噪声。
- `--sample-by-mask` 会按 mask 阳性体素比例提高含伪影样本的采样概率。
- CUDA 训练时 DataLoader 自动启用 `pin_memory`，tensor 拷贝使用 non-blocking；`--num-workers > 0` 时启用 worker 持久化和预取。
- 每轮输出 train loss、Dice loss、BCE loss，以及验证 Dice、IoU、Recall、Precision。
- 使用 `CosineAnnealingLR` 学习率调度，并按验证 Dice 保存最佳模型。
- 验证阶段使用 `torch.inference_mode()`，减少不必要的 autograd 开销。
- 默认使用 CT 窗宽 `[-1000, 3000]` 归一化到 `[-1, 1]`。

若只想做严格无增强的消融实验，可加入 `--no-augment`。

## 推理使用

训练完成后，可用最佳 checkpoint 对新的 CT NIfTI 体数据生成金属伪影预测 mask：

```powershell
python Filter/model/predict_unet3d.py --checkpoint Filter/model/runs/metal_unet3d/best_unet3d_metal.pt --input path/to/ct_volume.nii.gz --output path/to/pred_mask.nii.gz --patch-size 32,128,128 --overlap 0.5
```

输出 mask 会复制输入 CT 的空间信息，便于继续用 SimpleITK、VTK 或现有桌面工具查看。

## 双通道质控与 MAR 工作链路

当前平台采用“双通道”设计：

```text
原始 CT
  -> U-Net3D 金属伪影分割，输出 artifact mask / severity / affected_slices
  -> MAR 通道，登记 InDuDoNet 成熟公开 checkpoint，并执行 mask 引导图像域校正
  -> Orchestrator 汇总 quality_context
  -> LesionDetection 根据 input_policy 使用校正 CT
  -> RAG/LLM 报告辅助说明伪影影响与医生复核要求
```

当前已登记的成熟 MAR checkpoint：

```text
Filter/model/external_weights/metal_artifact_reduction/InDuDoNet_latest.pt
```

重要边界：

- `InDuDoNet_latest.pt` 是金属伪影减少/重建权重，不是金属伪影 mask 分割权重。
- 当前服务会在结果中返回 `artifact_reduction` 块，说明成熟 checkpoint 登记状态、实际执行引擎和校正 CT 地址。
- 由于业务上传的是标准 NIfTI 体数据，而官方 InDuDoNet 投影域推理需要 `ma_sinogram`、`LI_sinogram`、`metal_trace` 等上游张量，当前生产链路采用透明的 `sitk_mask_guided_gaussian_replacement` 图像域校正。
- 当金属伪影 mask 生成成功时，服务会输出 `corrected_ct.nii.gz`，并将 `artifact_reduction.corrected_ct_url` 与 `use_for_lesion_input=true` 写入结果；Orchestrator 后续病灶识别使用该校正 CT。
- `official_indudonet_executed=false` 表示未伪装为官方投影域 InDuDoNet 前向；`registered_checkpoint_model_name=InDuDoNet` 表示成熟 MAR checkpoint 已作为模型来源记录。

Filter 结果中新增的结构化字段：

```json
{
  "artifact_segmentation": {
    "mask_url": "/api/ct-artifact/files/{request_id}/mask.nii.gz",
    "artifact_detected": true,
    "artifact_ratio": 0.01,
    "severity": "moderate"
  },
  "artifact_reduction": {
    "enabled": true,
    "registered": true,
    "executable": true,
    "model_name": "mask_guided_image_domain_mar",
    "task_type": "metal_artifact_reduction",
    "registered_checkpoint_model_name": "InDuDoNet",
    "official_indudonet_executed": false,
    "execution_engine": "sitk_mask_guided_gaussian_replacement",
    "correction_status": "executed",
    "corrected_ct_url": "/api/ct-artifact/files/{request_id}/corrected_ct.nii.gz",
    "use_for_lesion_input": true,
    "execution_blockers": []
  }
}
```

## 结果可视化

训练完成后可生成 PNG 可视化结果：

```powershell
python Filter/model/visualize_results.py --run-dir Filter/model/runs/metal_unet3d
```

默认会读取 `run-dir/metrics.json`、`run-dir/best_unet3d_metal.pt`，并从
`datasets/CT` 与 `datasets/mask` 中取第一组同名数据输出 loss 曲线、混淆矩阵和
`CT / GT / Pred` 三联图。
