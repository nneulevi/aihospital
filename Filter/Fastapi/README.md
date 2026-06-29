# CT 金属伪影检测 FastAPI 微服务

本目录实现 NIfTI CT 上传、3D/2D U-Net 推理、结构化结果落盘、三平面预览图和结果下载接口。

## 安装依赖

```powershell
pip install -r Filter/Fastapi/requirements.txt
```

依赖覆盖：

- `fastapi`: Web API 服务框架。
- `uvicorn[standard]`: ASGI 服务启动器。
- `python-multipart`: 支持 NIfTI 文件上传接口。
- `SimpleITK`: 读取/写出 `.nii/.nii.gz` CT 和 mask。
- `torch`: 加载 3D U-Net 模型并推理。
- `numpy`: 体数据数组处理。
- `pyinstaller`: 可选，用于打包 exe。

如果需要 CUDA 版 PyTorch，建议按本机 CUDA 版本从 PyTorch 官方命令单独安装 `torch`，
再安装本文件中的其他依赖。

## 启动服务

默认模型权重：

```text
Filter/model/runs/metal_unet3d/best_unet3d_metal.pt
```

启动：

```powershell
python Filter/Fastapi/CTDetectionServer.py
```

UNet2D 备份服务：

```powershell
python Filter/Fastapi/CTDetectionServer_unet2d.py
```

默认监听端口：

```text
3D 主服务: http://localhost:8000
2D 备份服务: http://localhost:8001
```

访问：

```text
http://localhost:8000
http://localhost:8000/ui
http://localhost:8000/docs
```

Web 前端入口：

```text
3D 主服务界面: http://localhost:8000/ui
2D 备份服务界面: http://localhost:8001/ui
```

## 接口

推荐使用平台契约接口：

- `GET /api/ct-artifact/health`: 服务、模型、版本和目录状态。
- `POST /api/ct-artifact/detect`: 上传 `.nii` 或 `.nii.gz` CT 文件并生成结构化结果。
- `POST /api/ct-artifact/tasks`: 上传 `.nii` 或 `.nii.gz` CT 文件并创建后台推理任务。
- `GET /api/ct-artifact/tasks/{task_id}`: 查询任务状态。
- `GET /api/ct-artifact/results/{request_id}`: 获取本次推理的 `result.json`。
- `GET /api/ct-artifact/files/{request_id}/{file_name}`: 下载 `mask.nii.gz`、`result.json` 或预览 PNG。

兼容旧接口：

- `GET /health`
- `POST /predict-ct-artifact`
- `GET /results/{mask_filename}`

一次推理会生成：

```text
Filter/filter_outputs/
  {request_id}/
    task.json
    mask.nii.gz
    result.json
    preview_axial.png
    preview_coronal.png
    preview_sagittal.png
```

2D 备份服务默认写入：

```text
Filter/filter_outputs_2d/
```

核心返回字段包括：

- `artifact_detected`
- `artifact_ratio`
- `severity`
- `affected_slices`
- `model_name`
- `model_version`
- `backend`
- `threshold`
- `elapsed_ms`
- `report_suggestion`
- `input_metadata`
- `download_url`
- `result_url`
- `preview_urls`

任务式接口返回示例：

```json
{
  "status": "queued",
  "task_id": "xxx",
  "task_url": "/api/ct-artifact/tasks/xxx",
  "result_url": "/api/ct-artifact/results/xxx",
  "mask_url": "/api/ct-artifact/files/xxx/mask.nii.gz"
}
```

任务状态包括：

- `queued`
- `running`
- `success`
- `failed`

## 环境变量

可选配置：

```powershell
$env:CT_MODEL_WEIGHT_PATH="D:\exam\Filter\model\runs\metal_unet3d\best_unet3d_metal.pt"
$env:CT_SERVER_DEVICE="cpu"
$env:CT_MODEL_NAME="metal_unet3d"
$env:CT_MODEL_VERSION="v1.0.0"
$env:CT_SERVER_PATCH_SIZE="32,128,128"
$env:CT_SERVER_OVERLAP="0.5"
$env:CT_SERVER_THRESHOLD="0.35"
$env:CT_UPLOAD_DIR="D:\exam\Filter\Fastapi\uploads"
$env:CT_OUTPUT_ROOT="D:\exam\Filter\filter_outputs"
```

UNet2D 备份服务可使用：

```powershell
$env:CT_MODEL_WEIGHT_PATH="D:\exam\Filter\model\UNet2D方案\runs\unet2d\best_unet2d_metal.pt"
```

## 前端对接

本目录已内置静态前端：

```text
frontend/index.html
frontend/styles.css
frontend/app.js
```

页面功能：

- 检查服务健康状态。
- 选择当前服务、3D 主服务或 2D 备份服务。
- 上传 `.nii/.nii.gz` CT 文件。
- 展示检测结果、阳性体素、伪影比例、严重程度、耗时、尺寸、spacing 和结果文件名。
- 展示 axial / coronal / sagittal 三平面预览图。
- 下载生成的 mask。

Vue / axios 示例：

```js
const form = new FormData()
form.append("file", file)
const res = await axios.post("http://localhost:8000/api/ct-artifact/detect", form)
const downloadUrl = "http://localhost:8000" + res.data.download_url
```

返回中的 `download_url` 是相对路径，浏览器下载时需要拼接服务域名。

## Smoke Test

```powershell
python -m pytest Filter/Fastapi/tests/test_ct_artifact_api.py
```

测试覆盖：

- `/api/ct-artifact/health`
- `/api/ct-artifact/detect`
- `/api/ct-artifact/tasks`
- `/api/ct-artifact/tasks/{task_id}`
- `/api/ct-artifact/results/{request_id}`
- `/api/ct-artifact/files/{request_id}/mask.nii.gz`
- 三平面预览 PNG 下载
