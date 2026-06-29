# HeadCTLesionDetection API Contract

头部 CT 病灶识别服务。当前支持两种运行模式：

- `LESION_MODE=mock`：合同测试模式，返回固定阴性病灶结果。
- `LESION_MODE=model`：真实模型模式，调用颅内出血分类 checkpoint。

调用链：

```text
主平台 -> Orchestrator -> Filter -> LesionDetection -> Orchestrator
```

## 运行模式

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `LESION_MODE` | `mock` | `mock` 或 `model` |
| `LESION_REQUESTED_TYPES` | `hemorrhage` | 默认请求病灶类型 |
| `HEMORRHAGE_CHECKPOINT` | `models/hemorrhage/runs/hemorrhage_v1/best.pt` | 颅内出血分类 checkpoint |
| `HEMORRHAGE_DEVICE` | `auto` | `auto` / `cpu` / `cuda` |

`model` 模式当前只支持：

```text
hemorrhage
```

## 接口

```text
GET  /api/head-ct-lesion/health
POST /api/head-ct-lesion/tasks
GET  /api/head-ct-lesion/tasks/{task_id}
GET  /api/head-ct-lesion/results/{task_id}
```

## POST /api/head-ct-lesion/tasks

`multipart/form-data` 字段：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `file` | 是 | `.nii` / `.nii.gz` CT 文件 |
| `case_context` | 否 | 平台上下文 JSON |
| `quality_context` | 否 | Filter 质控上下文 JSON |
| `requested_lesions` | 否 | 逗号分隔，如 `hemorrhage` |

## 输出目录

```text
HeadCTLesionDetection/lesion_outputs/{task_id}/
  task.json
  input.nii.gz
  quality_context.json
  lesion_result.json
```

## lesion_result.json

核心字段：

```json
{
  "task_id": "xxx",
  "status": "success",
  "module": "head_ct_lesion_detection",
  "inference_mode": "model",
  "requested_lesions": ["hemorrhage"],
  "results": [],
  "summary": {
    "detected_lesion_count": 0,
    "positive_lesion_types": [],
    "highest_confidence": 0.0
  }
}
```

## 错误码

```text
INVALID_FILE_TYPE
INVALID_LESION_MODE
UNSUPPORTED_LESION_TYPE
QUALITY_CONTEXT_INVALID
MODEL_CHECKPOINT_NOT_FOUND
INFERENCE_FAILED
TASK_NOT_FOUND
RESULT_NOT_FOUND
```
