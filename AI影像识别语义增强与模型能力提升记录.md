# AI影像识别语义增强与模型能力提升记录

日期：2026-07-01

## 问题定位

医生端原先显示的“AI置信度 7%”来自病灶分类模型的 `lesion_analysis.summary.highest_confidence`，实际含义是“颅内出血阳性概率”，不是整套 AI 链路的可信度。

以当前样例 `testdata/headct/head_ct_positive_case.nii.gz` 运行 VinBigData MIDL2020 权重，真实输出为：

- 任意出血：6.74%
- 硬膜外出血：1.51%
- 脑实质内出血：1.55%
- 脑室内出血：2.46%
- 蛛网膜下腔出血：3.95%
- 硬膜下出血：0.38%
- 当前判定阈值：50%

因此低百分比应解释为“当前模型未提示明确颅内出血阳性倾向”，不应解释为“AI整体不可靠”。

## 已完成增强

### 1. 后端结构化字段增强

Project2 `ImageAnalyzeResponseVO` 新增字段：

- `positiveProbability`：出血阳性概率。
- `subtypeProbabilities`：出血亚型概率。
- `analysisReliability`：分析可靠性文字说明。
- `modelLimitations`：模型限制与复核提示。
- `previewUrls`：三视图可视化输出地址。

原 `confidence` 字段保留，用于兼容历史接口和数据库字段。

### 2. 医生端语义增强

医生端患者接诊页将：

- “AI置信度”改为“出血阳性概率”。
- 低概率显示为“未提示明确阳性倾向”，不再用红色弱置信度文案误导。
- 展示六类出血亚型概率条。
- 展示分析可靠性、链路状态、模型限制与复核重点。

### 3. 报告辅助增强

Orchestrator 的报告辅助模板现在会输出：

- 影像质量评估。
- 出血阳性概率。
- 判定阈值。
- 出血亚型概率。
- 模型输出为分类结果、不输出三维病灶边界的限制。
- 医生需要复核的重点区域和相邻层面。

规则模板不再依赖 `RAG_ENABLED=true`，即使 RAG 关闭，也会生成专业结构化报告辅助内容。

### 4. 模型输出增强

VinBigData 推理结果新增：

- `decision_threshold`
- `subtype_probabilities`

用于前端解释和报告草稿生成。

## 模型能力提升路径

当前不能通过手动调高概率来“提高模型能力”。合理路径如下：

## 2026-07-01 真实模型能力增强执行记录

### 1. VinBigData 推理侧增强

已在 VinBigData MIDL2020 raw `best_resnet50.pth` 适配器上加入真实推理增强：

- 多 offset 层面采样：`VINBIGDATA_SAMPLING_OFFSETS=-0.25,0,0.25`
- 水平翻转 TTA：`VINBIGDATA_TTA_FLIP=true`
- 每例推理变体数：`3 offsets x 2 flip = 6`
- 输出新增 `inference_strategy`，用于报告和验收追踪实际是否启用增强策略。

启动脚本 `scripts/start_headct_platform.ps1` 已默认启用该策略；服务 health 会暴露：

```text
models.hemorrhage.vinbigdata.sampling_offsets
models.hemorrhage.vinbigdata.tta_flip
```

### 2. CQ500CT200 真实数据子集准备

用户提供完整数据目录：

```text
D:\Data
```

本机实际病例目录格式为：

```text
D:\Data\CQ500CT200 CQ500CT200
D:\Data\CQ500CT201 CQ500CT201
...
```

已新增 DICOM 准备脚本：

```text
HeadCTLesionDetection/models/hemorrhage/prepare_cq500ct200.py
```

序列选择规则：

- 优先非增强序列。
- 优先包含 `Plain` / `Non-contrast` 的常规平扫序列。
- 常规平扫优先于 `Thin Plain` 薄层序列。
- 若没有明确常规平扫，再按切片数量兜底选择。

已先转换真实子集 5 例：

