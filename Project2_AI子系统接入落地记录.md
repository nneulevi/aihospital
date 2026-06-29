# Project2 AI子系统接入落地记录

## 本次完成内容

本轮按 `Project2_主平台整理与AI子系统整合指导.md` 的 P0 目标，完成了 Project2 与头部 CT AI 子系统的最小闭环接入：

```text
检查申请 -> CT影像上传 -> HeadCTOrchestrator分析 -> HeadCTReportService生成报告草稿 -> Project2落库返回
```

## 关键改动

### 1. 配置修正

文件：

```text
Project2/src/main/resources/application.yml
```

已完成：

- 将 `ai.service.mock=false` 修正为代码实际读取的 `ai.mock.enabled=false`；
- 新增 `ai.head-ct.orchestrator-base-url`，默认 `http://127.0.0.1:8010`；
- 新增 `ai.head-ct.report-base-url`，默认 `http://127.0.0.1:8030`；
- 新增轮询超时、HTTP 请求超时、服务调用 actor 配置；
- 将 multipart 上传限制从 `10MB` 提升到 `1024MB`，用于 NIfTI / DICOM ZIP 等医学影像文件。

### 2. 主平台 AI 配置入口

文件：

```text
Project2/src/main/java/com/neuedu/his/config/AIServiceConfig.java
Project2/src/main/java/com/neuedu/his/config/HeadCtAiProperties.java
```

已完成：

- 新增 `HeadCtAiProperties` 集中读取头部 CT AI 子系统配置；
- 注册 `RestClient` Bean；
- `RestClient` 已接入 `request-timeout-seconds`，避免外部服务卡死。

### 3. 外部服务客户端

新增：

```text
Project2/src/main/java/com/neuedu/his/client/HeadCtOrchestratorClient.java
Project2/src/main/java/com/neuedu/his/client/HeadCtReportClient.java
```

已完成：

- `HeadCtOrchestratorClient` 支持 multipart 上传 CT 文件并创建 `/api/head-ct-ai/tasks`；
- 支持查询 task 状态和 result；
- `HeadCtReportClient` 支持调用 `/api/v1/reports/from-analysis/{task_id}`；
- ReportService 调用已补齐 `X-Actor-Id`、`X-Actor-Role`、`X-Request-Id`、`Idempotency-Key`。

### 4. 业务工作流封装

新增：

```text
Project2/src/main/java/com/neuedu/his/service/HeadCtAiWorkflowService.java
```

已完成：

- 将 Project2 的 `checkRequest/register/imageFile` 转换为 AI 子系统所需的 `patient_id/study_id/series_id/report_id/doctor_id`；
- 同步轮询 Orchestrator task；
- 成功后获取分析结果；
- 根据 `task_id` 调用 ReportService 创建报告草稿。

### 5. 影像真实实现

文件：

```text
Project2/src/main/java/com/neuedu/his/service/impl/ImageServiceRealImpl.java
```

已完成：

- `upload` 不再抛出占位异常；
- 上传文件保存到 `uploads/ct/{registerId}`；
- 写入 `ai_image_file`；
- 返回包含 `imageFileId/filePath/fileName` 的 JSON 字符串；
- `analyze` 调用 Orchestrator，保存 AI 结果快照到 `ai_image_analysis.ai_annotation`；
- 返回当前接口所需的 `analysisId/findings/conclusion/confidence/annotations`。

### 6. 报告真实实现

文件：

```text
Project2/src/main/java/com/neuedu/his/service/impl/ReportServiceRealImpl.java
```

已完成：

- `generate` 不再抛出占位异常；
- 根据 `checkRequestId` 查找已有 AI 分析；
- 从 `ai_annotation` 中读取 `task_id`；
- 调用 HeadCTReportService 创建报告草稿；
- 写入 `ai_generated_report`；
- 返回 `reportId/reportContent/status`。

### 7. 上传格式支持

