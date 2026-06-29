# Detection 目录总结与复现说明

本文档用于CT 图像中金属伪影区域检测、自动/半自动分割、可视化标注和掩码导出 的桌面工具。
**文档描述模型只做参考，具体看我们自己的模型**

## 1. 目录概览

当前工作区根目录下只有一个主要 Python 包目录：`Detection/`。

```text
Detection/
├── __init__.py
├── CTArtGui.py
├── CTArtifactInfer.py
├── best.pth
├── Run/
│   └── Norm/
│       └── Weights/
└── __pycache__/
    ├── __init__.cpython-310.pyc
    ├── CTArtifactInfer.cpython-310.pyc
    └── CTArtGui.cpython-39.pyc.2232879818480
```

文件与目录说明：

| 路径 | 作用 |
| --- | --- |
| `Detection/CTArtGui.py` | 主 GUI 程序。基于 PySide6 构建 CT 金属伪影掩码标注系统，支持加载 DICOM/MHD/NIfTI/单张图像、阈值法生成掩码、AI 自动分割、三平面浏览、VTK 3D 重建和保存掩码。 |
| `Detection/CTArtifactInfer.py` | AI 推理封装。加载 2D UNet 权重，对 CT 体数据逐 axial 切片推理，并输出 SimpleITK 掩码图像。 |
| `Detection/best.pth` | PyTorch 模型权重文件，约 30.86 MB。可加载为 `collections.OrderedDict`，包含 106 个 tensor key，总参数量约 7,707,471。 |
| `Detection/__init__.py` | 空文件，用于将目录标记为 Python 包。 |
| `Detection/Run/Norm/Weights/` | 空目录，可能是训练或推理历史流程中用于保存归一化权重/模型权重的预留目录。当前没有实际文件。 |
| `Detection/__pycache__/` | Python 字节码缓存，不是源码复现必需内容。 |



## 2. 主要依赖

根据源码导入，复现环境至少需要：

```text
Python
numpy
SimpleITK
torch
PySide6
vtk
```


`Config.py` 中至少应提供：

```python
DEVICE = "cuda"  # 或 "cpu"
```

`UNet2D.py` 中的 `UNet2D` 必须与 `best.pth` 的 state_dict 结构兼容。

## 4. 模型权重信息

`best.pth` 是 PyTorch state_dict：

```text
类型: collections.OrderedDict
key 数量: 106
参数量: 7,707,471
主要模块前缀: d1, d2, d3, d4, up4, up3, up2, u4, u3, u2, out
```

前若干 key 形态：

```text
d1.conv.0.weight: (64, 1, 3, 3)
d1.conv.0.bias: (64,)
d1.conv.1.weight: (64,)
d1.conv.1.bias: (64,)
d2.conv.0.weight: (128, 64, 3, 3)
```

由此可判断该模型是单通道输入、单通道输出的 2D UNet 类结构，编码侧大致为 `64 -> 128 -> 256 -> 512`，解码侧通过 `up4/up3/up2` 和 `u4/u3/u2` 回到输出层 `out`。

## 5. `CTArtifactInfer.py` 实现方法

该文件定义 `CTArtifactInfer` 类，负责 AI 掩码推理。

### 5.1 初始化

```python
infer = CTArtifactInfer(model_weight_path, device=None)
```

逻辑：

1. 如果调用方传入 `device`，使用传入值。
2. 否则使用 `BrainCT.Conf.Config` 中的 `DEVICE`。
3. 创建 `UNet2D()`。
4. 加载 `model_weight_path` 指向的 state_dict。
5. 调用 `model.eval()` 进入推理模式。

### 5.2 单切片推理

入口：

```python
predict_slice(img_slice)
```

处理流程：

1. 将 2D numpy 切片转为 `float32`。
2. 对当前切片做 Z-score 归一化：

```python
img_slice = (img_slice - mean) / (std + 1e-7)
```

3. 构造 PyTorch 输入张量形状：

```text
[1, 1, H, W]
```

4. 前向推理：

```python
output = self.model(tensor)
pred = torch.sigmoid(output)
```

5. 使用 `0.5` 作为阈值二值化，输出 `int16` 掩码。

### 5.3 NIfTI 文件推理

入口：

```python
predict_from_nii(nii_path, save_mask_path=None)
```

处理流程：

1. 用 `sitk.ReadImage` 读取 `.nii` 或 `.nii.gz`。
2. 用 `sitk.GetArrayFromImage` 转为 numpy，形状为 `[D, H, W]`。
3. 对每个 axial 切片 `ct_vol[z]` 调用 `predict_slice`。
4. 将 `mask_vol` 转回 SimpleITK 图像。
5. 调用 `CopyInformation(sitk_ct)` 复制 spacing、origin、direction 等空间信息。
6. 如果传入 `save_mask_path`，则创建输出目录并写出掩码。
7. 返回 `sitk_mask`。

