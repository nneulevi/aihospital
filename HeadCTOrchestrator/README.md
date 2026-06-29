# Head CT AI Orchestrator

头部 CT AI 影像分析编排模块。当前可编排 `Filter`、`HeadCTLesionDetection`、pgvector RAG、Rerank 和外部 LLM 报告辅助。

主平台与 Orchestrator、报告服务及 EMR 的完整协同方式见 [主平台协同工作与接入说明.md](../主平台协同工作与接入说明.md)。

## 接口

- `GET /api/head-ct-ai/health`
- `POST /api/head-ct-ai/tasks`
- `GET /api/head-ct-ai/tasks/{task_id}`
- `GET /api/head-ct-ai/results/{task_id}`

平台对接契约：

- [API_CONTRACT.md](API_CONTRACT.md)
- [SPRING_BOOT_CLIENT_EXAMPLE.md](SPRING_BOOT_CLIENT_EXAMPLE.md)

## 启动

先启动 Filter：

```powershell
python Filter/Fastapi/CTDetectionServer.py
```

如需启用 mock 病灶识别，再启动 LesionDetection：

```powershell
python HeadCTLesionDetection/LesionDetectionServer.py
```

再启动 Orchestrator：

```powershell
python HeadCTOrchestrator/OrchestratorServer.py
```

启用病灶识别编排：

```powershell
$env:LESION_SERVICE_ENABLED="true"
$env:LESION_BASE_URL="http://localhost:8020"
$env:LESION_REQUESTED_TYPES="hemorrhage"
python HeadCTOrchestrator/OrchestratorServer.py
```

默认地址：

```text
http://localhost:8010
```

## 输出

```text
HeadCTOrchestrator/orchestrator_outputs/{task_id}/
  task.json
  source/{original_upload}
  input.nii.gz
  filter_result.json
  lesion_result.json      # 启用病灶识别时生成
  orchestrator_result.json
```

## CT 输入格式

`POST /api/head-ct-ai/tasks` 支持：

- `.nii`
- `.nii.gz`
- `.dcm`
- `.dicom`
- DICOM Series `.zip`

Orchestrator 会先把 DICOM/RSNA 上传内容归一化为内部 `input.nii.gz`，再调用 Filter 与
LesionDetection。下游服务仍保持 NIfTI 输入契约，主平台只需要对接 Orchestrator。

任务记录中的 `input_metadata` 会保留 `source_format`、`normalization`、`spacing`、
`image_size_xyz`、DICOM series ID 和切片数量等信息。

`orchestrator_result.json` 包含：

- `case_context`
- `pipeline`
- `quality_control`
- `analysis_reliability`
- `lesion_analysis`
- `report_assist`
- `warnings`

## 错误码

- `INVALID_FILE_TYPE`
- `DICOM_NORMALIZATION_FAILED`
- `FILTER_UNAVAILABLE`
- `FILTER_TASK_FAILED`
- `FILTER_TIMEOUT`
- `LESION_SERVICE_UNAVAILABLE`
- `LESION_TASK_FAILED`
- `LESION_TIMEOUT`
- `TASK_NOT_FOUND`
- `RESULT_NOT_FOUND`
- `ORCHESTRATION_FAILED`

## 测试

```powershell
python -m pytest HeadCTOrchestrator/tests/test_orchestrator_pipeline.py
```

测试覆盖：

- 健康检查。
- Orchestrator -> Filter 主链路。
- Orchestrator -> Filter -> mock LesionDetection 集成链路。
- 非法文件类型。
- 任务不存在。
- 结果不存在。
- Filter 不可用。
