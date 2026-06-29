# HeadCTOrchestrator API Contract

## 1. 模块定位

`HeadCTOrchestrator` 是头部 CT AI 影像分析编排模块。主平台只需要调用本模块，本模块内部负责调用 `Filter` 质控服务，并为后续病灶识别与报告辅助预留统一结果结构。

当前阶段：

```text
Orchestrator -> Filter -> Orchestrator 汇总结果
```

可选启用 mock 病灶识别链路：

```text
Orchestrator -> Filter -> HeadCTLesionDetection(mock) -> Orchestrator 汇总结果
```

暂未接入真实病灶识别模型。

## 2. Base URL

默认：

```text
http://localhost:8010
```

## 3. 接口列表

```text
GET  /api/head-ct-ai/health
POST /api/head-ct-ai/tasks
GET  /api/head-ct-ai/tasks/{task_id}
GET  /api/head-ct-ai/results/{task_id}
POST /api/head-ct-ai/reviews/{task_id}
GET  /api/head-ct-ai/reviews/{task_id}
```

## 4. 健康检查

### Request

```http
GET /api/head-ct-ai/health
```

### Response

```json
{
  "status": "ok",
  "module": "head_ct_ai_orchestrator",
  "module_version": "v1.0.0",
  "service": {
    "available": true,
    "filter_base_url": "http://localhost:8000",
    "error": null
  },
  "filter": {
    "status": "ok"
  },
  "lesion_service_enabled": false,
  "rag": {
    "enabled": false,
    "vector_db": {
      "status": "disabled",
      "backend": "pgvector"
    }
  },
  "storage": {
    "outputs": "D:/exam/HeadCTOrchestrator/orchestrator_outputs",
    "outputs_exists": true
  }
}
```

如果 Filter 不可用，`status` 为 `degraded`，`filter.status` 为 `unavailable`。

如果启用 RAG，`rag.vector_db.status` 会反映 pgvector 当前状态：`ok`、`not_configured` 或 `unavailable`。

## 5. 创建分析任务

### Request

```http
POST /api/head-ct-ai/tasks
Content-Type: multipart/form-data
```

字段：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `file` | 是 | `.nii`、`.nii.gz`、`.dcm`、`.dicom` 或 DICOM Series `.zip` CT 文件 |
| `patient_id` | 否 | 患者 ID |
| `study_id` | 否 | 检查 ID |
| `series_id` | 否 | 序列 ID |
| `report_id` | 否 | 报告 ID |
| `doctor_id` | 否 | 医生 ID |

### Response

```json
{
  "task_id": "xxx",
  "status": "queued",
  "module": "head_ct_ai_orchestrator",
  "case_context": {
    "patient_id": "patient_001",
    "study_id": "study_001",
    "series_id": "series_001",
    "report_id": "report_001",
    "doctor_id": "doctor_001"
  },
  "pipeline": {
    "quality_control": "queued",
    "lesion_analysis": "not_configured",
    "report_assist": "pending"
  },
  "original_file": "ct_series.zip",
  "input_file": "input.nii.gz",
  "input_metadata": {
    "source_format": "dicom_zip",
    "normalization": "dicom_zip_to_nifti",
    "dicom_file_count": 32
  },
  "task_url": "/api/head-ct-ai/tasks/xxx",
  "result_url": "/api/head-ct-ai/results/xxx"
}
```

## 6. 查询任务

### Request

```http
GET /api/head-ct-ai/tasks/{task_id}
```

### Response

```json
{
  "task_id": "xxx",
  "status": "success",
  "filter_task_id": "yyy",
  "filter_status": "success",
  "pipeline": {
    "quality_control": "success",
    "lesion_analysis": "not_configured",
    "report_assist": "success"
  },
  "result_url": "/api/head-ct-ai/results/xxx",
  "error_code": null,
  "error_message": null
}
```

任务状态：

```text
queued
running_filter
filter_success
success
failed
```

## 7. 获取结果

### Request

```http
GET /api/head-ct-ai/results/{task_id}
```

### Response

