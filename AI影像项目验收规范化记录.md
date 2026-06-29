# AI影像项目验收规范化记录

更新时间：2026-06-26

## 本阶段目标

本阶段目标不是医院真实上线合规，而是把课程/项目验收语境下的 AI 影像链路说法和接口输出规范化，确保：

- 上传 CT 影像后能够完成伪影识别。
- 病灶识别模块能够给出结构化分类结果。
- 报告辅助模块能够基于模型结构化结果和 RAG/LLM 生成报告辅助内容。
- Project2 主平台能够拿到并展示 AI 影像链路状态。
- 验收脚本能够验证端到端链路，而不是只验证单个接口可访问。

## 已完成改动

### 1. Orchestrator 新增 AI 影像链路状态汇总

新增文件：

- `HeadCTOrchestrator/ai_imaging_readiness.py`

新增统一输出字段：

- `ai_imaging_status.project_use_status`
- `ai_imaging_status.workflow_ready`
- `ai_imaging_status.quality_control_model`
- `ai_imaging_status.artifact_reduction`
- `ai_imaging_status.lesion_model`
- `ai_imaging_status.report_assist`
- `ai_imaging_status.diagnosis_output_policy`
- `ai_imaging_status.limitations`

该字段用于表达项目验收层面的链路状态，例如：

- `ready_for_project_demo`：项目链路可用。
- `degraded_for_project_demo`：链路可运行但存在缺项。
- `lesion_model.task_type=classification`：当前病灶模型输出为分类，不冒充像素级分割。
- `artifact_reduction.status=registered_not_executable`：InDuDoNet checkpoint 已登记，但当前未执行校正。

### 2. Project2 透传 AI 影像状态

已更新：

- `Project2/src/main/java/com/neuedu/his/model/vo/ImageAnalyzeResponseVO.java`
- `Project2/src/main/java/com/neuedu/his/service/impl/ImageServiceRealImpl.java`
- `Project2/src/main/java/com/neuedu/his/service/impl/ImageServiceMockImpl.java`

新增响应字段：

- `aiImagingStatus`

真实模式下由 Orchestrator 的 `ai_imaging_status` 透传；mock 模式下返回 `mock_demo_only`，避免真实/模拟模式结构不一致。

### 3. 医生端前端展示链路状态

已更新：

- `frontend/src/views/doctor/PatientVisit.vue`
- `frontend/src/api/model/imageAnalyzeResponseVO.ts`

医生端 AI 影像识别卡片新增展示：

- 链路状态
- 伪影模型
- 金属伪影校正状态
- 病灶模型
- 输出类型：分类/分割
- 链路限制项

前端兼容后端返回的 camelCase 与 snake_case 两种字段命名。

### 4. 验收脚本加强

已更新：

- `scripts/smoke_test_headct_platform.py`
- `scripts/e2e_project2_real_business.py`

新增校验：

- Orchestrator 必须返回 `ai_imaging_status`。
- Project2 必须返回 `aiImagingStatus`。
- 必须能识别质量控制模型和病灶模型状态。
- 端到端结果必须包含项目级 AI 影像链路状态。

## 当前模型链路口径

当前项目可按如下口径描述：

> 本项目已完成头部 CT AI 影像分析链路接入。系统支持 CT 影像上传、金属伪影识别、颅内出血风险分类、RAG/LLM 报告辅助生成、医生审核和报告归档。当前病灶识别输出为分类结果，金属伪影校正 checkpoint 已登记但未执行图像校正，因此项目展示中明确显示模型能力边界。

不建议写成：

> 系统已完成医院级临床诊断上线。

也不建议写成：

> 当前模型已完成出血区域精确分割。

## 验收结果

已执行：

```powershell
python -m pytest HeadCTOrchestrator\tests\test_orchestrator_pipeline.py -q
```

结果：

```text
10 passed
```

已执行：

```powershell
$env:MAVEN_USER_HOME='D:\exam\.maven'
.\mvnw.cmd -q compile -DskipTests -Dmaven.test.skip=true -Dmaven.repo.local=D:\exam\.m2\repository
```

结果：Project2 编译通过。

已执行：

```powershell
npm run build
```

结果：前端构建通过，仅存在既有 chunk size warning。

已执行：

```powershell
python scripts\smoke_test_headct_platform.py
```

关键结果：

```json
{
  "orchestrator_status": "success",
  "lesion_status": "success",
  "ai_imaging_project_status": "ready_for_project_demo",
  "ai_imaging_workflow_ready": true,
  "ai_lesion_task_type": "classification",
  "ai_artifact_reduction_status": "registered_not_executable",
  "report_status": "released",
  "emr_status": "final"
}
```

已执行：

```powershell
python scripts\e2e_project2_real_business.py
```

关键结果：

```json
{
  "status": "success",
  "analysis_confidence": 0.06743263453245163,
  "ai_imaging_project_status": "ready_for_project_demo",
  "ai_imaging_workflow_ready": true,
  "report_service_status": "released",
  "emr_status": "final",
  "persisted": {
    "ai_consultation": 1,
    "ai_diagnosis_suggestion": 2,
    "ai_image_analysis": 1,
    "ai_generated_report": 1
  }
}
```

## 后续可选优化

- 接入真正可执行的 InDuDoNet 推理代码和投影域预处理后，将 `artifact_reduction.status` 从 `registered_not_executable` 升级为 `executable`。
- 若获得出血分割模型或完成 nnU-Net/MONAI 分割训练，可将 `lesion_model.task_type` 从 `classification` 升级为 `segmentation`。
- 前端可在报告生成页面继续展示 `aiImagingStatus`，方便报告医生确认链路状态。