### 5.4 SimpleITK 图像推理

入口：

```python
predict_from_sitk(sitk_ct, save_mask_path=None)
```

逻辑与 `predict_from_nii` 基本一致，但输入已经是 SimpleITK 图像，适合 GUI 内部直接调用，避免重复读写文件。

### 5.5 注意事项

`CTArtifactInfer.py` 中使用了 `torch` 和 `os`，但文件本身没有显式 `import torch`、`import os`。当前代码可能依赖 `from BrainCT.Conf.Config import *` 间接带入这些名字。为了更稳妥复现，建议在该文件顶部显式补充：

```python
import os
import torch
```

## 6. `CTArtGui.py` 实现方法

该文件是完整桌面 GUI 主程序，入口位于文件末尾：

```python
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ArtifactAnnotationWindow()
    win.show()
    sys.exit(app.exec())
```

### 6.1 GUI 总体结构

主窗口类：

```python
class ArtifactAnnotationWindow(QMainWindow)
```

窗口标题：

```text
CT金属伪影掩码标注系统 - 支持DICOM/MHD/NIfTI + VTK 3D视图 + AI自动分割
```

窗口尺寸：

```text
1600 x 900
```

主界面分为左右两部分：

1. 左侧控制面板，宽度 340。
2. 右侧显示区，包含 axial、coronal、sagittal 三平面切片视图，以及一个 VTK 3D CT 重建视图。

### 6.2 核心状态变量

```python
self.ct_image       # SimpleITK CT 图像
self.artifact_mask  # SimpleITK 掩码图像
self.volume_np      # numpy CT 体数据, shape [D, H, W]
self.mask_np        # numpy 掩码体数据, shape [D, H, W]

self.slice_axial
self.slice_coronal
self.slice_sagittal
```

AI 推理器在窗口初始化时创建：

```python
self.infer = CTArtifactInfer(model_weight_path="best.pth")
```

注意：这里的 `best.pth` 是相对路径。实际运行时，当前工作目录必须能直接找到 `best.pth`，或者应改成基于 `__file__` 的绝对路径。

### 6.3 异步任务封装

GUI 使用两个辅助类：

```python
class ProgressDialog(QDialog)
class Worker(QThread)
```

作用：

1. 长耗时任务放进 `QThread`，避免卡死 UI。
2. 通过 `progress = Signal(int, str)` 更新进度条与文本。
3. 任务结束后统一调用：

```python
self.refresh_all_views()
self.update_all_slice_labels()
self.render_3d_ct()
```

涉及异步的操作包括：

```text
加载 DICOM
加载 MHD
加载 NIfTI
加载单张图像
加载掩码
传统阈值法生成掩码
AI 自动分割
保存掩码
```

### 6.4 支持的数据加载方式

#### DICOM 序列

入口：

```python
load_dicom_async()
_load_dicom_task(report, folder)
```

实现：

```python
reader = sitk.ImageSeriesReader()
fns = reader.GetGDCMSeriesFileNames(folder)
reader.SetFileNames(fns)
img = reader.Execute()
vol = sitk.GetArrayFromImage(img)
```

#### MHD/RAW

入口：

```python
load_mhd_async()
_load_mhd_task(report, path)
```

实现：

```python
img = sitk.ReadImage(path)
vol = sitk.GetArrayFromImage(img)
```

#### NIfTI

入口：

```python
load_nifti_async()
_load_nifti_task(report, path)
```

支持：

```text
.nii
.nii.gz
```

#### 单张图像

入口：

```python
load_single_async()
_load_single_task(report, path)
```

支持：

```text
.dcm
.png
.jpg
.nii
.mhd
```

如果读入结果是二维图像，会扩展为一层体数据：

```python
vol = vol[None]
img = sitk.GetImageFromArray(vol)
```

#### 外部掩码

入口：

```python
load_mask_async()
_load_mask_task(report, path)
```

要求：

1. 必须先加载 CT。
2. 掩码尺寸必须与 CT 的 `GetSize()` 完全一致。
3. 掩码读入后会转为二值：

```python
self.mask_np = (mask_np > 0).astype(np.uint8)
```

### 6.5 传统规则法掩码生成

入口：

```python
generate_mask_async()
_generate_mask_task(report)
```

用户可调参数：

| 参数 | 控件范围 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `th_low` | 300-1500 | 600 | CT 强度阈值下限 |
| `th_high` | 2000-4000 | 2800 | CT 强度阈值上限 |
| `grad_th` | 50-500 | 100 | 梯度幅值阈值 |
| `open_r` | 0-5 | 1 | 形态学开运算半径 |
| `close_r` | 0-10 | 2 | 形态学闭运算半径 |
| `min_area` | 10-500 | 40 | 连通域最小像素数 |

算法流程：

1. CT 强度阈值分割：

```python
mask = sitk.BinaryThreshold(img, tl, th, 1, 0)
```

