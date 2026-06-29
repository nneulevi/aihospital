# 阶段 H：三服务真实模型模式联调详细指导

更新时间：2026-06-12

## 1. 阶段目标

阶段 H 的目标是把已经完成的服务链路从“mock/骨架可运行”推进到“真实 checkpoint 参与推理的完整联调”。

目标链路：

```text
主平台 / 测试客户端
  -> HeadCTOrchestrator
  -> Filter 金属伪影质控服务
  -> HeadCTLesionDetection 真实病灶模型模式
  -> HeadCTOrchestrator 汇总 quality_control + lesion_analysis + report_assist
```

本阶段重点验证：

- 三个服务都能独立启动。
- Orchestrator 能稳定调用 Filter。
- Orchestrator 能在 `LESION_SERVICE_ENABLED=true` 时调用 LesionDetection。
- LesionDetection 能以 `LESION_MODE=model` 加载真实 checkpoint。
- `orchestrator_result.json` 中的 `pipeline.lesion_analysis` 为 `success`。
- Filter 或 LesionDetection 任一服务异常时，Orchestrator 能返回稳定错误码。

## 2. 前置条件

### 2.1 必须完成

```text
Filter/Fastapi/CTDetectionServer.py                      已完成
HeadCTLesionDetection/LesionDetectionServer.py            已完成
HeadCTLesionDetection/models/hemorrhage/infer.py          已完成
HeadCTOrchestrator/OrchestratorServer.py                  已完成
HeadCTOrchestrator/service_clients/filter_client.py       已完成
HeadCTOrchestrator/service_clients/lesion_client.py       已完成
```

### 2.2 真实模型文件

正式联调需要：

```text
HeadCTLesionDetection/models/hemorrhage/runs/hemorrhage_v1/best.pt
```

如果暂时没有真实训练得到的 `best.pt`，可以用临时 checkpoint 做“链路技术联调”，但不能作为模型质量验收。

区别：

| checkpoint 类型 | 可用于链路联调 | 可用于模型验收 |
| --- | --- | --- |
| 临时随机权重 checkpoint | 是 | 否 |
| 真实训练 checkpoint | 是 | 是 |

### 2.3 跳过正式训练时的 smoke checkpoint

如果暂时略过“训练并评估第一个真实 checkpoint”，可以先生成随机权重 checkpoint，只验证 model 模式加载、推理接口和三服务调用链路：

```powershell
python HeadCTLesionDetection/models/hemorrhage/create_smoke_checkpoint.py `
  --output HeadCTLesionDetection/models/hemorrhage/runs/hemorrhage_v1/smoke_best.pt `
  --base-channels 2 `
  --input-shape 16,64,64
```

然后启动 LesionDetection：

```powershell
$env:LESION_MODE="model"
$env:HEMORRHAGE_CHECKPOINT="D:\exam\HeadCTLesionDetection\models\hemorrhage\runs\hemorrhage_v1\smoke_best.pt"
$env:HEMORRHAGE_DEVICE="cpu"
python HeadCTLesionDetection/LesionDetectionServer.py
```

注意：

- `smoke_best.pt` 只用于阶段 H 技术联调。
- `smoke_best.pt` 不能用于模型质量评估、论文指标或临床结论。
- 真实模型完成后，应改回真实训练得到的 `best.pt`。

## 3. 推荐目录

```text
D:\exam\
  Filter\
    Fastapi\
      CTDetectionServer.py
  HeadCTLesionDetection\
    LesionDetectionServer.py
    models\
      hemorrhage\
        runs\
          hemorrhage_v1\
            best.pt
  HeadCTOrchestrator\
    OrchestratorServer.py
    orchestrator_outputs\
```

## 4. 服务端口规划

| 服务 | 默认端口 | 健康检查 |
| --- | --- | --- |
| Filter | `8000` | `GET http://localhost:8000/api/ct-artifact/health` |
| LesionDetection | `8020` | `GET http://localhost:8020/api/head-ct-lesion/health` |
| Orchestrator | `8010` | `GET http://localhost:8010/api/head-ct-ai/health` |

如果端口冲突，优先通过环境变量调整：

