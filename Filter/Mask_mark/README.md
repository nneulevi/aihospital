# CT 标注掩码生成结果

本目录根据 `agent.md` 要求，使用 `../dataset` 下的 CQ500 DICOM CT 数据批量生成金属伪影标注掩码。

## 复现命令

```powershell
python .\generate_masks.py
```

默认输出到：

```text
output/
```

## 输出结构

每个 DICOM series 会生成一个独立目录：

```text
output/<case>/<series>/
|-- ct_volume.nii.gz
|-- metal_mask.nii.gz
`-- stats.json
```

- `ct_volume.nii.gz`：读取并配准到同一空间信息的原始 CT 体数据
- `metal_mask.nii.gz`：与原始 CT 一一对应的 0/1 标注掩码
- `stats.json`：输入路径、series id、输出路径、滤波参数和各阶段体素统计
- `output/manifest.json`：全量批处理汇总索引

若需要额外保存未压缩 NumPy 文件，可运行：

```powershell
python .\generate_masks.py --save-npy
```

## 本次运行摘要

- 已处理 DICOM series：25
- 失败项：0
- 输出配对文件：25 对 `ct_volume.nii.gz` / `metal_mask.nii.gz`

处理时 SimpleITK 对部分序列提示轻微层间距不均匀，这是 DICOM series 读取阶段的警告；对应输出已正常生成。