2. 梯度幅值计算：

```python
g = sitk.GradientMagnitude(sitk.Cast(img, sitk.sitkFloat32))
gmask = sitk.BinaryThreshold(g, gg, 99999, 1, 0)
```

3. 强度掩码与梯度掩码求交：

```python
comb = sitk.And(mask, gmask)
```

4. 三维形态学开运算：

```python
comb = sitk.BinaryMorphologicalOpening(comb, [ro, ro, ro])
```

5. 三维形态学闭运算：

```python
comb = sitk.BinaryMorphologicalClosing(comb, [rc, rc, rc])
```

6. 连通域分析：

```python
cc = sitk.ConnectedComponent(comb)
stats = sitk.LabelShapeStatisticsImageFilter()
stats.Execute(cc)
```

7. 过滤小连通域，生成最终 `sitkUInt8` 掩码。

滑动条变化后会启动 300 ms 单次定时器，自动重新生成掩码。

### 6.6 AI 自动分割

入口：

```python
ai_segment_async()
_ai_segment_task(report)
```

流程：

1. 检查是否已加载 CT。
2. 调用：

```python
sitk_mask = self.infer.predict_from_sitk(self.ct_image)
```

3. 将结果保存到：

```python
self.artifact_mask = sitk_mask
self.mask_np = sitk.GetArrayFromImage(sitk_mask)
```

4. 刷新三平面视图和 3D 视图。

AI 按钮初始禁用，加载 CT 后启用。

### 6.7 三平面显示

显示函数：

```python
update_view_axial()
update_view_coronal()
update_view_sagittal()
```

取片方式：

```python
axial:    self.volume_np[self.slice_axial]
coronal:  self.volume_np[:, self.slice_coronal, :]
sagittal: self.volume_np[:, :, self.slice_sagittal]
```

绘制方法：

```python
draw_slice(im, mk)
```

处理逻辑：

1. 将 CT 值裁剪到 `[-500, 1500]`。
2. 归一化到 `0-255`。
3. 转为 RGB。
4. 掩码区域覆盖为红色 `[255, 80, 80]`。
5. 转为 `QPixmap` 并等比例缩放到最大 `500 x 500`。

### 6.8 三平面滑动同步

入口：

```python
on_slice_change(vt, v)
```

逻辑：

1. 用户拖动一个方向的滑动条。
2. 按比例映射另外两个方向的切片索引。
3. 使用 `np.clip` 限制索引范围。
4. 用 `blockSignals(True/False)` 避免递归触发。
5. 刷新三平面图像与标签。

### 6.9 VTK 3D 重建

初始化：

```python
init_vtk_3d_view()
```

使用：

```python
QVTKRenderWindowInteractor
vtkRenderer
```

CT 表面重建：

```python
contour = vtk.vtkMarchingCubes()
contour.SetValue(0, 200)
```

掩码 3D 显示：

```python
mask_contour = vtk.vtkMarchingCubes()
mask_contour.SetValue(0, 0.5)
```

显示风格：

1. CT 表面为浅灰白色。
2. 掩码为红色，透明度 0.6。
3. 每次刷新前调用 `RemoveAllViewProps()` 清空旧 actor。

### 6.10 掩码保存

入口：

```python
save_mask_async()
_save_mask_task(report, path)
```

支持保存为：

```text
.nii
.nii.gz
```

实现：

```python
sitk.WriteImage(self.artifact_mask, path)
```

如果目标文件已存在，会弹窗询问是否覆盖。


## 7. 命令行推理复现示例

如果只复现 AI 分割，不启动 GUI，可以使用：

```python
from BrainCT.Detection.CTArtifactInfer import CTArtifactInfer

infer = CTArtifactInfer(model_weight_path="BrainCT/Detection/best.pth", device="cpu")
mask = infer.predict_from_nii(
    nii_path="input_ct.nii.gz",
    save_mask_path="artifact_mask.nii.gz",
)
```

输出 `mask` 是 SimpleITK 图像，并且会复制输入 CT 的空间信息。


## 8. 语法与权重核对结果

已使用 UTF-8 读取源码，中文注释和界面文本正常。

源码语法通过以下无写入方式检查：

```powershell
python -c "import pathlib; [compile(pathlib.Path(p).read_text(encoding='utf-8'), p, 'exec') for p in ['Detection/CTArtGui.py','Detection/CTArtifactInfer.py']]; print('syntax ok')"
```

结果：

```text
syntax ok
```

权重文件可被 PyTorch 加载为 state_dict。加载权重时 PyTorch 输出了关于 `torch.load(..., weights_only=False)` 的安全提示，属于 PyTorch 反序列化安全提醒，不代表权重损坏。

## 9. 给后续的复现路径
1. 分别验证：

```text
三平面显示
传统阈值法生成掩码
AI 自动分割
VTK 3D 重建
NIfTI 掩码保存
```

