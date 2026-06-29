# Filter 下一步任务指导：任务式推理与平台接入

## 1. 当前状态判断

根据 `Filter完整子模块交付评估与后续工作指导.md` 的整体项目布局，Filter 模块在平台中的定位应为：

```text
头部 CT 影像质控与金属伪影识别子模块
```

它不是完整头部 CT 诊断系统，也不直接生成最终医学结论。它应为上层智慧云脑诊疗平台、AI 报告模块、医生审核模块提供稳定的影像质控结果。

当前已完成的 MVP/P0 能力包括：

- 3D U-Net 主服务。
- 2D U-Net 备份服务。
- `/api/ct-artifact/health` 健康检查。
- `/api/ct-artifact/detect` 同步推理接口。
- `/api/ct-artifact/results/{request_id}` 结果 JSON 查询。
- `/api/ct-artifact/files/{request_id}/{file_name}` mask / 预览图下载。
- 统一结构化结果字段。
- `artifact_ratio`、`severity`、`affected_slices`。
- `model_name`、`model_version`、`backend`。
- `elapsed_ms`、`error_code`。
- `filter_outputs/{request_id}` 结果落盘。
- `mask.nii.gz`、`result.json`、三平面 PNG 预览图。
- 基础前端页面已对接新接口。
- smoke test 已覆盖 3D / 2D 基础链路。

### P1 当前完成进展

已继续补齐任务式推理的第一版工程实现：

- 新增 `/api/ct-artifact/tasks`。
- 新增 `/api/ct-artifact/tasks/{task_id}`。
- 新增本地 `task.json` 任务状态落盘。
- 任务状态支持 `queued`、`running`、`success`、`failed`。
- 3D 主服务和 2D 备份服务均已接入任务式推理。
- 前端已支持“任务式推理 / 同步推理”两种调用方式。
- smoke test 已覆盖任务创建、任务查询、result.json 获取、mask 下载、预览图下载。

因此，当前最合理的下一步不是继续扩展诊断模型，而是先围绕任务式接口做平台对接验证；任务式链路稳定后，再进入 DICOM 对接和医生审核闭环。

## 2. 下一步优先级

下一阶段建议优先做：

```text
P1：增加任务式推理机制
```

目标是让主系统上传 CT 后立即获得 `task_id`，后续通过查询任务状态和结果完成异步对接，避免大体积 CT 推理阻塞 HTTP 请求。

推荐接口：

```text
POST /api/ct-artifact/tasks
GET  /api/ct-artifact/tasks/{task_id}
GET  /api/ct-artifact/results/{task_id}
GET  /api/ct-artifact/files/{task_id}/{file_name}
```

保留现有同步接口：

```text
POST /api/ct-artifact/detect
```

同步接口适合演示、调试和小文件快速验证；任务式接口适合平台正式集成。

## 3. 任务式推理设计

### 3.1 任务状态

任务状态建议统一为：

```text
queued
running
success
failed
```

状态含义：

- `queued`：文件已上传，等待推理。
- `running`：模型正在推理。
- `success`：推理完成，结果已落盘。
- `failed`：推理失败，可读取错误码和错误信息。

### 3.2 任务目录结构

建议沿用当前结果结构，不新增混乱目录：

```text
Filter/
  filter_outputs/
    {task_id}/
      input.nii.gz
      task.json
      result.json
      mask.nii.gz
      preview_axial.png
      preview_coronal.png
      preview_sagittal.png
```

2D 备份服务可继续使用：

```text
Filter/
  filter_outputs_2d/
    {task_id}/
      input.nii.gz
      task.json
      result.json
      mask.nii.gz
      preview_axial.png
      preview_coronal.png
      preview_sagittal.png
```

### 3.3 task.json 推荐结构

```json
{
  "task_id": "xxx",
  "request_id": "xxx",
  "status": "running",
  "module": "ct_artifact_filter",
  "backend": "unet3d",
  "created_at": "2026-06-11T10:00:00",
  "started_at": "2026-06-11T10:00:01",
  "finished_at": null,
  "elapsed_ms": null,
  "input_file": "input.nii.gz",
  "result_file": "result.json",
  "error_code": null,
  "error_message": null
}
```

任务完成后：

```json
{
  "task_id": "xxx",
  "status": "success",
  "finished_at": "2026-06-11T10:00:12",
  "elapsed_ms": 11234,
  "result_url": "/api/ct-artifact/results/xxx",
  "mask_url": "/api/ct-artifact/files/xxx/mask.nii.gz"
}
```

失败时：

```json
{
  "task_id": "xxx",
  "status": "failed",
  "error_code": "INFERENCE_FAILED",
  "error_message": "服务处理失败: ..."
}
```

## 4. 建议实现顺序

### Step 1：抽取同步推理核心函数

当前 `/api/ct-artifact/detect` 已完成上传、推理、结构化结果生成。

下一步应将核心逻辑整理为可复用函数：

```text
输入：task_id、input_path、output_dir、original_filename
输出：result.json 对应 dict
```

这样同步接口和任务接口都可以复用同一套推理逻辑，避免 3D / 2D / 同步 / 异步四套逻辑分叉。

