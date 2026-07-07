# 真实成熟 Checkpoint 接入记录

## 目标

补足头部 CT AI 链路中的真实 checkpoint 接入策略，避免把本地 smoke 或本地小规模训练权重误标为“成熟模型”。

## 优先级

```text
市面已有公开成熟模型权重 > 本地训练权重 > smoke 兜底权重
```

## 分类模型

### 颅内出血分类

首选成熟模型：

- 名称：VinBigData MIDL2020 CNN-LSTM ICH
- 任务：头颅 CT 颅内出血分类 / subtype classification
- 代码：https://github.com/vinbigdata-medical/midl2020-cnnlstm-ich
- 论文：https://arxiv.org/abs/2005.10992
- 权重：https://www.kaggle.com/dattran2346/midl2020-cnn-lstm
- 公开说明：论文和仓库说明其在 RSNA ICH Detection challenge 上达到较强表现，并在 CQ500 上验证泛化。

本项目接入路径：

```text
HeadCTLesionDetection/models/hemorrhage/external_weights/vinbigdata_midl2020_cnn_lstm.pt
HeadCTLesionDetection/models/hemorrhage/external_weights/vinbigdata_midl2020_cnn_lstm.torchscript.pt
HeadCTLesionDetection/models/hemorrhage/external_weights/best_resnet50.pth
```

当前行为：

- 若上述成熟公开权重存在，`scripts/start_headct_platform.ps1` 会优先设置 `HEMORRHAGE_MODEL_PROVIDER=vinbigdata`。
- 当前启动脚本设置 `HEMORRHAGE_ALLOW_INFERENCE_FALLBACK=false`，真实模型加载或推理失败时不再静默退回 smoke/local fallback。
- 若成熟权重不存在，优先使用本地训练 `best.pt`；若仍不存在，使用 `smoke_best.pt`。
- 对 VinBigData raw `best_resnet50.pth`，当前已启用多 offset + flip TTA，结果中通过 `inference_strategy` 暴露实际推理策略。

## 分割模型

### 金属伪影分割

当前没有发现本机已具备的市面公开成熟金属伪影分割 checkpoint。

接入预留路径：

```text
Filter/model/external_weights/metal_artifact_segmentation/mature_metal_artifact_unet3d.pt
```

当前行为：

- 若该公开成熟权重存在，Filter 服务优先加载它。
- 否则使用本地训练权重：

```text
Filter/model/runs/metal_unet3d/best_unet3d_metal.pt
```

- 若本地训练权重也不存在，使用 smoke 权重：

```text
Filter/model/runs/config_visual_smoke/best_unet3d_metal.pt
```

### 金属伪影减少/MAR

已接入成熟公开模型权重：

- 名称：InDuDoNet
- 任务：CT Metal Artifact Reduction / Reconstruction
- 论文：An Interpretable Dual Domain Network for CT Metal Artifact Reduction, MICCAI 2021
- 代码：https://github.com/hongwang01/InDuDoNet
- 权重：https://github.com/hongwang01/InDuDoNet/blob/main/pretrained_model/InDuDoNet_latest.pt
- 本机路径：`Filter/model/external_weights/metal_artifact_reduction/InDuDoNet_latest.pt`
- 本机大小：`20701408` bytes

接入边界：

- 该 checkpoint 是成熟公开的金属伪影减少模型权重。
- 它不是当前 Filter 金属伪影 mask 分割服务的 U-Net3D checkpoint，不能直接替换 `best_unet3d_metal.pt`。
- 启动脚本会通过 `CT_MATURE_MAR_CHECKPOINT_PATH`、`CT_MATURE_MAR_MODEL_NAME`、`CT_MATURE_MAR_TASK_TYPE` 暴露该成熟 MAR checkpoint 元数据。
- Filter health 会返回 `mature_mar_checkpoint_exists`，用于验收成熟 MAR checkpoint 是否已被平台识别。

### 颅内出血分割

当前没有发现可直接接入且本机已具备的公开成熟 checkpoint。推荐成熟数据集路线：

- PhysioNet CT-ICH：https://physionet.org/content/ct-ich/1.3.1/
- INSTANCE 2022：https://instance.grand-challenge.org/