文件：

```text
Project2/src/main/java/com/neuedu/his/util/FileUploadUtil.java
```

已支持：

```text
jpg, jpeg, png, gif, pdf,
nii, gz, dcm, dicom, zip, mha, mhd, nrrd
```

### 8. Bean 冲突与编码修复

已清理以下类上的 `@Service/@Primary`，让 `AIServiceConfig` 成为唯一 Bean 选择入口：

```text
ConsultationServiceMockImpl
DiagnosisServiceMockImpl
ImageServiceMockImpl
ReportServiceMockImpl
ConsultationServiceRealImpl
```

同时修复了若干原有乱码/非法 UTF-8 文件，避免 Maven 编译失败。

### 9. API 测试文件调整

文件：

```text
Project2/api-test.http
```

已完成：

- `@drugstore`、`@ai` 统一为 `http://localhost:8092`；
- AI 上传/分析/报告路径改为：

```text
POST /api/ai/image/upload
POST /api/ai/image/analyze
POST /api/ai/report/generate
```

- 上传示例文件调整为 `sample_head_ct.nii.gz`。

## 编译验证

已执行：

```powershell
$env:MAVEN_USER_HOME='D:\exam\.maven'
.\mvnw.cmd -q -DskipTests "-Dmaven.repo.local=D:\exam\.m2\repository" compile
```

结果：

```text
compile passed
```

## 联调前置条件

在 IDEA 启动 Project2 前，建议先确认：

```text
HeadCTOrchestrator  http://127.0.0.1:8010
HeadCTReportService http://127.0.0.1:8030
```

至少以下健康检查应正常：

```text
http://127.0.0.1:8010/health
http://127.0.0.1:8030/health
```

随后在 IDEA 中启动：

```text
Project2/src/main/java/com/neuedu/his/HisApplication.java
```

再按 `Project2/api-test.http` 依次执行：

```text
10. 开检查申请
11. AI影像上传
12. AI影像分析
13. AI生成报告
```

## 仍需注意

当前为了不改数据库结构，外部 task/result/report 的快照优先写入现有 JSON 字段：

```text
ai_image_analysis.ai_annotation
ai_generated_report.ai_structured_data
```

后续如果要做生产级追踪，建议继续按指导文档增加专用字段：

```text
orchestrator_task_id
orchestrator_status
orchestrator_result_url
report_service_report_id
external_document_id
```


## 2026-06-22 全链路验收补充

本阶段已新增并通过 Project2 主平台入口的真实业务端到端验收。

详见：

```text
Project2_全链路验收进度记录.md
```

关键结论：

- `scripts/start_headct_platform.ps1` 已支持 `-Restart` 自动释放旧监听端口，并纳入 Project2 一键启动。
- `scripts/e2e_project2_real_business.py` 已覆盖问诊、辅助诊断、CT 上传、AI 分析、报告生成、医生审核签发、EMR 分发。
- 本次验收结果为 `status=success`，ReportService 报告状态为 `released`，EMR 状态为 `final`。

## 2026-06-24 Frontend Gap API and JWT Completion

See details:

```text
Project2_前端缺口接口补全与JWT接入记录.md
```

Completed backend endpoints:

```text
POST /api/auth/send-code
POST /api/auth/login-by-code
POST /api/patient/send-code
POST /api/patient/auth/register
POST /api/patient/logout
POST /api/patient/switch
GET  /api/patient/list
```

Verification:

- `AuthPatientContractTest` passed.
- Project2 full Maven test passed.
- Temporary OpenAPI check showed `missing=[]`.
- Frontend API export reverse check showed `frontendExports=41`, `backendMapped=41`, `gaps=[]`.

JWT status:

- Employee password login, employee code login, patient code login, patient auth register/login, and patient switch all return JWT.
- Patient JWT claims include `patientId`, `phone`, `caseNumber`, and `roleType=PATIENT`.