### Step 2：增加任务注册与状态落盘

新增轻量任务工具模块，例如：

```text
Fastapi/task_store.py
```

职责：

- 创建任务目录。
- 写入 `task.json`。
- 更新状态。
- 读取任务状态。
- 处理异常状态。

第一阶段可以使用本地 JSON 文件，不必立即引入数据库或 Redis。

### Step 3：实现任务接口

新增：

```text
POST /api/ct-artifact/tasks
GET  /api/ct-artifact/tasks/{task_id}
```

`POST /tasks` 行为：

1. 校验上传文件。
2. 保存为 `{task_id}/input.nii.gz`。
3. 写入 `task.json`，状态为 `queued`。
4. 提交后台任务。
5. 立即返回 `task_id`。

返回示例：

```json
{
  "status": "queued",
  "task_id": "xxx",
  "task_url": "/api/ct-artifact/tasks/xxx",
  "result_url": "/api/ct-artifact/results/xxx"
}
```

`GET /tasks/{task_id}` 行为：

1. 读取 `{task_id}/task.json`。
2. 返回当前状态。
3. 如果成功，返回 `result_url` 和 `mask_url`。

### Step 4：后台执行方式

第一阶段建议使用 FastAPI 内置 `BackgroundTasks`：

```text
fastapi.BackgroundTasks
```

优点：

- 不需要安装新依赖。
- 适合本地 MVP。
- 能快速打通平台任务式调用。

限制：

- 不适合多进程、多实例、服务重启后恢复任务。
- 不适合生产级队列。

后续如果需要生产化，再升级为：

```text
Redis Queue / Celery / Dramatiq / RabbitMQ
```

当前阶段先不要过度设计。

### Step 5：补 smoke test

新增测试：

```text
POST /api/ct-artifact/tasks
GET  /api/ct-artifact/tasks/{task_id}
GET  /api/ct-artifact/results/{task_id}
GET  /api/ct-artifact/files/{task_id}/mask.nii.gz
```

验收逻辑：

1. 上传 smoke NIfTI。
2. 立即获得 `task_id`。
3. 轮询任务状态，直到 `success` 或 `failed`。
4. `success` 后读取 `result.json`。
5. 下载 mask 和 PNG 预览图。

测试时不需要启动 uvicorn 服务，继续使用 `TestClient`。

## 5. 平台接入关系

在整体项目布局中，Filter 应作为被调用的算法子模块。

推荐调用链：

```text
主平台 / Spring Boot
  -> 上传 CT 到 Filter /api/ct-artifact/tasks
  -> 获得 task_id
  -> 查询 Filter /api/ct-artifact/tasks/{task_id}
  -> 读取 result.json
  -> 保存 mask / preview / report_suggestion
  -> 将 report_suggestion 合并进 AI 检查报告草稿
  -> 医生端审核
```

Filter 输出给主平台的关键字段：

- `task_id`
- `request_id`
- `status`
- `artifact_detected`
- `artifact_ratio`
- `severity`
- `affected_slices`
- `model_name`
- `model_version`
- `backend`
- `threshold`
- `elapsed_ms`
- `download_url`
- `preview_urls`
- `report_suggestion`
- `input_metadata`
- `error_code`

## 6. 不建议下一步做什么

暂时不建议优先做：

- 新增脑出血、脑梗、骨折等诊断模型。
- 大规模重构现有 3D / 2D 模型目录。
- 直接引入复杂任务队列。
- 直接做数据库审计系统。
- 直接承诺生产级医疗诊断能力。

原因是当前模块的核心瓶颈不是模型种类，而是平台级调用闭环、任务状态、审计结果和医生审核链路。

## 7. P1 验收标准

P1 完成后，至少应满足：

- 主平台上传一例 `.nii/.nii.gz` 后能立即拿到 `task_id`。
- 任务状态可查询。
- 任务成功后能读取完整 `result.json`。
- 任务成功后能下载 `mask.nii.gz`。
- 任务成功后能下载三平面 PNG 预览图。
- 任务失败时能返回稳定 `error_code` 和 `error_message`。
- 3D 主服务和 2D 备份服务接口字段一致。
- smoke test 覆盖任务式推理链路。

## 8. P1 之后的路线

P1 完成后，再进入：

```text
P2：DICOM 对接能力
```

重点：

- 支持 DICOM zip。
- 支持 DICOM Series 转 NIfTI。
- 结果写入 StudyInstanceUID、SeriesInstanceUID。
- 将 DICOM 元数据合并到 `input_metadata`。

然后进入：

```text
P3：医生审核闭环
```

重点：

- 医生修正 mask 回传。
- 保存 `review.json`。
- 区分 AI mask 与 reviewed mask。
- 记录审核医生、审核时间、审核结论。

## 9. 推荐下一次开发任务

下一次建议直接执行：

```text
为 3D 和 2D FastAPI 服务增加 /api/ct-artifact/tasks 任务式推理接口，并补充 task.json 落盘和 smoke test。
```

这是当前最符合整体项目布局、也最能推动 Filter 从演示原型走向平台可交付子模块的一步。
