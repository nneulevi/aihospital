# Intracranial Hemorrhage Classifier

第一阶段颅内出血 series/study 级二分类模型骨架。

当前目标：

```text
.nii/.nii.gz CT -> hemorrhage confidence -> structured lesion result
```

本目录只负责模型训练、评估和单例推理，不负责 FastAPI 任务管理。

## 数据格式

推荐目录：

```text
HeadCTLesionDetection/datasets/hemorrhage/
  images/
    case_0001.nii.gz
    case_0002.nii.gz
  labels.csv
```

`labels.csv` 必需字段：

```csv
case_id,image_path,hemorrhage,source,split
case_0001,images/case_0001.nii.gz,1,CQ500,train
case_0002,images/case_0002.nii.gz,0,CQ500,val
```

如果没有 `hemorrhage` 字段，可用亚型字段自动聚合：

```csv
epidural,intraparenchymal,intraventricular,subarachnoid,subdural
```

任一亚型为阳性时，`hemorrhage=1`。

## RSNA/DICOM 数据准备

如果使用 RSNA Intracranial Hemorrhage Detection 的 Kaggle DICOM 数据，可先转换为本项目统一的
NIfTI + `labels.csv` 格式：

```powershell
python HeadCTLesionDetection/models/hemorrhage/prepare_rsna_dataset.py `
  --rsna-labels-csv D:\datasets\rsna-ich\stage_2_train.csv `
  --dicom-root D:\datasets\rsna-ich\stage_2_train `
  --output-dir HeadCTLesionDetection/datasets/hemorrhage_rsna `
  --skip-existing
```

快速试跑可加：

```powershell
--limit 100
```

输出结构：

```text
HeadCTLesionDetection/datasets/hemorrhage_rsna/
  images/
    ID_xxxxx.nii.gz
  labels.csv
```

说明：

- 脚本读取 RSNA `ID_xxx_any/subtype` 标签，并聚合为 `hemorrhage` 二分类标签。
- 当前准备脚本按 slice 生成训练记录，适合先接入 RSNA 分类预训练。
- `split` 使用 case_id + seed 确定性划分，避免每次运行训练/验证集变化。
- 完整 study/series 级建模仍建议后续结合 DICOM metadata 构建序列索引。

## 训练

默认轻量 PyTorch 训练：

```powershell
python HeadCTLesionDetection/models/hemorrhage/train.py `
  --labels-csv HeadCTLesionDetection/datasets/hemorrhage/labels.csv `
  --output-dir HeadCTLesionDetection/models/hemorrhage/runs/hemorrhage_v1 `
  --input-shape 32,160,160 `
  --batch-size 2 `
  --device auto
```

输出：

```text
runs/hemorrhage_v1/
  best.pt
  metrics.json
  label_map.json
  train_config.json
```

## MONAI 规范训练

如需使用更规范的医学影像训练流程，先安装可选依赖：

```powershell
pip install -r HeadCTLesionDetection/requirements-medimg.txt
```

然后使用 MONAI transforms + MONAI DenseNet：

```powershell
python HeadCTLesionDetection/models/hemorrhage/train_monai.py `
  --labels-csv HeadCTLesionDetection/datasets/hemorrhage/labels.csv `
  --output-dir HeadCTLesionDetection/models/hemorrhage/runs/monai_densenet121 `
  --network densenet121 `
  --input-shape 32,160,160 `
  --batch-size 2 `
  --device auto
```

MONAI 管线包含：

- `LoadImaged`
- `EnsureChannelFirstd`
- `ScaleIntensityRanged`
- `Resized`
- `RandFlipd`
- `RandRotate90d`
- `RandGaussianNoised`
- `EnsureTyped`

`infer.py` 可以自动识别 `framework=monai` 的 checkpoint。

## 评估

```powershell
python HeadCTLesionDetection/models/hemorrhage/evaluate.py `
  --labels-csv HeadCTLesionDetection/datasets/hemorrhage/labels.csv `
  --checkpoint HeadCTLesionDetection/models/hemorrhage/runs/hemorrhage_v1/best.pt `
  --split test
```

输出：

```text
runs/hemorrhage_v1/eval/
  metrics.json
  predictions.csv
```

## 单例推理

```powershell
python HeadCTLesionDetection/models/hemorrhage/infer.py `
  --input sample_ct.nii.gz `
  --checkpoint HeadCTLesionDetection/models/hemorrhage/runs/hemorrhage_v1/best.pt `
  --device auto