```powershell
python -X utf8 HeadCTLesionDetection\models\hemorrhage\prepare_cq500ct200.py `
  --dicom-root D:\Data `
  --output-dir HeadCTLesionDetection\datasets\hemorrhage\cq500ct200_images `
  --manifest HeadCTLesionDetection\datasets\hemorrhage\cq500ct200_manifest.csv `
  --limit 5 `
  --overwrite
```

转换结果：

```text
cases=5 converted=5 labeled=0
```

注意：当前 `D:\Data` 下未发现 `reads.csv`、`prediction_probabilities.csv` 或其他标签文件；仓库中也只有字段释义文档。因此该子集当前可用于真实推理与人工复核，但不能用于监督评估、阈值校准或训练。

### 3. CQ500 子集真实推理结果

已新增 manifest 批量推理脚本：

```text
HeadCTLesionDetection/models/hemorrhage/run_manifest_inference.py
```

使用成熟公开 raw checkpoint、CUDA、生产输入尺寸和增强策略执行：

```powershell
python -X utf8 HeadCTLesionDetection\models\hemorrhage\run_manifest_inference.py `
  --manifest HeadCTLesionDetection\datasets\hemorrhage\cq500ct200_manifest.csv `
  --checkpoint HeadCTLesionDetection\models\hemorrhage\external_weights\best_resnet50.pth `
  --output-jsonl HeadCTLesionDetection\datasets\hemorrhage\cq500ct200_vinbigdata_tta_predictions.jsonl `
  --device cuda `
  --threshold 0.5 `
  --image-size 512 `
  --max-slices 64 `
  --sampling-offsets=-0.25,0,0.25 `
  --tta-flip `
  --limit 5
```

输出证据文件：

```text
HeadCTLesionDetection/datasets/hemorrhage/cq500ct200_vinbigdata_tta_predictions.jsonl
```

5 例真实 CQ500 子集均由 VinBigData `state_dict` 完成推理，且每条结果均包含：

```text
checkpoint_framework=state_dict
inference_strategy.name=tta_flip_multi_offset
inference_strategy.variant_count=6
```

当前 5 例输出的任意出血阳性概率约为 `2.71% ~ 4.34%`。由于没有标签，不能判断这些低概率是否正确，也不能通过修改阈值声称模型能力提升。

## 2026-07-01 路线 2/3/4/6 继续执行记录

本次按“暂时忽略官方标签获取和 Grad-CAM，可先继续后续路线”的要求执行。

### 路线 2：扩大真实 CQ500 推理子集

已将真实 CQ500 子集从 5 例扩大到 20 例：

```powershell
python -X utf8 HeadCTLesionDetection\models\hemorrhage\prepare_cq500ct200.py `
  --dicom-root D:\Data `
  --output-dir HeadCTLesionDetection\datasets\hemorrhage\cq500ct200_images `
  --manifest HeadCTLesionDetection\datasets\hemorrhage\cq500ct200_manifest.csv `
  --limit 20 `
  --overwrite
```

转换结果：

```text
cases=20 converted=20 labeled=0
```

随后使用成熟公开 VinBigData raw checkpoint 执行真实 CUDA 推理：

```powershell
python -X utf8 HeadCTLesionDetection\models\hemorrhage\run_manifest_inference.py `
  --manifest HeadCTLesionDetection\datasets\hemorrhage\cq500ct200_manifest.csv `
  --checkpoint HeadCTLesionDetection\models\hemorrhage\external_weights\best_resnet50.pth `
  --output-jsonl HeadCTLesionDetection\datasets\hemorrhage\cq500ct200_vinbigdata_tta_predictions.jsonl `
  --device cuda `
  --threshold 0.5 `
  --image-size 512 `
  --max-slices 64 `
  --sampling-offsets=-0.25,0,0.25 `
  --tta-flip `
  --limit 20
```

20 例输出统计：

```text
count=20
min_positive_probability=0.022593243047595024
max_positive_probability=0.0433514229953289
mean_positive_probability=0.033216022234410045
```

当前 Top 5 概率病例：

```text
CQ500CT201 0.0433514229953289
CQ500CT210 0.04318690672516823
CQ500CT209 0.042926084250211716
CQ500CT203 0.03683404624462128
CQ500CT205 0.0358583964407444
```

