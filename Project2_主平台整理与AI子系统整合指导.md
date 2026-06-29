# Project2 主平台整理与 AI 子系统整合指导

## 1. 文档目标

本文用于整理 `Project2` 当前 Spring Boot 主平台内容，并给出与现有头部 CT AI 子系统的下一步整合方案。

约束：

- `.java` 文件运行、调试和启动以本机 IDEA 环境为准；
- 本文优先保证最小可落地链路打通；
- 在最小落地基础上，保留真实业务场景的扩展方向。

## 2. Project2 当前定位

`Project2` 是“智慧云脑诊疗平台”的 Java 主平台后端，当前包含：

- 患者端：挂号、退号、缴费项目、病历查看；
- 医生端：待诊列表、病历保存、开检查、开检验、开处置、开处方、门诊确诊；
- 管理员端：收费、费用记录、日结、药房库存、发药、退药；
- AI 模块：AI 问诊、AI 辅助诊断、AI 影像上传/分析、AI 检查报告、AI 排班；
- 基础能力：JWT 登录、全局响应、全局异常、MyBatis、PostgreSQL、分页、OpenAPI。

当前项目结构符合典型 Spring Boot 分层：

```text
controller  -> HTTP 接口层
service     -> 业务接口
service/impl -> mock/real 实现
mapper      -> MyBatis 数据访问
model/dto   -> 请求参数
model/vo    -> 响应对象
model/entity -> 数据库实体
resources/mapper -> XML Mapper
```

## 3. 技术栈与依赖

当前 `pom.xml` 主要技术栈：

| 类别 | 依赖/版本 | 用途 |
| --- | --- | --- |
| Java | 17 | 主平台运行环境 |
| Spring Boot | 3.4.7 | Web 后端基础 |
| Spring Web | starter-web | REST API |
| MyBatis | mybatis-spring-boot-starter 3.0.4 | 数据访问 |
| PostgreSQL | org.postgresql | 主平台数据库 |
| PageHelper | 2.1.0 | 分页 |
| Lombok | 1.18.36 | DTO/VO/Entity 简化 |
| Jakarta Validation | 3.0.2 | 参数校验 |
| Hibernate Validator | 8.0.2.Final | 参数校验实现 |
| JJWT | 0.12.6 | JWT 登录 |
| Actuator | starter-actuator | 健康检查 |
| SpringDoc | 2.6.0 | Swagger/OpenAPI |

当前 `application.yml` 关键配置：

```yaml
server:
  port: 8092

spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/hospital
    username: postgres
    password: root

file:
  upload:
    path: ./uploads
```

需要注意：当前配置中写的是：

```yaml
ai:
  service:
    mock: false
```

但 `AIServiceConfig.java` 判断的是：

```java
@ConditionalOnProperty(name = "ai.mock.enabled", ...)
```

两者不一致。结果是：即使配置 `ai.service.mock=false`，也可能仍然加载 mock Bean。

建议统一为：

```yaml
ai:
  mock:
    enabled: false
```

或修改 Java 配置读取 `ai.service.mock`。为了少改代码，优先建议修改 YAML。

## 4. 已有 AI 子系统

当前外部 AI 子系统已经具备较完整链路：

| 子系统 | 默认端口 | 作用 |
| --- | ---: | --- |
| Filter | 8000 | 头部 CT 金属伪影识别 |
| HeadCTLesionDetection | 8021 | 病灶识别，支持本地模型、VinBigData adapter |
| HeadCTOrchestrator | 8010 | AI 编排入口，主平台优先接它 |
| HeadCTReportService | 8030 | 报告草稿、审核、签署、发布、Outbox |
| HeadCTEMRService | 8040 | 本地 EMR 后端，承接报告发布入库 |
| PostgreSQL/pgvector | 本机 | RAG 知识库、报告、审计、EMR 数据 |
| DashScope | 外部 HTTPS | Embedding、Rerank、LLM 报告增强 |

主平台业务代码不应直接调用 Filter、LesionDetection 或 RAG 数据库。推荐只直接调用：

```text
HeadCTOrchestrator
HeadCTReportService
```

## 5. 当前 Project2 与 AI 子系统的差距

### 5.1 AI real 实现仍未接入

以下类目前仍是占位：

```text
ImageServiceRealImpl.java
ReportServiceRealImpl.java
DiagnosisServiceRealImpl.java
ConsultationServiceRealImpl.java
```

其中与头部 CT 子系统最相关的是：

```text
ImageServiceRealImpl.java
ReportServiceRealImpl.java
```

当前实现：

```java
throw new UnsupportedOperationException("真实AI模型待接入");
```

下一步应优先替换这两个类，而不是先扩展新接口。

### 5.2 当前 DTO/VO 字段偏简单

现有 `ImageAnalyzeResponseVO`：

```text
analysisId
findings
conclusion
confidence
annotations
```

外部 Orchestrator 实际会返回：

```text
task_id
status
quality_control
lesion_analysis
report_assist
warnings
analysis_reliability
```

因此建议扩展 VO，至少增加：

```text
orchestratorTaskId
aiStatus
reportSuggestion
reliability
maskUrl
previewUrls
warnings
rawResultJson
```

