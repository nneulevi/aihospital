# 上级 Orchestrator 模块开发指导

## 1. 模块定位

上级 Orchestrator 不直接替代 Filter，也不直接替代具体病灶识别模型。

它的职责是：

```text
统一接收影像分析请求
  -> 调用 Filter 完成影像质控与金属伪影识别
  -> 根据质控结果决定是否继续后续病灶识别
  -> 调用一个或多个病灶识别模型
  -> 汇总结构化结果
  -> 给报告辅助模块提供统一输入
```

建议命名：

```text
HeadCTOrchestrator
```

或者：

```text
ImageAIOrchestrator
```

不要把它命名为“诊断系统”或“自动诊断模块”。它更准确的定位是：

```text
头部 CT AI 影像分析编排模块
```

## 2. 与 Filter 的关系

Filter 已经完成影像质控与金属伪影识别，并提供稳定任务式接口：

```text
POST /api/ct-artifact/tasks
GET  /api/ct-artifact/tasks/{task_id}
GET  /api/ct-artifact/results/{task_id}
GET  /api/ct-artifact/files/{task_id}/{file_name}
```

Orchestrator 应把 Filter 当作一个独立服务调用，而不是直接导入 Filter 内部 Python 函数。

推荐关系：

```text
Orchestrator
  -> HTTP 调用 Filter FastAPI
  -> 读取 Filter result.json
  -> 保存 Filter 输出摘要
  -> 将质控结论传递给后续病灶识别模块
```

Filter 输出中对 Orchestrator 最重要的字段：

- `artifact_detected`
- `artifact_ratio`
- `severity`
- `affected_slices`
- `report_suggestion`
- `mask_file`
- `download_url`
- `preview_urls`
- `model_name`
- `model_version`
- `elapsed_ms`
- `input_metadata`

## 3. 推荐整体架构

建议新建独立目录，不要继续塞进 `Filter/` 内部。

推荐目录：

```text
HeadCTOrchestrator/
  OrchestratorServer.py
  config.py
  service_clients/
    filter_client.py
    lesion_client.py
    report_client.py
  schemas/
    request_schema.py
    result_schema.py
  task_store.py
  tests/
    test_orchestrator_health.py
    test_orchestrator_pipeline.py
  README.md
  .env.example
```

如果当前项目暂时只能放在 `Filter/` 下，也建议使用独立子目录：

```text
Filter/
  Orchestrator/
    OrchestratorServer.py
    config.py
    service_clients/
    schemas/
    task_store.py
    tests/
    README.md
```

## 4. 第一阶段目标

第一阶段不要急着接入真实病灶模型。

先完成：

```text
Orchestrator -> Filter -> Orchestrator 汇总结果
```

也就是先搭好上级编排骨架。

第一阶段接口建议：

```text
GET  /api/head-ct-ai/health
POST /api/head-ct-ai/tasks
GET  /api/head-ct-ai/tasks/{task_id}
GET  /api/head-ct-ai/results/{task_id}
```

第一阶段流程：

1. Orchestrator 接收 `.nii/.nii.gz` CT 文件。
2. Orchestrator 创建自己的 `task_id`。
3. Orchestrator 调用 Filter `/api/ct-artifact/tasks`。
4. Orchestrator 轮询 Filter 任务状态。
5. Orchestrator 获取 Filter `result.json`。
6. Orchestrator 生成自己的 `orchestrator_result.json`。
7. Orchestrator 返回统一分析结果。

## 5. 第一阶段输出结构

推荐输出目录：

```text
HeadCTOrchestrator/
  orchestrator_outputs/
    {task_id}/
      task.json
      input.nii.gz
      filter_result.json
      orchestrator_result.json
```

如果放在 `Filter/Orchestrator/` 下：

```text
Filter/
  Orchestrator/
    orchestrator_outputs/
      {task_id}/
        task.json
        input.nii.gz
        filter_result.json
        orchestrator_result.json
```

## 6. orchestrator_result.json 推荐结构

```json
{
  "task_id": "xxx",
  "status": "success",
  "module": "head_ct_ai_orchestrator",
  "input": {
    "file_name": "ct.nii.gz",
    "image_size_xyz": [512, 512, 128],
    "spacing": [0.48, 0.48, 1.0]
  },
  "quality_control": {
    "backend": "unet3d",
    "artifact_detected": true,
    "artifact_ratio": 0.034,
    "severity": "moderate",
    "affected_slices": [42, 43, 44],
    "report_suggestion": "存在中度金属伪影，可能影响邻近区域判断，建议医生结合原始影像复核。",
    "result_url": "http://localhost:8000/api/ct-artifact/results/xxx",
    "mask_url": "http://localhost:8000/api/ct-artifact/files/xxx/mask.nii.gz",
    "preview_urls": {
      "axial": "http://localhost:8000/api/ct-artifact/files/xxx/preview_axial.png",
      "coronal": "http://localhost:8000/api/ct-artifact/files/xxx/preview_coronal.png",
      "sagittal": "http://localhost:8000/api/ct-artifact/files/xxx/preview_sagittal.png"
    }
  },
  "lesion_analysis": {
    "status": "not_configured",
    "results": []
  },
  "report_assist": {
    "summary": "影像存在中度金属伪影，建议医生结合原始影像复核。当前未接入病灶识别模型。",
    "warnings": [
      "本结果仅用于影像质控与辅助提示，不作为最终诊断结论。"
    ]
  },
  "elapsed_ms": 12345,
  "error_code": null,
  "error_message": null
}
```

