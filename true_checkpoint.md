你的任务是补足真实接入的checkpoint

## 约束
- 已有的成熟模型权重优先
- 退而求其次用成熟数据集
- 分分割模型和分类模型
- 契合项目的需求

## 验收条件
- 能准确给出正确结果
- 不影响已有工作链路正确性

## 本次接入策略

真实 checkpoint 的优先级统一定义为：

```text
市面已有公开成熟模型权重 > 本地训练权重 > smoke 兜底权重
```

说明：

- “市面已有公开成熟模型权重”指已有论文/开源项目/公开权重发布渠道支撑的模型，例如 VinBigData MIDL2020 CNN-LSTM 颅内出血分类模型。
- 本项目自己训练出来的 `best.pt`、`best_unet3d_metal.pt` 不再称为真实成熟权重，只作为没有公开成熟权重时的第二优先级可运行权重。
- smoke 权重只用于保证接口合同、前后端链路和端到端流程不断。

## 当前落地

- 启动脚本 `scripts/start_headct_platform.ps1` 已按三档优先级自动选择权重。
- Filter 金属伪影分割：
  - 优先：`Filter/model/external_weights/metal_artifact_segmentation/mature_metal_artifact_unet3d.pt`
  - 其次：`Filter/model/runs/metal_unet3d/best_unet3d_metal.pt`
  - 兜底：`Filter/model/runs/config_visual_smoke/best_unet3d_metal.pt`
- Filter 金属伪影减少/MAR：
  - 已接入成熟公开 checkpoint：`Filter/model/external_weights/metal_artifact_reduction/InDuDoNet_latest.pt`
  - 来源：InDuDoNet，MICCAI 2021，公开仓库 `https://github.com/hongwang01/InDuDoNet`
  - 说明：这是 CT 金属伪影减少/重建 checkpoint，不是金属伪影 mask 分割 checkpoint，因此不会替换当前 U-Net3D 分割权重。
- HeadCTLesionDetection 颅内出血分类：
  - 优先：`HeadCTLesionDetection/models/hemorrhage/external_weights/vinbigdata_midl2020_cnn_lstm.pt`
  - 兼容：`vinbigdata_midl2020_cnn_lstm.torchscript.pt`、`best_resnet50.pth`
  - 其次：`HeadCTLesionDetection/models/hemorrhage/runs/hemorrhage_v1/best.pt`
  - 兜底：`HeadCTLesionDetection/models/hemorrhage/runs/hemorrhage_v1/smoke_best.pt`
- HeadCTLesionDetection 颅内出血分割：
  - 当前未发现可直接接入且已在本机具备的公开成熟 checkpoint。
  - 后续应优先使用 PhysioNet CT-ICH 或 INSTANCE 2022 数据集训练 nnU-Net/MONAI 分割模型。

## 验证入口

```powershell
python scripts\validate_true_checkpoints.py
```

输出会区分：

- `mature_public_external`
- `mature_public_external_raw`
- `local_project_trained`
- `smoke_fallback`
- `dataset_required`

## 2026-06-26 补充接入

本次完成一个公开成熟金属伪影相关 checkpoint 的本地接入：

```text
Filter/model/external_weights/metal_artifact_reduction/InDuDoNet_latest.pt
```

验收边界：

- 已满足“金属伪影相关成熟公开 checkpoint 已下载并登记”的要求。
- 未满足“金属伪影分割成熟公开 checkpoint”的严格要求，因为当前查到的 InDuDoNet/DuDoNet/U-DuDoNet 属于 metal artifact reduction/reconstruction，不输出当前 Filter 协议需要的伪影 mask。
- 当前 Filter 分割推理仍按既有优先级使用 `mature_metal_artifact_unet3d.pt`、本地 `best_unet3d_metal.pt`、smoke 权重三档选择。

## 2026-06-26 真实业务口径修正

### VinBigData

`HeadCTLesionDetection/models/hemorrhage/external_weights/best_resnet50.pth` 已按 VinBigData 原始 `baseline_resnet50` 结构接入。该 raw checkpoint 的关键结构不是本地简化模型的 `cnn/lstm/classifier`，而是：

```text
layer0.*
layer1.*
layer2.*
layer3.*
layer4.*
decoder.recurrent.*
decoder.fc.*
```

当前验收要求：

```text
provider=vinbigdata
checkpoint_framework=state_dict
checkpoint_fallback_used=false
```

### InDuDoNet

`Filter/model/external_weights/metal_artifact_reduction/InDuDoNet_latest.pt` 已登记为成熟 MAR checkpoint。由于业务上传的是标准 NIfTI 体数据，不包含官方 InDuDoNet 投影域推理所需的 `ma_sinogram`、`LI_sinogram`、`metal_trace` 等输入，当前链路不伪装为官方投影域 InDuDoNet 前向，而是执行透明的 mask 引导图像域 MAR 校正。

```text
artifact_reduction.registered=true
artifact_reduction.executable=true
artifact_reduction.execution_engine=sitk_mask_guided_gaussian_replacement
artifact_reduction.official_indudonet_executed=false
artifact_reduction.correction_status=executed
artifact_reduction.corrected_ct_url=/api/ct-artifact/files/{task_id}/corrected_ct.nii.gz
artifact_reduction.use_for_lesion_input=true
```

这意味着当前业务链路已经能完成“伪影识别 -> 输出校正 CT -> 使用校正 CT 进入病灶识别”。若后续要宣称“官方 InDuDoNet 投影域推理”，仍需补齐官方网络源码、ODL/Astra 投影算子、sinogram/metal_trace/LI 输入。

### 本轮验收

```powershell
python scripts\validate_true_checkpoints.py --strict-mature
python -m pytest Filter\Fastapi\tests\test_ct_artifact_api.py HeadCTLesionDetection\tests\test_lesion_contract.py HeadCTOrchestrator\tests\test_orchestrator_pipeline.py -q
python scripts\smoke_test_headct_platform.py
python scripts\e2e_project2_real_business.py
```

结果：

```text
strict mature checkpoint validation -> passed
Filter/Lesion/Orchestrator tests -> 23 passed
Head CT smoke -> success
Project2 real business e2e -> success
```
