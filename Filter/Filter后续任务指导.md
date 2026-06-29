# Filter 后续任务指导

## 1. 模块定位

Filter 在“智慧云脑诊疗平台业务模块图”中，应归属于：

```text
检查检验
  -> 头部 CT 医学影像识别
  -> AI 智能检查报告
```

更准确地说，Filter 当前不是完整的头部 CT 诊断系统，而是其中的：

```text
CT 影像质控与金属伪影掩码识别模块
```

它的核心职责是识别、标注和输出 CT 影像中的金属伪影区域，为后续头部 CT 病灶识别、医生审核和 AI 检查报告生成提供辅助信息。

Filter 不应直接扩展成挂号、问诊、电子病历、药房管理或完整诊断平台。更合理的方向是作为影像 AI 流程中的一个稳定子模块，被检查检验系统或影像识别系统调用。

## 2. 推荐业务流程

目标流程建议整理为：

```text
患者完成头部 CT 检查
  -> 检查检验系统产生 DICOM Study / Series
  -> Filter 读取 CT 影像
  -> 生成金属伪影 mask 与质控结果
  -> 头部 CT 医学影像识别模型参考 mask 进行分析
  -> AI 智能检查报告写入伪影提示和识别结果
  -> 医生端审核、修正、确认
  -> 修正结果回流训练数据集
```

该流程中，Filter 主要承担三件事：

- 影像预处理：读取、标准化、转换 CT 体数据。
- 伪影识别：规则滤波、2D U-Net、3D U-Net 或混合策略生成 mask。
- 结构化输出：给后续系统提供 mask、统计指标、截图和报告字段。

## 3. 后续优化优先级

### P0：统一输入输出

优先把 Filter 做成可被平台稳定调用的影像处理模块。

输入建议支持：

- DICOM 序列文件夹。
- NIfTI：`.nii` / `.nii.gz`。
- MHA / MHD。
- 内部测试用 `.npy`。

输出建议统一为：

```text
output/
  mask.nii.gz
  result.json
  preview_axial.png
  preview_coronal.png
  preview_sagittal.png
```

其中 `result.json` 至少包含：

```json
{
  "study_id": "",
  "series_id": "",
  "source_path": "",
  "artifact_detected": true,
  "artifact_ratio": 0.034,
  "positive_voxels": 12345,
  "affected_slices": [42, 43, 44],
  "severity": "moderate",
  "method": "unet2d",
  "model_version": "unet2d-v1",
  "threshold": 0.35,
  "suggestion": "存在中度金属伪影，可能影响邻近区域判断"
}
```

### P1：明确算法分层

建议保留三层能力，而不是只依赖单一模型：

- 规则滤波：作为快速 baseline 和无模型 fallback。
- 2D U-Net：作为低显存、快速推理方案，适合当前 `UNet2D方案`。
- 3D U-Net：作为更完整的体数据分割方案，适合最终效果优化。

推荐调用策略：

```text
默认快速模式：规则滤波 + 2D U-Net
高质量模式：3D U-Net
无模型模式：SimpleITK 规则滤波
医生标注模式：自动 mask + 手动修正
```

### P2：加入医生审核闭环

Filter 当前已有标注和可视化基础，后续应重点增强“自动结果 -> 医生修正 -> 数据回流”的闭环。

建议任务：

- 支持加载自动预测 mask。
- 支持医生在三平面视图中修正 mask。
- 保存修正后的 mask。
- 记录修正来源、医生确认状态和时间。
- 将确认样本加入训练数据目录。

推荐增加元数据：

```json
{
  "case_id": "",
  "mask_source": "ai_corrected_by_doctor",
  "review_status": "confirmed",
  "reviewer": "",
  "review_time": "",
  "model_version": "",
  "notes": ""
}
```

### P3：服务化接口

当桌面端和训练流程稳定后，再考虑把 Filter 封装为服务。

优先级建议：

1. CLI 命令稳定。
2. Python API 稳定。
3. FastAPI / HTTP 服务。
4. 平台集成接口。

CLI 示例：

```powershell
python metal_artifact_mask_tool.py --input path/to/ct.nii.gz --output output/mask.nii.gz --json output/result.json
```

Python API 示例：

```python
from filter_core import run_filter

result = run_filter(
    input_path="path/to/ct.nii.gz",
    output_dir="output",
    mode="unet2d"
)
```

HTTP 接口示例：

```text
POST /api/ct-artifact/detect
GET  /api/ct-artifact/tasks/{task_id}
GET  /api/ct-artifact/results/{task_id}
```

### P4：报告字段对接

Filter 的结果应能进入 AI 智能检查报告，但只写“质控与伪影提示”，不要冒充最终诊断。

建议报告片段：

```text
影像质控提示：本次头部 CT 检测到金属伪影，伪影主要分布于第 42-44 层，
估计影响体素比例约 3.4%。请结合原始图像判断邻近区域病灶识别可靠性。
```

严重程度建议：

```text
none: 未见明显金属伪影
minor: 轻度伪影，不明显影响识别
moderate: 中度伪影，可能影响局部判断
severe: 重度伪影，建议人工重点复核
```

## 4. 不建议优先做的事情

现阶段不建议把 Filter 直接扩展为：

- 完整问诊系统。
- 电子病历系统。
- 药房管理系统。
- 患者端应用。
- 大而全 AI 医生。
- 复杂 RAG 医学问答系统。
- MCP 驱动的多工具智能体平台。

RAG 和 MCP 可以作为后期增强能力，但不应成为当前主线。

适合后期引入 RAG 的场景：

- 查询项目文档、训练记录、医学指南。
- 解释参数含义。
- 辅助生成检查报告文字。

适合后期引入 MCP 的场景：

- 让 AI 助手自动调用训练、推理、可视化脚本。
- 自动读取模型指标和实验结果。
- 自动执行 DICOM 转换、批量推理和报告生成。

## 5. 近期任务清单

建议按以下顺序推进：

1. 梳理 `metal_artifact_mask_tool.py`、`predict_unet2d.py`、`predict_unet3d.py` 的公共输入输出格式。
2. 增加统一 `result.json` 输出。
3. 在 2D U-Net 推理中输出 mask 统计信息和 affected slices。
4. 在桌面端显示伪影比例、严重程度和报告建议。
5. 增加一键导出：mask + json + 三平面截图。
6. 建立 `model_version` 与 checkpoint 的对应关系。
7. 设计医生确认后的数据回流目录结构。
8. 增加小规模 smoke test，确保 CLI、预测和导出流程可运行。

推荐目录结构：

```text
Filter/
  filter_outputs/
    case_xxx/
      mask.nii.gz
      result.json
      preview_axial.png
      preview_coronal.png
      preview_sagittal.png
  reviewed_cases/
    case_xxx/
      ct.nii.gz
      mask_ai.nii.gz
      mask_reviewed.nii.gz
      review.json
```

## 6. 验收标准

一个阶段性可交付版本应满足：

- 能读取一例 CT 体数据。
- 能生成金属伪影 mask。
- 能输出结构化 `result.json`。
- 能生成三平面预览图。
- 能在 GUI 中查看 CT、mask 和叠加效果。
- 能保存医生修正后的 mask。
- 能区分规则滤波、2D U-Net、3D U-Net 的结果来源。
- 能把伪影提示文本交给 AI 智能检查报告模块使用。

## 7. 最终目标

Filter 的最佳定位不是“另一个诊疗平台”，而是：

```text
智慧云脑诊疗平台中的头部 CT 影像质控与金属伪影识别引擎
```

它应当做小而稳、接口清晰、结果可追踪、能被医生审核，并能持续积累高质量训练数据。
