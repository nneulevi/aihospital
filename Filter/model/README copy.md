# BrainCT 项目训练说明

## 目标

为 agent 提供可复现的模型训练和优化说明。本文档覆盖数据结构、训练流程、超参数、模型、损失函数和评价指标，便于直接实现或改进训练管道。

## 目录结构与职责

### 根目录
- `Main.py`：主入口，搭建训练流程，加载数据、构建模型、训练、保存权重、生成可视化。
- `Split3D2Dcm.py`：将 3D DICOM 数据拆分为 2D 切片。

### `Conf/`
- `Config.py`：全局训练配置和路径定义。

### `Datasets/`
- `Datasets.py`：`CTSliceDataset` 数据集类。
- `CT/`：原始 CT DICOM 切片。
- `MASK/`：对应分割标签 DICOM 切片。

### `Loss/`
- `Losses.py`：自定义混合损失函数 `DiceCELoss`。

### `Model/`
- `UNet2D.py`：2D U-Net 结构（备用）。
- `AttentionUNet2D.py`：当前实际使用的注意力 U-Net 模型。

### `Trainer/`
- `UNet2DTrainer.py`：训练器 `Trainer`，包含训练/验证循环、指标计算、模型保存、学习率调度。

### `Utils/`
- `EvalMetrics.py`：`MetricCalculator`，计算精度、召回、Dice 和准确率。

### `Vision/`
- `MeticsVisualizer.py`：训练曲线、混淆矩阵、预测可视化输出。

### `run/`
- 保存训练结果与图像输出，如 `loss_curve.png`、`acc_curve.png`、`confusion.png`、`pred_sample.png`。
- `weights/best.pth`：最优模型权重保存位置。

## 关键训练流程

### 数据加载

`Main.py`:
- 构建 `CTSliceDataset(CT_PATH, MASK_PATH)`。
- 使用 `random_split` 按 `VAL_SPLIT` 划分训练/验证集。
- 将 `train_ds.dataset.is_train = True` 打开训练增强，`val_ds.dataset.is_train = False` 关闭增强。
- DataLoader:
  - 训练：`batch_size=BATCH_SIZE`，`shuffle=True`
  - 验证：`batch_size=BATCH_SIZE`，`shuffle=False`

### 数据集处理逻辑

`CTSliceDataset`:
- 从 `ct_root` 读取以 `.dcm` 后缀的文件名，并匹配对应 `mask_root`。
- 读取 DICOM 后使用 `pydicom.dcmread`，转换为 `np.float32`。
- CT 图像标准化：`(x - mean) / (std + 1e-7)`。
- MASK 二值化：`mask > 0`。
- 生成张量且增加通道维度：`[1, H, W]`。
- 数据增强（仅训练）:
  - 随机水平翻转
  - 随机垂直翻转
  - 随机旋转角度 `[-10, 10]`

### 模型与优化

`Main.py`:
- 当前模型：`AttentionUNet2D()`。
- 损失函数：`DiceCELoss()`。
- 优化器：`AdamW(model.parameters(), lr=LR, weight_decay=1e-5)`。
- 学习率调度器：`CosineAnnealingLR(optimizer, T_max=EPOCHS)`。
- 最优权重保存路径：`./run/weights/best.pth`。

### 训练器逻辑

`Trainer.UNet2DTrainer.Trainer`:
- `train_one_epoch`:
  - model.train()
  - 前向 + 反向 + `optimizer.step()`
  - 返回平均训练 loss
- `val_one_epoch`:
  - model.eval()
  - `@torch.no_grad()`
  - 计算验证 loss 和指标
  - 返回：`val_loss, precision, recall, dice, accuracy`
- `Train`:
  - 执行 `epochs` 次训练
  - 每轮更新 `scheduler.step()`（如果有）
  - 保存 `history`
  - 当当前 `dice` 超过 `best_dice` 时保存模型权重

## 损失与指标

### 损失函数 `DiceCELoss`

- 组合 `BCEWithLogitsLoss` 和 Dice Loss：`0.5 * BCE + 0.5 * Dice`。
- 使用 `pos_weight=20.0` 强化正例。
- 通过 `torch.sigmoid(pred)` 计算 Dice。

### 评价指标

`MetricCalculator.calculate_metrics(pred, target)` 计算：
- Precision
- Recall
- Dice
- Accuracy

使用阈值 `0.5` 进行二值化预测。

## 可视化输出

`Visualizer`:
- `plot_all_curves(history)`:
  - 训练/验证 loss 曲线
  - 准确率曲线
  - Precision/Recall 曲线
  - Dice/F1 曲线
- `plot_confusion(model, loader, device)`:
  - 导出规范化混淆矩阵
- `plot_sample_pred(model, dataset, device)`:
  - 导出一张 `CT / GT / Prediction` 结果图

## 关键超参数

配置文件 `Conf/Config.py` 中的当前值：
- `DEVICE = "cuda" if torch.cuda.is_available() else "cpu"`
- `BATCH_SIZE = 2`
- `EPOCHS = 5`
- `LEARNING_RATE = 1e-4`
- `VAL_SPLIT = 0.2`
- `LR = 1e-4`

## 训练复现步骤

1. 确保工作目录结构为：
   - `Conf/Config.py`
   - `Datasets/CT/`
   - `Datasets/MASK/`
   - `Model/`
   - `Trainer/`
   - `Loss/`
2. 将训练数据放到 `datasets/CT` 和 `datasets/MASK` 下，文件名需一一对应。
3. 安装依赖：`torch`, `torchvision`, `pydicom`, `numpy`, `matplotlib`, `scikit-learn`。
4. 运行：
   ```bash
   python Main.py
   ```
5. 训练结果与可视化输出会保存在 `run/` 下。

## 可优化点建议

1. 数据增强
   - 加入随机裁剪、弹性变形、伪彩色增强、噪声
   - 采用更强的几何变换和强度变换
2. 模型架构
   - 比较 `UNet2D` 与 `AttentionUNet2D`
   - 尝试深层 U-Net、ResUNet、TransUNet、Swin-UNet
3. 损失函数
   - 试验 `DiceLoss`, `FocalLoss`, `TverskyLoss`, `ComboLoss`
4. 优化器与调度
   - 试验 `AdamW`, `SGD + momentum`, `Ranger`
   - 使用 `ReduceLROnPlateau`, `CosineAnnealingWarmRestarts`, `OneCycleLR`
5. 验证与保存
   - 用更大验证集或交叉验证
   - 保存每轮 checkpoint，并记录最优 Dice
6. 指标提升
   - 使用阈值搜索、滑动窗口预测、测试时增强（TTA）
   - 监控 `precision/recall/dice` 的趋势，避免过拟合

## 说明

本文件重点描述当前项目的训练实现细节，适合 agent 直接依据当前代码结构实现训练逻辑、搜索超参数或进行模型改进。