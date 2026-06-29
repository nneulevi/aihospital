# Project2 头部 CT 正常业务链路验收记录

更新时间：2026-06-27

## 1. 验收口径

本记录不使用旧的微服务轻量验收脚本作为头部 CT AI、报告、EMR 链路验收依据。

验收改为正常工作环境链路：

```text
Project2 主平台
-> 创建门诊头颅 CT 业务上下文
-> AI 问诊
-> AI 辅助诊断
-> CT 影像上传
-> AI 影像分析
-> HeadCTOrchestrator 编排 Filter / Lesion / RAG / LLM
-> Project2 生成 AI 报告
-> HeadCTReportService 报告草稿
-> 医生修改
-> 提交审核
-> 审核通过
-> 签名
-> 发布
-> HeadCTEMRService 归档
-> Project2 数据库回查持久化记录
```

## 2. 脚本调整

脚本：

```text
scripts/e2e_project2_real_business.py
```

调整内容：

- 样本 CT 从独立正式验收目录读取：

```text
testdata/headct/head_ct_positive_case.nii.gz
```

- 支持通过环境变量覆盖：

```powershell
$env:HEADCT_E2E_SAMPLE_CT="D:\path\to\case.nii.gz"
```

- 去掉运行时自动 `CREATE TABLE IF NOT EXISTS` 兜底。
- 启动时检查真实数据库表是否已经存在；缺表则直接失败，提示先执行数据库初始化。

## 3. 本轮执行命令

```powershell
python scripts\e2e_project2_real_business.py
```

## 4. 本轮通过证据

输出摘要：

```json
{
  "status": "success",
  "business_case": {
    "patient_id": 65,
    "register_id": 72,
    "medical_record_id": 40,
    "check_request_id": 46,
    "case_suffix": "76fa2fa640"
  },
  "health": {
    "project2": "UP",
    "orchestrator": "ok",
    "report": "ok",
    "emr": "ok"
  },
  "consultation_id": 24,
  "consultation_recommendation_count": 2,
  "diagnosis_suggestion_count": 2,
  "image_file_id": 23,
  "analysis_id": 23,
  "analysis_confidence": 0.06743263453245163,
  "ai_imaging_project_status": "ready_for_project_demo",
  "ai_imaging_workflow_ready": true,
  "report_id": 22,
  "project2_report_status": "draft",
  "report_service_id": "5fef8c27-65c1-417b-a20a-f2e21da39b1a",
  "report_service_status": "released",
  "report_version_after_review": 2,
  "emr_document_id": "DR-DF4264D254C74043AE37B388FA1B27C5",
  "emr_status": "final",
  "persisted": {
    "ai_consultation": 1,
    "ai_diagnosis_suggestion": 2,
    "ai_image_analysis": 1,
    "ai_generated_report": 1
  }
}
```

## 5. 结论

头部 CT AI、报告、EMR 链路已按正常工作环境从 Project2 主平台入口完成验收：

- 不是单独调用 AI 微服务的轻量验收。
- 不是仅健康检查。
- 不是只验证 Orchestrator。
- 已覆盖 Project2 业务入口、AI 分析、报告审核状态机、EMR 归档和数据库持久化回查。

后续验收该链路时，应优先运行：

```powershell
python scripts\e2e_project2_real_business.py
```

## 6. 截图级证据补充

用户指出原验收记录看不到上传 CT 图像、病灶识别、AI 辅助结论、归档截图。本轮已补充专项视觉验收。

命令：

```powershell
npx playwright test -c playwright.config.ts tests/visual/headct-workflow-screenshots.spec.ts --project=desktop-chrome
```

结果：

```text
1 passed
```

截图目录：

```text
frontend/visual-results/headct-workflow
```

截图清单：

```text
desktop-chrome-01-upload-ct-image.png
desktop-chrome-02-lesion-recognition.png
desktop-chrome-03-ai-assisted-conclusion-and-report.png
desktop-chrome-04-report-released.png
desktop-chrome-05-emr-archive.png
```

对应关系：

- `01-upload-ct-image`：医生接诊页上传 CT 图像，显示检查申请 ID、影像文件 ID、文件名和上传成功。
- `02-lesion-recognition`：医生接诊页显示 AI 识别结果、病灶模型、伪影模型、链路状态和限制说明。
- `03-ai-assisted-conclusion-and-report`：医生接诊页显示影像所见、AI 结论、置信度和 AI 报告内容。
- `04-report-released`：报告服务返回发布后的报告详情，状态为 `released`。
- `05-emr-archive`：EMR 服务返回归档后的诊断报告详情，状态为 `final`。

## 7. 本轮真实逻辑问题修复

本轮截图验收暴露并修复了两个真实链路问题：

1. Project2 医生接诊页上传影像后，若后端返回对象，前端可能将 `imageFileId` 显示为 `[object Object]`。现已改为读取 `imageFileId/id`，并兼容字符串 JSON。
2. 同一检查申请重复 AI 分析/生成报告时：
   - Project2 查询最新影像分析时按 `analysis_time DESC, id DESC LIMIT 1` 获取最新记录；
   - Project2 查询最新 AI 报告时按 `generation_time DESC, id DESC LIMIT 1` 获取最新记录；
   - HeadCTReportService 对同一检查单已有主报告时返回已有报告，避免唯一约束冲突。

复验：

```text
npm run build -> 通过
headct-workflow-screenshots.spec.ts -> 1 passed
python scripts\e2e_project2_real_business.py -> status=success, report_service_status=released, emr_status=final
```