建议后续使用 nnU-Net 或 MONAI 训练分割 checkpoint，再接入 `HeadCTLesionDetection` 的分割结果协议。

## 验证命令

```powershell
python scripts\validate_true_checkpoints.py
```

严格检查至少存在一个公开成熟权重：

```powershell
python scripts\validate_true_checkpoints.py --strict-mature
```

注意：当前链路允许成熟权重缺失时 fallback，不会破坏 Project2、Orchestrator、Filter、Lesion、Report、EMR 的端到端流程。

## 2026-06-25 本机验证结果

执行：

```powershell
python scripts\validate_true_checkpoints.py
```

当前本机选择结果：

```text
Filter 金属伪影分割: local_project_trained
Filter 金属伪影减少/MAR: mature_public_external
Lesion 颅内出血分类: smoke_fallback
Lesion 颅内出血分割: dataset_required
```

说明：

- 当前本机未放置公开成熟金属伪影分割 checkpoint。
- 当前本机已放置公开成熟金属伪影减少/MAR checkpoint：`Filter/model/external_weights/metal_artifact_reduction/InDuDoNet_latest.pt`。
- 当前本机未放置 VinBigData MIDL2020 CNN-LSTM 权重。
- Filter 因存在本地训练权重，按第二优先级使用：

```text
Filter/model/runs/metal_unet3d/best_unet3d_metal.pt
```

- Lesion 分类因没有公开成熟权重，也没有本地 `best.pt`，按第三优先级使用：

```text
HeadCTLesionDetection/models/hemorrhage/runs/hemorrhage_v1/smoke_best.pt
```

重启服务后 health 验证：

```text
Filter checkpoint_provenance=local_project_trained
Lesion checkpoint_provenance=smoke_fallback
```

链路回归：

```powershell
python scripts\smoke_test_headct_platform.py
python scripts\e2e_project2_real_business.py
```

结果：

```text
smoke_test_headct_platform.py -> success
e2e_project2_real_business.py -> success
```

结论：当前尚未获得公开成熟 checkpoint，但系统已具备成熟权重优先接入入口；成熟权重缺失时不会影响现有端到端业务链路。

## 2026-06-26 补充验证结果

本次新增并验证：

```text
Filter 金属伪影减少/MAR: mature_public_external
Filter 金属伪影分割: local_project_trained
Lesion 颅内出血分类: mature_public_external_raw
Lesion 颅内出血分割: dataset_required
```

本机已存在的公开成熟相关权重：

```text
Filter/model/external_weights/metal_artifact_reduction/InDuDoNet_latest.pt
HeadCTLesionDetection/models/hemorrhage/external_weights/best_resnet50.pth
```

仍需区分：

- `InDuDoNet_latest.pt` 是金属伪影减少/MAR 权重，不是分割 mask 权重。
- `best_resnet50.pth` 是 VinBigData MIDL2020 CNN-LSTM 项目中的分类模型权重原始文件，不是颅内出血分割权重。
- 当前金属伪影分割若要求“公开成熟分割 checkpoint”，仍未找到可直接接入的市面成熟权重；系统继续使用本地训练 U-Net3D 权重保持业务链路可用。

本次回归验证：

```powershell
python scripts\validate_true_checkpoints.py --strict-mature
python -m pytest Filter\Fastapi\tests\test_ct_artifact_api.py HeadCTLesionDetection\tests\test_lesion_contract.py -q
python scripts\smoke_test_headct_platform.py
python scripts\e2e_project2_real_business.py
```

结果：

```text
validate_true_checkpoints.py --strict-mature -> passed
Filter/Lesion API contract tests -> 12 passed
smoke_test_headct_platform.py -> success
e2e_project2_real_business.py -> success
```

Filter health 已暴露：

```text
mature_mar_checkpoint_path=Filter/model/external_weights/metal_artifact_reduction/InDuDoNet_latest.pt
mature_mar_checkpoint_exists=true
mature_mar_model_name=InDuDoNet
mature_mar_task_type=metal_artifact_reduction
```

启动脚本同时修复了 Windows 环境变量中 `Path/PATH` 大小写重复导致 `Start-Process` 失败的问题。

## 2026-06-26 双通道工作链路完善

本次按“U-Net3D 分割 + InDuDoNet MAR 状态”的组合思路完善链路：