```powershell
$env:FILTER_PORT="8001"
$env:LESION_PORT="8021"
$env:ORCH_PORT="8011"
```

同时更新 Orchestrator 的服务地址：

```powershell
$env:FILTER_BASE_URL="http://localhost:8001"
$env:LESION_BASE_URL="http://localhost:8021"
```

## 5. 启动顺序

### 5.1 启动 Filter

```powershell
python Filter/Fastapi/CTDetectionServer.py
```

验证：

```powershell
Invoke-RestMethod http://localhost:8000/api/ct-artifact/health
```

期望：

```json
{
  "status": "ok"
}
```

### 5.2 启动 LesionDetection 真实模型模式

```powershell
$env:LESION_MODE="model"
$env:HEMORRHAGE_CHECKPOINT="D:\exam\HeadCTLesionDetection\models\hemorrhage\runs\hemorrhage_v1\best.pt"
$env:HEMORRHAGE_DEVICE="auto"
python HeadCTLesionDetection/LesionDetectionServer.py
```

验证：

```powershell
Invoke-RestMethod http://localhost:8020/api/head-ct-lesion/health
```

期望：

```json
{
  "status": "ok",
  "mode": "model",
  "models": {
    "hemorrhage": {
      "checkpoint_exists": true
    }
  }
}
```

如果返回：

```json
{
  "status": "degraded",
  "models": {
    "hemorrhage": {
      "checkpoint_exists": false
    }
  }
}
```

说明 checkpoint 路径不正确或模型文件尚未生成。

### 5.3 启动 Orchestrator

```powershell
$env:FILTER_BASE_URL="http://localhost:8000"
$env:LESION_SERVICE_ENABLED="true"
$env:LESION_BASE_URL="http://localhost:8020"
$env:LESION_REQUESTED_TYPES="hemorrhage"
$env:LESION_SKIP_ON_SEVERE_ARTIFACT="false"
python HeadCTOrchestrator/OrchestratorServer.py
```

验证：

```powershell
Invoke-RestMethod http://localhost:8010/api/head-ct-ai/health
```

期望：

```json
{
  "status": "ok",
  "lesion_service_enabled": true,
  "filter": {
    "status": "ok"
  },
  "lesion": {
    "status": "ok",
    "mode": "model"
  }
}
```

## 6. 联调请求

### 6.1 上传 CT

示例：

```powershell
$file = "D:\exam\Filter\model\runs\config_visual_smoke\sample_ct_positive.nii.gz"

curl.exe -X POST "http://localhost:8010/api/head-ct-ai/tasks" `
  -F "patient_id=patient_001" `
  -F "study_id=study_001" `
  -F "series_id=series_001" `
  -F "report_id=report_001" `
  -F "doctor_id=doctor_001" `
  -F "file=@$file"
```

返回应包含：

```json
{
  "task_id": "xxx",
  "status": "queued",
  "task_url": "/api/head-ct-ai/tasks/xxx",
  "result_url": "/api/head-ct-ai/results/xxx"
}
```

### 6.2 轮询任务

```powershell
Invoke-RestMethod http://localhost:8010/api/head-ct-ai/tasks/{task_id}
```

最终期望：

```json
{
  "status": "success",
  "pipeline": {
    "quality_control": "success",
    "lesion_analysis": "success",
    "report_assist": "success"
  }
}
```

### 6.3 获取结果

```powershell
Invoke-RestMethod http://localhost:8010/api/head-ct-ai/results/{task_id}
```

核心结构：

```json
{
  "task_id": "xxx",
  "status": "success",
  "quality_control": {},
  "lesion_analysis": {
    "enabled": true,
    "status": "success",
    "results": [
      {
        "lesion_type": "intracranial_hemorrhage",
        "detected": false,
        "confidence": 0.0,
        "model_name": "head_ct_hemorrhage_classifier"
      }
    ]
  },
  "report_assist": {
    "summary": "...",
    "quality_control_text": "...",
    "lesion_text": "...",
    "warnings": [],
    "can_enter_report": true
  }
}
```

## 7. 输出检查

每个 Orchestrator 任务目录应包含：

```text
HeadCTOrchestrator/orchestrator_outputs/{task_id}/
  task.json
  input.nii.gz
  filter_result.json
  lesion_result.json
  orchestrator_result.json
```