### 路线 3：生成待标注 CSV

已新增复核模板生成脚本：

```text
HeadCTLesionDetection/models/hemorrhage/generate_cq500_review_template.py
```

已生成：

```text
HeadCTLesionDetection/datasets/hemorrhage/cq500ct200_review_template.csv
```

模板特点：

- 合并 `case_id`、`image_path`、`series_dir`、`slice_count`。
- 合并 VinBigData `positive_probability`。
- 增加 `probability_rank`。
- 增加 `review_priority`。
- 概率排名前 20% 标记为 `top_probability_review`，便于人工优先复核。
- `hemorrhage` 和各 subtype 标签列保持空白，不会伪造标签。

### 路线 4：阈值校准入口保护

已新增补标后 labels.csv 生成器：

```text
HeadCTLesionDetection/models/hemorrhage/finalize_reviewed_labels.py
```

该脚本会从复核模板中筛选已经填写标签的行，生成可供 `evaluate.py --calibrate-threshold` 使用的 `labels.csv`。

当前复核模板尚未填写标签，脚本已验证会明确拒绝：

```text
ValueError: no reviewed labels found; fill hemorrhage or subtype columns before finalizing labels.csv
```

这可以避免把空标签误当作阴性样本进行阈值校准。

### 路线 6：分割模型准备

已新增分割 mask 采集模板脚本：

```text
HeadCTLesionDetection/models/hemorrhage/generate_segmentation_mask_template.py
```

已生成：

```text
HeadCTLesionDetection/datasets/hemorrhage/cq500ct200_segmentation_mask_template.csv
```

该模板为每个病例生成期望 mask 路径：

```text
HeadCTLesionDetection/datasets/hemorrhage/masks/{case_id}.nii.gz
```

当前 20 例均为：

```text
annotation_status=mask_required
```

因此分割训练尚不能启动；等 voxel 级 mask 准备完成后，可继续使用既有 `segmentation_prepare.py` 和 `train_nnunet.py` 进入 nnU-Net/MONAI 分割训练流程。

### 阶段 1：验证集阈值校准

使用 RSNA/CQ500 或本地标注验证集运行：

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
python -X utf8 HeadCTLesionDetection/models/hemorrhage/evaluate.py `
  --provider vinbigdata `
  --checkpoint HeadCTLesionDetection/models/hemorrhage/external_weights/best_resnet50.pth `
  --labels-csv HeadCTLesionDetection/models/hemorrhage/labels.csv `
  --split val `
  --device cuda `
  --calibrate-threshold
```

输出：

- `metrics.json`
- `predictions.csv`
- `calibration.json`

根据验证集选择 `best_f1_threshold` 或 `best_youden_threshold`，再配置：

```powershell
$env:VINBIGDATA_THRESHOLD='校准后的阈值'
```

### 阶段 2：补充更贴近业务的样本

优先补充：

- 阳性出血病例。
- 轻微出血病例。
- 金属伪影干扰病例。
- 阴性正常病例。
- 伪影但无出血病例。

否则模型在演示样例上输出低阳性概率是合理现象，无法仅靠工程层面证明“识别能力强”。

### 阶段 3：引入定位/分割能力

VinBigData 当前是分类模型，不能输出病灶边界。若要让医生获得更强辅助价值，应接入：

- 颅内出血分割模型；
- 或 Grad-CAM/热力图解释；
- 或 nnU-Net/MONAI 训练出的病灶分割模型。

### 阶段 4：模型能力验收指标

建议至少记录：

- AUC
- Sensitivity
- Specificity
- Precision
- NPV
- F1
- 最佳阈值
- 混淆矩阵
- 正负样本数量

没有这些指标时，不应声称模型能力已提高，只能说“链路和表达增强已完成”。

## 当前结论

当前完成的是“报告与语义增强”和“模型能力提升入口”。它解决了医生端误读 7% 的问题，也为后续真实提升模型能力准备了验证与阈值校准工具。

真正提高模型识别能力仍需要验证集、阈值校准、阳性样本补充，或接入定位/分割模型。