### 5.3 数据库表缺少跨服务映射字段

现有实体：

```text
AiImageFile
AiImageAnalysis
AiGeneratedReport
```

建议增加或新建映射字段：

```text
orchestrator_task_id
orchestrator_status
orchestrator_result_url
report_service_report_id
external_document_id
ai_raw_result_json
ai_pipeline_status
```

最小落地可先只加在 `ai_image_analysis` 和 `ai_generated_report` 中。

## 6. 推荐最小整合链路

优先打通这条链路：

```text
医生开检查申请
 -> Project2 上传 CT 文件
 -> Project2 调 HeadCTOrchestrator 创建 AI 任务
 -> Project2 轮询任务状态
 -> 成功后 Project2 调 HeadCTReportService 绑定检查与 AI 任务
 -> 返回报告草稿
 -> 医生端编辑/审核/签署/发布
 -> ReportService Outbox 写入 EMR
```

与当前 `api-test.http` 对应：

```text
10. 开检查申请
11. AI影像上传
12. AI影像分析
13. AI生成报告
```

建议先改造 11、12、13 三步，不动门诊、收费、药房等已经存在的业务。

## 7. Project2 配置建议

在 `application.yml` 增加：

```yaml
ai:
  mock:
    enabled: false
  head-ct:
    orchestrator-base-url: http://127.0.0.1:8010
    report-base-url: http://127.0.0.1:8030
    poll-interval-ms: 1000
    timeout-seconds: 300
    request-timeout-seconds: 30
```

同时将 multipart 放宽，支持 NIfTI/DICOM ZIP：

```yaml
spring:
  servlet:
    multipart:
      max-file-size: 1024MB
      max-request-size: 1024MB
```

当前 `10MB` 对 CT 影像明显不够。

## 8. 需要新增的 Java 组件

### 8.1 配置类

新增：

```text
com.neuedu.his.config.HeadCtAiProperties
```

字段：

```text
orchestratorBaseUrl
reportBaseUrl
pollIntervalMs
timeoutSeconds
requestTimeoutSeconds
```

### 8.2 HTTP 客户端

新增：

```text
com.neuedu.his.client.HeadCtOrchestratorClient
com.neuedu.his.client.HeadCtReportClient
```

建议使用 Spring Boot 3 自带的 `RestClient`，或使用 `WebClient`。

如果使用 `RestClient`，需要在配置中提供 Bean：

```java
@Bean
public RestClient restClient(RestClient.Builder builder) {
    return builder.build();
}
```

### 8.3 工作流服务

新增：

```text
com.neuedu.his.service.HeadCtAiWorkflowService
```

职责：

```text
uploadAndCreateTask(...)
pollTask(...)
createDraftReportAfterSuccess(...)
syncReportStatus(...)
```

`ImageServiceRealImpl` 只负责调用这个工作流，不直接拼复杂 HTTP 逻辑。

## 9. ImageServiceRealImpl 改造建议

### 9.1 upload

当前：

```java
throw new UnsupportedOperationException("真实AI模型待接入");
```

建议最小实现：

1. 保存上传文件到 `uploads/`；
2. 插入 `ai_image_file`；
3. 返回 `imageFileId`。

当前 controller 返回 `String`，建议后续改为结构化 VO；若为了最小改造，可先返回：

```json
{"imageFileId":1,"filePath":"..."}
```

### 9.2 analyze

建议流程：

1. 根据 `imageFileId` 查询 `ai_image_file`；
2. 调用 `HeadCTOrchestrator /api/head-ct-ai/tasks` 上传文件；
3. 保存 `orchestrator_task_id`；
4. 后台轮询或同步轮询任务；
5. 成功后读取 result；
6. 写入 `ai_image_analysis`；
7. 返回 `ImageAnalyzeResponseVO`。

最小实现可以先同步轮询，真实场景再改异步任务。

## 10. ReportServiceRealImpl 改造建议

当前 Project2 的 `AiReportController` 是：

```text
POST /api/ai/report/generate
```

最小整合方式：

1. 根据 `checkRequestId` 查询已经成功的 `ai_image_analysis`；
2. 取其中 `orchestrator_task_id`；
3. 调用 `HeadCTReportService` 登记检查或绑定分析结果；
4. 获取报告草稿；
5. 写入 `ai_generated_report`；
6. 返回 `ReportGenerateResponseVO`。

建议不要让 Project2 自己根据 AI JSON 生成报告正文，因为外部 ReportService 已经包含：

```text
AI 草稿
RAG 增强
医生审核
签署
发布
EMR Outbox
```

Project2 应作为主平台业务入口，而不是重复实现报告生命周期。

## 11. 数据库最小改造建议

建议新增迁移脚本：