```json
{
  "task_id": "xxx",
  "status": "success",
  "module": "head_ct_ai_orchestrator",
  "module_version": "v1.0.0",
  "case_context": {
    "patient_id": null,
    "study_id": null,
    "series_id": null,
    "report_id": null,
    "doctor_id": null
  },
  "pipeline": {
    "quality_control": "success",
    "lesion_analysis": "not_configured",
    "report_assist": "success"
  },
  "input": {
    "file_name": "ct_series.zip",
    "source_format": "dicom_zip",
    "normalized_file": "input.nii.gz",
    "normalization": "dicom_zip_to_nifti",
    "image_size_xyz": [512, 512, 32],
    "array_shape_zyx": [32, 512, 512],
    "spacing": [0.5, 0.5, 5.0]
  },
  "quality_control": {
    "artifact_detected": true,
    "artifact_ratio": 0.034,
    "severity": "moderate",
    "affected_slices": [42, 43, 44],
    "report_suggestion": "存在中度金属伪影，可能影响邻近区域判断，建议医生结合原始影像复核。"
  },
  "lesion_analysis": {
    "status": "success",
    "enabled": true,
    "task_id": "lesion_task_xxx",
    "result_url": "http://localhost:8020/api/head-ct-lesion/results/lesion_task_xxx",
    "results": [
      {
        "lesion_type": "intracranial_hemorrhage",
        "display_name": "颅内出血",
        "detected": false,
        "confidence": 0.05,
        "severity": "none",
        "report_suggestion": "未见明确颅内出血征象，建议医生结合原始影像复核。"
      }
    ],
    "warnings": []
  },
  "report_assist": {
    "summary": "存在中度金属伪影，可能影响邻近区域判断，建议医生结合原始影像复核。 当前未接入病灶识别模型。",
    "quality_control_text": "存在中度金属伪影，可能影响邻近区域判断，建议医生结合原始影像复核。",
    "lesion_text": "未接入病灶识别模型。",
    "rag_enhanced": false,
    "suggested_report_sections": {
      "findings": [],
      "impression": [],
      "limitations": [
        "AI 结果仅供辅助参考，最终结论需医生审核。"
      ]
    },
    "recommended_actions": [],
    "rag_context": {
      "enabled": false,
      "status": "disabled",
      "retrieval_confidence": 0.0,
      "sources": [],
      "fallback_reason": null
    },
    "llm_context": {
      "enabled": false,
      "provider": "rule_template",
      "model": null,
      "status": "disabled",
      "prompt_version": "report_assist_v1",
      "fallback_reason": null
    },
    "warnings": [
      "AI 结果仅供辅助参考，最终结论需医生审核。"
    ],
    "can_enter_report": false,
    "requires_doctor_review": true
  },
  "warnings": [],
  "elapsed_ms": 12345,
  "error_code": null,
  "error_message": null
}
```

## 8. 医生审核

### 8.1 提交审核

```http
POST /api/head-ct-ai/reviews/{task_id}
Content-Type: application/json
```

请求体：

```json
{
  "review_status": "modified",
  "doctor_id": "doctor_001",
  "doctor_comment": "已结合原始影像复核，报告草稿部分采纳。",
  "artifact_review": {
    "accepted": true,
    "severity_override": null,
    "comment": "质控结果符合阅片感受。"
  },
  "lesion_review": {
    "accepted": false,
    "lesion_overrides": [
      {
        "lesion_type": "intracranial_hemorrhage",
        "detected": false,
        "comment": "原始影像复核后未见明确出血。"
      }
    ],
    "comment": "模型提示仅作参考。"
  },
  "report_review": {
    "ai_summary_used": false,
    "final_report_text": "医生最终报告文本。",
    "final_report_used": true
  },
  "safety": {
    "doctor_confirmed_ai_is_reference_only": true,
    "requires_follow_up": false
  }
}
```

响应：

```json
{
  "status": "success",
  "review": {
    "task_id": "xxx",
    "review_status": "modified",
    "doctor_id": "doctor_001",
    "reviewed_at": "2026-06-12T10:30:00",
    "source_result_url": "/api/head-ct-ai/results/xxx"
  }
}
```

说明：

- 只允许对 `status=success` 的任务提交审核。
- 审核写入 `review.json`。
- 每次提交追加写入 `review_events.jsonl`。
- 不修改原始 `orchestrator_result.json`。

### 8.2 查询审核

```http
GET /api/head-ct-ai/reviews/{task_id}
```

已审核时：

```json
{
  "status": "success",
  "review": {
    "task_id": "xxx",
    "review_status": "confirmed"
  }
}
```

任务存在但未审核时：

```json
{
  "status": "success",
  "review": {
    "task_id": "xxx",
    "review_status": "pending"
  }
}
```

审核状态枚举：

```text
pending
confirmed
modified
rejected
needs_follow_up
```

## 9. 错误码