## 7. Orchestrator 任务状态

建议沿用 Filter 的任务状态：

```text
queued
running_filter
filter_success
running_lesion_analysis
success
failed
```

第一阶段可以只使用：

```text
queued
running_filter
success
failed
```

后续接入病灶模型后再启用：

```text
running_lesion_analysis
```

## 8. 质控结果如何影响后续病灶识别

Orchestrator 需要根据 Filter 结果做策略判断。

建议规则：

```text
severity == none:
  正常进入病灶识别

severity == mild:
  正常进入病灶识别，但报告提示存在轻度伪影

severity == moderate:
  进入病灶识别，但在 affected_slices 附近结果标注 warning

severity == severe:
  可以继续识别，但整体结果必须标注低可信度
  如病灶模型未经过强伪影数据验证，可选择跳过病灶识别
```

推荐在结果中加入：

```json
{
  "analysis_reliability": "limited_by_artifact",
  "reliability_reason": "存在重度金属伪影，可能影响局部结构判断。"
}
```

## 9. 后续病灶识别模块接口建议

后续病灶识别模块不要直接和 Filter 混在一起。

建议每个识别能力独立提供接口：

```text
POST /api/head-ct-lesion/tasks
GET  /api/head-ct-lesion/tasks/{task_id}
GET  /api/head-ct-lesion/results/{task_id}
```

病灶结果建议统一结构：

```json
{
  "lesion_type": "intracranial_hemorrhage",
  "detected": true,
  "confidence": 0.91,
  "affected_slices": [30, 31, 32],
  "bbox": [],
  "mask_url": null,
  "model_name": "head_ct_hemorrhage_detector",
  "model_version": "v1.0.0",
  "report_suggestion": "疑似颅内出血，请医生结合原始影像复核。"
}
```

第一批可规划的病灶识别方向：

- 颅内出血。
- 颅骨骨折。
- 脑梗死。
- 中线移位。
- 占位效应。

但第一阶段 Orchestrator 只需要预留 `lesion_analysis.results`，不需要立刻全部实现。

## 10. 报告辅助模块边界

Orchestrator 可以生成报告辅助摘要，但不能输出最终医学诊断。

推荐字段：

```json
{
  "report_assist": {
    "summary": "存在中度金属伪影，可能影响邻近区域判断。未接入病灶识别模型。",
    "suggestions": [],
    "warnings": [
      "AI 结果仅供辅助参考，最终结论需医生审核。"
    ]
  }
}
```

禁止表述：

```text
患者确诊为……
无需医生复核……
AI 已完成最终诊断……
```

推荐表述：

```text
疑似……
建议结合原始影像复核……
可能影响判断……
供医生参考……
```

## 11. Spring Boot / 主平台调用方式

主平台未来更适合只调用 Orchestrator，而不是分别调用 Filter 和各个模型。

推荐主平台调用链：

```text
Spring Boot / 主平台
  -> POST /api/head-ct-ai/tasks
  -> GET  /api/head-ct-ai/tasks/{task_id}
  -> GET  /api/head-ct-ai/results/{task_id}
```

Orchestrator 内部负责：

```text
调用 Filter
调用病灶模型
汇总结果
生成报告辅助字段
```

这样主平台只需要对接一个统一 AI 入口。

## 12. 配置项建议

`.env.example` 建议包含：

```text
ORCH_HOST=0.0.0.0
ORCH_PORT=8010

FILTER_BASE_URL=http://localhost:8000
FILTER_TIMEOUT_SECONDS=300
FILTER_POLL_INTERVAL_SECONDS=1

LESION_SERVICE_ENABLED=false
LESION_BASE_URL=http://localhost:8020
LESION_TIMEOUT_SECONDS=300

ORCH_OUTPUT_ROOT=orchestrator_outputs
```

第一阶段只需要 `FILTER_BASE_URL` 可用。

## 13. Smoke Test 建议

第一阶段至少测试：

```text
GET  /api/head-ct-ai/health
POST /api/head-ct-ai/tasks
GET  /api/head-ct-ai/tasks/{task_id}
GET  /api/head-ct-ai/results/{task_id}
```

测试目标：

- Orchestrator 能检查 Filter 服务状态。
- Orchestrator 能上传 CT 给 Filter。
- Orchestrator 能轮询 Filter 任务。
- Orchestrator 能保存 `filter_result.json`。
- Orchestrator 能生成 `orchestrator_result.json`。
- Filter 失败时 Orchestrator 能返回明确错误码。

## 14. 第一阶段验收标准

第一阶段完成后，应满足：

- 主平台只需要调用 Orchestrator。
- Orchestrator 能成功调用 Filter。
- 能生成统一任务 ID。
- 能保存 `task.json`。
- 能保存 `filter_result.json`。
- 能保存 `orchestrator_result.json`。
- 返回结果中包含 `quality_control`。
- 返回结果中预留 `lesion_analysis`。
- 返回结果中包含 `report_assist`。
- Filter 不可用时能返回稳定错误。
- 有 smoke test 覆盖主链路。

## 15. 推荐下一步开发任务

建议下一次开发直接执行：

```text
新建 HeadCTOrchestrator 或 Filter/Orchestrator 模块，
实现 /api/head-ct-ai/health、/api/head-ct-ai/tasks、
/api/head-ct-ai/tasks/{task_id}、/api/head-ct-ai/results/{task_id}，
第一阶段只编排 Filter，不接入真实病灶模型。
```

完成这一阶段后，再开始设计病灶识别模块接口和模型接入。