```text
上传 CT
  -> Filter artifact_segmentation: U-Net3D 输出 mask、artifact_ratio、severity
  -> Filter artifact_reduction: 暴露 InDuDoNet checkpoint 状态
  -> Orchestrator quality_context: 同时携带分割质控与 MAR 状态
  -> LesionDetection input_policy: 决定使用 original_ct 或 corrected_ct
  -> Report Assist: 将伪影影响与 MAR 使用状态写入 warnings
```

当时的历史状态（2026-06-26，已被 2026-07-07 补强覆盖）：

```text
artifact_segmentation: local_project_trained U-Net3D，参与当前伪影 mask 推理
artifact_reduction: InDuDoNet checkpoint 仅登记，尚未输出 corrected_ct
lesion_input_policy: 使用原始 CT
```

说明：

- 本次没有把原始 CT 复制成假 corrected CT。
- 在 InDuDoNet 上游模型代码、投影域预处理、重建后处理正式接入前，病灶识别仍使用原始 CT。
- 但 Orchestrator、LesionDetection 和报告辅助已经能够接收并展示 MAR 状态，后续补齐可执行 MAR 引擎时无需再改主链路协议。

本次新增/回归验证：

```powershell
python -m pytest Filter\Fastapi\tests\test_ct_artifact_api.py HeadCTLesionDetection\tests\test_lesion_contract.py HeadCTOrchestrator\tests\test_orchestrator_pipeline.py -q
```

结果：

```text
21 passed
```

真实服务回归：

```powershell
python scripts\smoke_test_headct_platform.py
python scripts\e2e_project2_real_business.py
```

结果：

```text
smoke_test_headct_platform.py -> success
e2e_project2_real_business.py -> success
```

当时真实 Orchestrator 结果中已出现：

```text
quality_control.artifact_reduction.model_name=InDuDoNet
quality_control.artifact_reduction.correction_status=仅登记未执行
quality_control.lesion_input_policy.used_input=original_ct（历史状态）
quality_control.lesion_input_policy.corrected_ct_used=false（历史状态）
```

这表示当前链路已经能够同时携带伪影分割结果和 MAR checkpoint 状态；但由于 InDuDoNet 可执行校正引擎尚未接入，病灶识别仍显式使用原始 CT。

## 2026-06-26 真实业务场景修正

本次继续修正两个容易误判为“已真实接入”的点。

### VinBigData raw checkpoint

此前 `best_resnet50.pth` 虽然已经放入本机，但其结构是 VinBigData 原项目的 `baseline_resnet50`，权重 key 为：

```text
layer0.*
layer1.*
layer2.*
layer3.*
layer4.*
decoder.recurrent.*
decoder.fc.*
```

而不是本项目早期简化适配器中的：

```text
cnn.*
lstm.*
classifier.*
```

因此真实 smoke 会因为架构不兼容进入本地 fallback。当前已新增 `VinBigDataBaselineResnet50` 适配器，直接加载 raw `best_resnet50.pth` 并执行推理。验收重点为：

```text
provider=vinbigdata
checkpoint_framework=state_dict
checkpoint_fallback_used=false
```

### InDuDoNet MAR checkpoint（历史状态，已被 2026-07-07 补强覆盖）

`InDuDoNet_latest.pt` 仍只能视为“成熟 MAR checkpoint 已登记”，不能视为“已经执行图像校正”。原因是官方 InDuDoNet 推理需要：

- 官方 `network/indudonet.py` 网络源码；
- ODL/Astra 投影/反投影几何算子；
- `ma_sinogram`、`LI_sinogram`、`metal_trace`、`LI_CT` 等投影域和线性插值输入；
- 输出 corrected CT 后再写入业务链路。

当时 Filter 返回：

```text
artifact_reduction.registered=true
artifact_reduction.executable 为否（历史状态）
artifact_reduction.correction_status=仅登记未执行（历史状态）
artifact_reduction.use_for_lesion_input 为否（历史状态）
```

这属于真实业务安全行为：平台知道存在成熟 MAR 权重，但不会伪造 corrected CT，也不会把原始 CT 复制成“校正后影像”。在可执行 MAR 引擎补齐前，LesionDetection 明确使用：

```text
input_policy.used_input=original_ct
input_policy.corrected_ct_used=false
```

