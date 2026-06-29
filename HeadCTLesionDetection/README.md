# Head CT Lesion Detection

头部 CT 病灶识别服务。当前支持 `mock` 和 `model` 两种模式：`mock` 用于合同测试，`model` 用于接入颅内出血分类 checkpoint。

## 启动

```powershell
python HeadCTLesionDetection/LesionDetectionServer.py
```

默认地址：

```text
http://localhost:8020
```

## 接口

- `GET /api/head-ct-lesion/health`
- `POST /api/head-ct-lesion/tasks`
- `GET /api/head-ct-lesion/tasks/{task_id}`
- `GET /api/head-ct-lesion/results/{task_id}`

## Mock 行为

- 不加载真实模型。
- 支持 `hemorrhage` 和 `fracture` 两个占位类型。
- 返回固定阴性结果。
- 根据 `quality_context.severity` 生成 warning。

## Model 模式

启用真实颅内出血分类模型：

```powershell
$env:LESION_MODE="model"
$env:HEMORRHAGE_CHECKPOINT="D:\exam\HeadCTLesionDetection\models\hemorrhage\runs\hemorrhage_v1\best.pt"
$env:HEMORRHAGE_DEVICE="auto"
python HeadCTLesionDetection/LesionDetectionServer.py
```

说明：

- `LESION_MODE=mock` 是默认值。
- `LESION_MODE=model` 目前只支持 `requested_lesions=hemorrhage`。
- `/api/head-ct-lesion/health` 会返回 checkpoint 路径、是否存在、推理设备。
- checkpoint 缺失时任务会进入 `failed`，错误码为 `MODEL_CHECKPOINT_NOT_FOUND`。

### VinBigData CNN-LSTM 接入

VinBigData MIDL 2020 CNN-LSTM 模型公开说明见：

```text
https://github.com/vinbigdata-medical/midl2020-cnnlstm-ich
```

该模型使用 ResNet-50/CNN 提取单层 CT 三窗图像特征，并用 LSTM 建模层间关系；仓库 README
说明其预训练权重发布在 Kaggle：

```text
https://www.kaggle.com/dattran2346/midl2020-cnn-lstm
```

将下载后的权重放到本地后，可这样启动：

```powershell
$env:LESION_MODE="model"
$env:HEMORRHAGE_MODEL_PROVIDER="vinbigdata"
$env:VINBIGDATA_CHECKPOINT="D:\exam\HeadCTLesionDetection\models\hemorrhage\external_weights\vinbigdata_cnn_lstm.pt"
$env:HEMORRHAGE_DEVICE="auto"
python HeadCTLesionDetection/LesionDetectionServer.py
```

可选参数：

```powershell
$env:VINBIGDATA_IMAGE_SIZE="512"
$env:VINBIGDATA_MAX_SLICES="64"
$env:VINBIGDATA_THRESHOLD="0.5"
```

说明：

- `HEMORRHAGE_MODEL_PROVIDER=local` 使用本项目训练的 3D CNN/MONAI checkpoint。
- `HEMORRHAGE_MODEL_PROVIDER=vinbigdata` 使用 VinBigData CNN-LSTM adapter。
- 权重缺失时不回落到 mock，任务会失败并返回 `MODEL_CHECKPOINT_NOT_FOUND`。
- VinBigData 输出会包含 `subtype_probabilities`，包括 `any`、`epidural`、`intraparenchymal`、`intraventricular`、`subarachnoid`、`subdural`。

## 训练优化与断点恢复

颅内出血分类训练脚本支持预处理缓存、断点恢复和中断保护：

```powershell
python HeadCTLesionDetection/models/hemorrhage/train.py `
  --cache-dir D:\exam\.tmp\hemorrhage_cache `
  --resume HeadCTLesionDetection\models\hemorrhage\runs\hemorrhage_v1\last.pt
```

说明：

- `--cache-dir` 会缓存 NIfTI 预处理后的 tensor，缓存 key 包含文件路径、修改时间、目标尺寸和窗宽窗位参数。
- 每轮训练都会保存 `last.pt`；验证指标最优时保存 `best.pt`。
- 如果训练被 `Ctrl+C` 中断，会额外保存 `interrupted.pt`，便于后续从当前权重继续。
- CUDA 训练时 DataLoader 会自动启用 `pin_memory`，并使用 non-blocking 拷贝；`--num-workers > 0` 时启用 worker 持久化和预取。
- 验证阶段使用 `torch.inference_mode()`，减少不必要的 autograd 开销。

## 测试

```powershell
python -m pytest HeadCTLesionDetection/tests/test_lesion_contract.py
```