```

返回结构会匹配 `HeadCTLesionDetection` 的 lesion result 单项格式。

### VinBigData CNN-LSTM 单例推理

VinBigData CNN-LSTM adapter 使用三窗输入：

- brain window：center `40`，width `80`
- subdural window：center `80`，width `200`
- bone window：center `600`，width `2800`

运行：

```powershell
python HeadCTLesionDetection/models/hemorrhage/infer.py `
  --provider vinbigdata `
  --input sample_ct.nii.gz `
  --checkpoint HeadCTLesionDetection/models/hemorrhage/external_weights/vinbigdata_cnn_lstm.pt `
  --device auto
```

输出中会额外包含：

```text
provider=vinbigdata
subtype_probabilities.any
subtype_probabilities.epidural
subtype_probabilities.intraparenchymal
subtype_probabilities.intraventricular
subtype_probabilities.subarachnoid
subtype_probabilities.subdural
```

权重兼容说明：

- 优先尝试 `torch.jit.load` 读取 TorchScript 权重。
- 其次尝试读取 `model_state`、`state_dict`、`model` 或纯 state dict。
- 如果 state dict 与本地 CNN-LSTM 架构不兼容，会直接报错，不回落到规则或 mock。

## 分割准备

当前第一阶段是分类模型。如果后续具备出血区域 mask，可使用：

```powershell
python HeadCTLesionDetection/models/hemorrhage/segmentation_prepare.py `
  --labels-csv HeadCTLesionDetection/datasets/hemorrhage/labels.csv `
  --mask-dir HeadCTLesionDetection/datasets/hemorrhage/masks `
  --output-dir D:/nnUNet_raw/Dataset501_Hemorrhage
```

这会生成 nnU-Net 风格目录：

```text
Dataset501_Hemorrhage/
  imagesTr/
  labelsTr/
  imagesTs/
  dataset.json
```

注意：只有具备 voxel 级出血 mask 时才适合做分割。分类标签不能直接用于分割训练。

## nnU-Net v2 分割训练

安装医学影像训练依赖：

```powershell
pip install -r HeadCTLesionDetection/requirements-medimg.txt
```

当前项目已固定 Windows + Python 3.9 可用的 `nnunetv2` 依赖组合。先创建并查看 nnU-Net 工作目录：

```powershell
python HeadCTLesionDetection/models/hemorrhage/train_nnunet.py env
```

默认工作目录在：

```text
D:\exam\nnUNet_raw
D:\exam\nnUNet_preprocessed
D:\exam\nnUNet_results
```

完整流程：

```powershell
# 1. 准备 nnU-Net 风格数据
python HeadCTLesionDetection/models/hemorrhage/segmentation_prepare.py `
  --labels-csv HeadCTLesionDetection/datasets/hemorrhage/labels.csv `
  --mask-dir HeadCTLesionDetection/datasets/hemorrhage/masks `
  --output-dir D:\exam\nnUNet_raw\Dataset501_Hemorrhage `
  --dataset-name Dataset501_Hemorrhage

# 2. 规划和预处理
python HeadCTLesionDetection/models/hemorrhage/train_nnunet.py plan `
  -d 501 `
  --verify-dataset-integrity `
  --configurations 3d_fullres

# 3. 训练 fold 0
python HeadCTLesionDetection/models/hemorrhage/train_nnunet.py train `
  -d 501 `
  -c 3d_fullres `
  -f 0 `
  --device cuda

# 4. 预测
python HeadCTLesionDetection/models/hemorrhage/train_nnunet.py predict `
  -i D:\exam\nnUNet_raw\Dataset501_Hemorrhage\imagesTs `
  -o D:\exam\nnUNet_results\Dataset501_Hemorrhage\predictionsTs `
  -d 501 `
  -c 3d_fullres `
  -f 0 `
  --device cuda
```

可以先加 `--dry-run` 查看实际命令，不启动耗时任务。

## 注意

- 当前是研究/演示模型骨架，不作为最终诊断依据。
- 第一版是 series/study 级分类，不输出病灶位置。
- 不要把金属伪影 mask 当作病灶标签。
- 数据划分必须按 patient/study 级完成，避免数据泄漏。

## 真实成熟权重接入状态

VinBigData MIDL2020 CNN-LSTM 的公开 `best_resnet50.pth` 已按其原始 `baseline_resnet50` 结构接入，而不是再按本地简化 CNN-LSTM 强行加载。当前适配器会识别以下结构：

- 顶层 ResNet block：`layer0`、`layer1`、`layer2`、`layer3`、`layer4`
- 序列解码器：`decoder.recurrent`、`decoder.fc`
- 6 类输出：`any`、`epidural`、`intraparenchymal`、`intraventricular`、`subarachnoid`、`subdural`

若加载的是该 raw checkpoint，推理结果应显示：

```text
provider=vinbigdata
checkpoint_framework=state_dict
checkpoint_fallback_used=false
```

若权重结构不兼容，服务会显式报错或写入 fallback 标记，不应把 fallback 结果伪装成成熟模型结果。