## 2026-07-01 VinBigData 推理能力增强与 CQ500 子集验证

本次对成熟公开 VinBigData raw checkpoint 做了推理侧增强：

```text
HeadCTLesionDetection/models/hemorrhage/external_weights/best_resnet50.pth
```

新增能力：

- 多 offset slice sampling：`-0.25,0,0.25`
- horizontal flip TTA：启用
- 每例 6 个推理变体取平均概率
- 结果字段新增 `inference_strategy`
- Lesion 服务 health 暴露 `sampling_offsets` 与 `tta_flip`
- 启动脚本默认启用该策略，且继续禁止真实权重失败后静默 fallback。

真实 CQ500 子集验证：

```text
数据目录：D:\Data
实际病例目录示例：D:\Data\CQ500CT200 CQ500CT200
转换脚本：HeadCTLesionDetection/models/hemorrhage/prepare_cq500ct200.py
manifest：HeadCTLesionDetection/datasets/hemorrhage/cq500ct200_manifest.csv
推理结果：HeadCTLesionDetection/datasets/hemorrhage/cq500ct200_vinbigdata_tta_predictions.jsonl
```

执行结果：

```text
CQ500 子集 5 例 DICOM -> NIfTI 转换成功
序列选择规则：非增强 Plain 常规平扫优先，Thin Plain 作为次选
5 例均使用 VinBigData state_dict 完成 CUDA 推理
inference_strategy.variant_count=6
checkpoint_framework=state_dict
```

当前限制：

- `D:\Data` 下未发现 CQ500 `reads.csv` 或其他标签表。
- 仓库内目前只有 CQ500 字段释义文档，没有真实标签 CSV。
- 因此本次能够证明“成熟权重真实执行 + 真实 DICOM 子集推理 + TTA 增强启用”，但不能证明 AUC/Sensitivity/F1 等监督指标提升。
- 后续一旦补充标签表，可直接使用 `evaluate.py --provider vinbigdata --calibrate-threshold` 做阈值校准和指标验收。

## 2026-07-07 ICHSeg/nnU-Net 与 MAR 真实链路补强

### ICHSeg/nnU-Net 病灶分割

已接入成熟公开 ICHSeg nnU-Net checkpoint，并由 `HeadCTLesionDetection` 服务在真实任务中执行网络前向，输出病灶 mask 与三向叠加预览：

```text
checkpoint=HeadCTLesionDetection/models/hemorrhage/external_weights/ichseg_rank_nnunet/fold_0/checkpoint_final.pth
provider=ichseg_rank_nnunet
runtime_status=executed_direct_network_forward
checkpoint_fallback_used=false
mask_url=/api/head-ct-lesion/files/{task_id}/lesion_mask.nii.gz
preview_urls=axial/coronal/sagittal
```

与 VinBigData 分类模型合并时，若 ICHSeg 分割为阳性，最终主结论以分割 mask 证据为主，分类模型概率作为辅助参考，避免“分类低置信阴性”和“分割阳性”在报告中互相冲突。

### 金属伪影 MAR

当前链路已登记 `InDuDoNet_latest.pt` 作为成熟 MAR checkpoint；由于标准 NIfTI 上传不包含官方 InDuDoNet 投影域输入，服务不宣称执行官方投影域 InDuDoNet，而是执行透明的 mask 引导图像域 MAR 校正：

```text
artifact_reduction.registered=true
artifact_reduction.executable=true
artifact_reduction.execution_engine=sitk_mask_guided_gaussian_replacement
artifact_reduction.official_indudonet_executed=false
artifact_reduction.correction_status=executed
artifact_reduction.corrected_ct_url=/api/ct-artifact/files/{task_id}/corrected_ct.nii.gz
artifact_reduction.use_for_lesion_input=true
lesion_input_policy.used_input=corrected_ct
```

### 真实用户链路证据

```text
cd frontend
npx playwright test tests/visual/headct-real-user-workflow.spec.ts --project=desktop-chrome
```

结果：

```text
1 passed
```

该测试从医生端正常入口进入头部 CT 工作台，上传真实 NIfTI 测试影像，完成伪影分割、MAR 校正、VinBigData 分类、ICHSeg 分割、报告生成、医生审核发布和 EMR 归档校验。
