# U-Net2D 方案

这是独立于现有 3D U-Net 的 2D baseline/fallback 方案，不调整上级目录中的现有结构。

## 数据

默认读取：

```text
../datasets/CT
../datasets/mask
```

两边按同名 NIfTI 文件配对，例如：

```text
CT/000_CT.nii.gz
mask/000_CT.nii.gz
```

训练时会把 3D 体数据拆成 axial 2D 切片。含标注的切片全部保留，空切片按
`--keep-empty-fraction` 抽样保留，避免负样本淹没小目标。

## 训练

快速 smoke：

```powershell
python Filter/model/UNet2D方案/train_unet2d.py --epochs 1 --batch-size 2 --base-channels 8 --size 128,128 --device cpu
```

正式训练参考：

```powershell
python Filter/model/UNet2D方案/train_unet2d.py --epochs 100 --batch-size 4 --accum-steps 2 --lr 1e-4 --base-channels 64
```

## 速度优化

训练脚本默认做了几项不改变训练功能的加速：

- `pos_weight` 直接从 mask 统计，不再完整遍历 `Dataset` 加载 CT。
- `CTArtifactSliceDataset` 会缓存最近读取的体数据，默认 `--cache-items 16`。
- CUDA 训练时 DataLoader 自动启用 `pin_memory`，tensor 拷贝使用 non-blocking。
- `--num-workers > 0` 时启用 `persistent_workers` 和预取，减少 worker 重建与等待开销。
- 验证阶段使用 `torch.inference_mode()`。
- checkpoint 中写入 optimizer 与 scheduler 状态，便于后续扩展断点恢复。

常用加速参数：

```powershell
python Filter/model/UNet2D方案/train_unet2d.py --epochs 100 --batch-size 8 --size 256,256 --num-workers 2 --cache-items 16
```

显存或内存不足时：

```powershell
python Filter/model/UNet2D方案/train_unet2d.py --batch-size 2 --accum-steps 4 --cache-items 4
```

输出：

```text
runs/unet2d/best_unet2d_metal.pt
runs/unet2d/last_unet2d_metal.pt
runs/unet2d/metrics.json
```

## 推理

```powershell
python Filter/model/UNet2D方案/predict_unet2d.py --checkpoint Filter/model/UNet2D方案/runs/unet2d/best_unet2d_metal.pt --input path/to/ct.nii.gz --output path/to/pred_mask.nii.gz
```

## 与 3D U-Net 的定位

- 2D U-Net：训练更快、显存占用低，适合作 baseline 或 GUI 快速 fallback。
- 3D U-Net：利用层间空间上下文，理论上更适合最终体素级金属伪影分割。