检查重点：

- `filter_result.json` 存在。
- `lesion_result.json` 存在。
- `orchestrator_result.json` 存在。
- `orchestrator_result.json.pipeline.quality_control = success`
- `orchestrator_result.json.pipeline.lesion_analysis = success`
- `orchestrator_result.json.pipeline.report_assist = success`
- `orchestrator_result.json.lesion_analysis.results[0].model_name = head_ct_hemorrhage_classifier`

## 8. 异常场景验收

### 8.1 Filter 未启动

操作：

```text
只启动 Orchestrator，不启动 Filter
```

期望：

```json
{
  "status": "failed",
  "error_code": "FILTER_UNAVAILABLE"
}
```

### 8.2 LesionDetection 未启动

操作：

```text
启动 Filter 和 Orchestrator，设置 LESION_SERVICE_ENABLED=true，但不启动 LesionDetection
```

期望：

```json
{
  "status": "failed",
  "error_code": "LESION_SERVICE_UNAVAILABLE"
}
```

### 8.3 checkpoint 缺失

操作：

```powershell
$env:LESION_MODE="model"
$env:HEMORRHAGE_CHECKPOINT="D:\exam\missing_best.pt"
python HeadCTLesionDetection/LesionDetectionServer.py
```

期望：

- LesionDetection `/health` 返回 `status=degraded`。
- Orchestrator 调用后返回病灶服务任务失败。
- 错误信息中保留 `MODEL_CHECKPOINT_NOT_FOUND`。

### 8.4 重度伪影跳过病灶识别

如果配置：

```powershell
$env:LESION_SKIP_ON_SEVERE_ARTIFACT="true"
```

且 Filter 返回 `severity=severe`，则期望：

```json
{
  "lesion_analysis": {
    "enabled": true,
    "status": "skipped"
  }
}
```

## 9. 自动化测试建议

在 `HeadCTOrchestrator/tests/test_orchestrator_pipeline.py` 增加或保留以下测试：

```text
test_orchestrator_pipeline_with_filter
test_orchestrator_pipeline_with_mock_lesion_detection
test_filter_unavailable_marks_task_failed
test_invalid_file_type_returns_stable_error
test_missing_task_and_result_return_stable_errors
```

新增建议：

```text
test_orchestrator_pipeline_with_model_lesion_detection
test_lesion_service_unavailable_marks_task_failed
test_lesion_checkpoint_missing_is_reported
test_skip_lesion_on_severe_artifact
```

说明：

- `test_orchestrator_pipeline_with_model_lesion_detection` 可以使用临时 checkpoint 验证技术链路。
- 模型质量不应在 Orchestrator 单元测试中验证。
- 模型质量应由 `HeadCTLesionDetection/models/hemorrhage/evaluate.py` 的指标文件验证。
- 如果使用 `smoke_best.pt`，验收范围仅限服务链路和错误码，不包含模型准确率。

## 10. 验收标准

阶段 H 完成时，应满足：

- 三个服务均可独立启动。
- Orchestrator `/health` 能同时看到 Filter 和 LesionDetection 状态。
- 上传 `.nii/.nii.gz` 后任务最终成功。
- 结果目录包含 `filter_result.json`、`lesion_result.json`、`orchestrator_result.json`。
- `lesion_analysis.status = success`。
- `report_assist.can_enter_report = true`，除非出现明确质量限制或服务失败。
- Filter 不可用、LesionDetection 不可用、checkpoint 缺失均有稳定错误码。
- 自动化测试通过。

## 11. 阶段交付物

建议保留：

```text
HeadCTOrchestrator/阶段H_三服务真实模型模式联调记录.md
HeadCTOrchestrator/orchestrator_outputs/{联调任务ID}/
HeadCTLesionDetection/models/hemorrhage/runs/hemorrhage_v1/metrics.json
HeadCTLesionDetection/models/hemorrhage/runs/hemorrhage_v1/eval/predictions.csv
```

联调记录应包含：

- 使用的 checkpoint 路径。
- 使用的模型版本。
- 三个服务启动命令。
- 成功任务 ID。
- 失败场景验证结果。
- 当前已知限制。