| 错误码 | 场景 |
| --- | --- |
| `INVALID_FILE_TYPE` | 上传文件不是 `.nii`、`.nii.gz`、`.dcm`、`.dicom` 或 DICOM `.zip` |
| `DICOM_NORMALIZATION_FAILED` | DICOM/RSNA 上传内容无法读取或无法转换为内部 NIfTI |
| `FILTER_UNAVAILABLE` | Filter 服务不可用 |
| `FILTER_TASK_FAILED` | Filter 任务执行失败 |
| `FILTER_TIMEOUT` | Filter 任务轮询超时 |
| `LESION_SERVICE_UNAVAILABLE` | 病灶识别服务不可用 |
| `LESION_TASK_FAILED` | 病灶识别任务失败 |
| `LESION_TIMEOUT` | 病灶识别任务轮询超时 |
| `TASK_NOT_FOUND` | 查询的任务不存在 |
| `RESULT_NOT_FOUND` | 查询的结果不存在 |
| `ORCHESTRATION_FAILED` | 编排流程发生未分类异常 |
| `INVALID_REVIEW_PAYLOAD` | 审核请求体不是合法结构 |
| `INVALID_REVIEW_STATUS` | 审核状态不在枚举范围内 |
| `TASK_NOT_SUCCESS` | 任务未成功完成，不允许提交医生审核 |
| `RAG_RETRIEVAL_FAILED` | RAG 启用后 pgvector 未配置、不可用、检索无结果或向量检索失败 |
| `LLM_PROVIDER_FAILED` | LLM 启用后阿里百炼 API Key 缺失、调用失败、输出非法或安全检查失败 |

错误响应：

```json
{
  "status": "failed",
  "error_code": "INVALID_FILE_TYPE",
  "message": "只支持 .nii、.nii.gz、.dcm、.dicom 或 DICOM .zip 格式的 CT 文件"
}
```

任务失败时，错误信息写入 `task.json`：

```json
{
  "task_id": "xxx",
  "status": "failed",
  "error_code": "FILTER_UNAVAILABLE",
  "error_message": "Filter service unavailable"
}
```

## 10. 平台字段映射

| Orchestrator 字段 | 主平台建议用途 |
| --- | --- |
| `task_id` | AI 分析任务 ID |
| `case_context.patient_id` | 患者 ID |
| `case_context.study_id` | 检查 ID |
| `case_context.series_id` | 序列 ID |
| `case_context.report_id` | 报告 ID |
| `quality_control` | 影像质控结果 |
| `lesion_analysis` | 病灶识别结果，当前预留 |
| `report_assist` | 报告草稿辅助字段 |
| `warnings` | 医生审核提示 |
| `review.review_status` | 医生审核状态 |
| `review.report_review.final_report_text` | 医生最终报告文本 |

## 11. 医疗安全边界

本模块输出仅用于辅助提示，不作为最终医学诊断。

平台展示时应保留类似提示：

```text
AI 结果仅供辅助参考，最终结论需医生审核。
```
## Clinical Assist Conversation Memory Extension

The clinical assist endpoints keep backward compatibility. Existing callers can continue to omit all memory fields.

### Request Extension

`POST /api/head-ct-ai/clinical/consultation`

`POST /api/head-ct-ai/clinical/diagnosis`

Optional fields:

```json
{
  "conversation_id": "patient:12:consultation",
  "user_id": "patient:12",
  "role_scope": "patient",
  "visit_id": 88,
  "memory_enabled": true
}
```

`conversation_id` is the memory boundary. Recommended values:

- Patient consultation: `patient:{patientId}:consultation`
- Doctor diagnosis assist: `medical_record:{medicalRecordId}:diagnosis`

### Response Extension

When memory is enabled and configured, the response contains:

```json
{
  "memory_context": {
    "enabled": true,
    "conversation_id": "patient:12:consultation",
    "role_scope": "patient",
    "summary": "用户提到：头痛持续3天...",
    "key_facts": ["头痛持续3天", "高血压病史"],
    "unresolved_questions": [],
    "recent_message_count": 2,
    "semantic_recall": {
      "enabled": true,
      "result_count": 2,
      "scope": "conversation_or_same_patient_role"
    },
    "semantic_memories": [
      {
        "conversation_id": "patient:12:old",
        "sender": "user",
        "content": "Previous visit: I take warfarin...",
        "score": 0.62,
        "provider": "pgvector"
      }
    ],
    "message_count": 14,
    "compression": {
      "strategy": "rolling_structured_summary",
      "recent_message_limit": 8,
      "compression_interval_messages": 6,
      "summarized_message_count": 12
    }
  }
}
```

The memory context is used only as AI prompt context. It does not directly update diagnosis, report, EMR, or doctor review records.