```sql
ALTER TABLE ai_image_file
  ADD COLUMN IF NOT EXISTS source_format VARCHAR(32),
  ADD COLUMN IF NOT EXISTS study_id VARCHAR(64),
  ADD COLUMN IF NOT EXISTS series_id VARCHAR(64);

ALTER TABLE ai_image_analysis
  ADD COLUMN IF NOT EXISTS orchestrator_task_id VARCHAR(64),
  ADD COLUMN IF NOT EXISTS orchestrator_status VARCHAR(32),
  ADD COLUMN IF NOT EXISTS orchestrator_result_url TEXT,
  ADD COLUMN IF NOT EXISTS analysis_reliability VARCHAR(64),
  ADD COLUMN IF NOT EXISTS mask_url TEXT,
  ADD COLUMN IF NOT EXISTS preview_urls TEXT,
  ADD COLUMN IF NOT EXISTS warnings TEXT,
  ADD COLUMN IF NOT EXISTS ai_raw_result_json TEXT;

ALTER TABLE ai_generated_report
  ADD COLUMN IF NOT EXISTS report_service_report_id VARCHAR(64),
  ADD COLUMN IF NOT EXISTS external_document_id VARCHAR(128),
  ADD COLUMN IF NOT EXISTS report_status VARCHAR(32),
  ADD COLUMN IF NOT EXISTS report_raw_snapshot TEXT;
```

## 12. 接口整合建议

当前 Project2 接口可保持不变：

```text
POST /api/ai/image/upload
POST /api/ai/image/analyze
POST /api/ai/report/generate
```

内部实现替换为真实服务调用。

后续可新增查询接口：

```text
GET /api/ai/image/analysis/{analysisId}
GET /api/ai/image/check-request/{checkRequestId}/latest
GET /api/ai/report/{reportId}
POST /api/ai/report/{reportId}/submit-review
POST /api/ai/report/{reportId}/sign
POST /api/ai/report/{reportId}/release
```

这些接口可以转发或包装 `HeadCTReportService`。

## 13. 联调启动顺序

先启动 AI 子系统：

```powershell
.\scripts\start_headct_platform.ps1
```

检查：

```powershell
.\scripts\check_headct_platform.ps1
```

确认至少：

```text
HeadCTOrchestrator 8010 ok
HeadCTReportService 8030 ok
```

再用 IDEA 启动 `Project2`：

```text
HisApplication.java
```

启动后访问：

```text
http://localhost:8092/actuator/health
http://localhost:8092/swagger-ui/index.html
```

## 14. api-test.http 调整建议

当前文件里分了：

```text
@outpatient = http://localhost:8092
@drugstore = http://localhost:8091
@ai = http://localhost:8093
```

但当前 Project2 是一个 Spring Boot 应用，默认端口为 `8092`，没有看到独立 `8091/8093` 模块。

建议最小调整：

```text
@outpatient = http://localhost:8092
@drugstore = http://localhost:8092
@ai = http://localhost:8092
```

如果未来拆分服务，再恢复多个端口。

## 15. 下一步任务清单

### P0：打通链路

1. 修正 `application.yml` 中 mock 配置名；
2. 放宽 multipart 文件大小；
3. 新增 `HeadCtAiProperties`；
4. 新增 `HeadCtOrchestratorClient`；
5. 新增 `HeadCtReportClient`；
6. 改造 `ImageServiceRealImpl.upload`；
7. 改造 `ImageServiceRealImpl.analyze`；
8. 改造 `ReportServiceRealImpl.generate`；
9. 调整 `api-test.http` 的端口；
10. 用一例 `.nii.gz` 或 DICOM ZIP 完成 10 -> 11 -> 12 -> 13 联调。

### P1：贴近真实业务

1. AI 分析改异步任务；
2. Project2 保存 `orchestrator_task_id` 和 `report_service_report_id`；
3. 医生端展示 AI 质控、病灶概率、报告草稿和警告；
4. 接入 ReportService 的审核、签署、发布接口；
5. 展示 EMR `external_document_id`。

### P2：生产化准备

1. 接入统一认证网关；
2. 服务间调用加入 Token 或内网白名单；
3. 上传文件改对象存储或 PACS/DICOMweb；
4. AI 分析状态增加失败重试；
5. 对患者隐私字段脱敏；
6. 用正式模型权重替换 smoke 模型。

## 16. 验收标准

最小验收：

1. IDEA 能启动 Project2；
2. `/actuator/health` 正常；
3. 医生开检查申请成功；
4. 上传一例 CT 文件成功；
5. Project2 调 Orchestrator 创建任务成功；
6. Project2 获取 AI 分析结果成功；
7. Project2 调 ReportService 生成报告草稿成功；
8. 数据库能保存 `imageFileId`、`analysisId`、`orchestratorTaskId`、`reportId`；
9. 任一 AI 服务不可用时，Project2 返回明确错误，不抛裸 `UnsupportedOperationException`；
10. `.http` 文件能跑通 10、11、12、13 四个步骤。

## 17. 结论

Project2 已具备主平台基础业务框架，当前最关键问题不是重新开发 AI 能力，而是把已有
`HeadCTOrchestrator` 与 `HeadCTReportService` 接入 Project2 的 AI 影像和 AI 报告接口。

建议下一步只聚焦一个闭环：

```text
开检查申请 -> 上传 CT -> AI 分析 -> 生成报告草稿
```

这条链路打通后，再扩展医生审核、签署、发布和 EMR 入库。
