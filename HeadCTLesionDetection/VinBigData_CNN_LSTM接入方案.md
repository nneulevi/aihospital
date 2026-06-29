# VinBigData CNN-LSTM 颅内出血分类模型接入方案

## 1. 接入目标

将 VinBigData MIDL 2020 CNN-LSTM 颅内出血分类模型作为 `HeadCTLesionDetection`
的真实模型 provider 接入，服务层继续保持现有 lesion contract：

```text
NIfTI CT -> lesion result -> Orchestrator -> ReportService
```

如果主平台上传 DICOM/RSNA 数据，应先经 Orchestrator 归一化为内部 `input.nii.gz`，再调用
LesionDetection。

## 2. 模型来源

公开仓库：

```text
https://github.com/vinbigdata-medical/midl2020-cnnlstm-ich
```

仓库 README 说明：

- 模型为 CNN + LSTM；
- CNN 提取单层 CT 图像特征；
- LSTM 建模 slice 间关系；
- 输入为三个不同窗宽窗位堆叠形成的 RGB-like 图像；
- 在 RSNA ICH Detection challenge 上报告 weighted log loss；
- 预训练权重发布在 Kaggle：

```text
https://www.kaggle.com/dattran2346/midl2020-cnn-lstm
```

## 3. 当前代码落点

核心文件：

```text
HeadCTLesionDetection/models/hemorrhage/vinbigdata_cnn_lstm.py
HeadCTLesionDetection/models/hemorrhage/infer.py
HeadCTLesionDetection/LesionDetectionServer.py
HeadCTLesionDetection/config.py
```

测试文件：

```text
HeadCTLesionDetection/tests/test_lesion_contract.py
```

## 4. 输入预处理

adapter 使用三窗 CT 输入：

| 通道 | center | width | 用途 |
| --- | ---: | ---: | --- |
| brain | 40 | 80 | 常规脑窗 |
| subdural | 80 | 200 | 硬膜下/出血观察 |
| bone | 600 | 2800 | 骨窗及高密度结构 |

处理流程：

1. 读取 `.nii/.nii.gz`；
2. 取 axial slices；
3. 最多采样 `VINBIGDATA_MAX_SLICES` 层；
4. 每层生成 3 通道窗宽窗位图；
5. resize 到 `VINBIGDATA_IMAGE_SIZE`；
6. 送入 CNN-LSTM；
7. 对 slice 级 logits 做 max aggregation；
8. 输出 6 类概率。

## 5. 输出字段

VinBigData provider 会在原有 lesion result 中增加：

```json
{
  "provider": "vinbigdata",
  "model_name": "vinbigdata_midl2020_cnn_lstm_ich",
  "model_version": "midl2020-rsna",
  "subtype_probabilities": {
    "any": 0.0,
    "epidural": 0.0,
    "intraparenchymal": 0.0,
    "intraventricular": 0.0,
    "subarachnoid": 0.0,
    "subdural": 0.0
  }
}
```

`confidence` 使用 `subtype_probabilities.any`；如果权重输出缺少 `any`，则使用所有返回概率中的最大值。

## 6. 服务启动方式

下载 Kaggle 权重后放入：

```text
D:\exam\HeadCTLesionDetection\models\hemorrhage\external_weights\vinbigdata_cnn_lstm.pt
```

启动：

```powershell
$env:LESION_MODE="model"
$env:HEMORRHAGE_MODEL_PROVIDER="vinbigdata"
$env:VINBIGDATA_CHECKPOINT="D:\exam\HeadCTLesionDetection\models\hemorrhage\external_weights\vinbigdata_cnn_lstm.pt"
$env:HEMORRHAGE_DEVICE="auto"
$env:VINBIGDATA_IMAGE_SIZE="512"
$env:VINBIGDATA_MAX_SLICES="64"
$env:VINBIGDATA_THRESHOLD="0.5"
python HeadCTLesionDetection/LesionDetectionServer.py
```

健康检查：

```http
GET /api/head-ct-lesion/health
```

应看到：

```json
{
  "mode": "model",
  "model_provider": "vinbigdata",
  "models": {
    "hemorrhage": {
      "provider": "vinbigdata",
      "checkpoint_exists": true
    }
  }
}
```

## 7. 单例推理

```powershell
python HeadCTLesionDetection/models/hemorrhage/infer.py `
  --provider vinbigdata `
  --input sample_ct.nii.gz `
  --checkpoint HeadCTLesionDetection/models/hemorrhage/external_weights/vinbigdata_cnn_lstm.pt `
  --device auto
```

## 8. 兼容策略

当前 adapter 支持：

- TorchScript：`torch.jit.load`；
- `model_state`；
- `state_dict`；
- `model`；
- 纯 PyTorch state dict。

如果权重与本地 CNN-LSTM 结构不兼容，推理会失败并返回 `INFERENCE_FAILED`，不会回落到 mock。

## 9. 验收标准

1. `/health` 显示 `model_provider=vinbigdata`；
2. checkpoint 缺失时任务失败，错误码为 `MODEL_CHECKPOINT_NOT_FOUND`；
3. checkpoint 存在且兼容时，任务返回 `provider=vinbigdata`；
4. 返回 `subtype_probabilities` 六类概率；
5. Orchestrator 调用 LesionDetection 时无需改接口；
6. 跨模块测试通过。

## 10. 当前限制

- 当前项目不内置 VinBigData 权重，需从 Kaggle 下载后放入本地；
- 若 Kaggle 权重是官方源码特有结构，可能需要根据真实 state dict key 增加一次映射；
- 当前输出为分类概率，不输出出血 mask 或 bbox；
- 正式使用前必须在本地验证集、CQ500/RSNA 外部集上评估阈值和校准。
