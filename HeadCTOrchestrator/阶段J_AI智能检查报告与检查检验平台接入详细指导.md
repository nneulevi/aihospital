# 阶段 J：AI 智能检查报告与检查检验平台接入详细指导

## 1. 阶段结论

参考项目业务模块图 `project.png`，在已经完成以下能力后：

- 头部 CT 影像预处理与伪影识别；
- 病灶识别服务和上级 Orchestrator 编排；
- RAG 知识检索、向量召回、重排和外部 LLM 报告辅助；
- 医生审核接口与基本审核记录；

下一步应进入 **AI 智能检查报告业务化及检查检验平台接入** 阶段。

本阶段不是继续堆叠模型，而是将 AI 输出转化为可被医院业务使用的正式流程：

```text
检查申请/影像检查
    -> 头部 CT AI 分析
    -> AI 报告草稿
    -> 医生编辑与审核
    -> 医生签署
    -> 正式检查报告
    -> 检查检验模块/电子病历
```

核心目标是让当前“能生成结果”的系统，升级为“结果可管理、可审核、可签署、可追溯、可被上级平台调用”的报告系统。

---

## 2. 与项目业务图的对应关系

`project.png` 中与本阶段直接相关的业务节点为：

```text
头部 CT 医学影像识别
    -> AI 智能检查报告
    <-> 检查 | 检验
    -> 门诊/电子病历
```

因此，当前 RAG 和医生审核能力只完成了“AI 智能检查报告”的生成基础，尚缺少：

1. 检查申请、影像检查和 AI 任务之间的业务标识关联；
2. 正式报告数据库和版本管理；
3. 医生工作列表、编辑、审核、签署和退回流程；
4. 报告发布、补充报告和撤回控制；
5. 与检查检验模块、电子病历的接口；
6. 身份认证、权限控制、审计和操作留痕；
7. 失败重试、幂等处理和服务监控。

---

## 3. 模块边界

建议在项目根目录新建独立兄弟模块：

```text
HeadCTReportService/
```

不要将正式报告业务继续堆入 `Filter`、`HeadCTLesionDetection` 或 `HeadCTOrchestrator`。

各模块职责应保持清晰：

| 模块 | 职责 |
| --- | --- |
| `Filter` | CT 图像质量与金属伪影处理 |
| `HeadCTLesionDetection` | 病灶模型推理及结构化识别结果 |
| `HeadCTOrchestrator` | 编排各 AI 服务，生成统一分析结果和报告辅助内容 |
| `HeadCTReportService` | 报告草稿、版本、审核、签署、发布和平台接入 |
| 上级业务平台 | 患者、医生、挂号、门诊、检查申请和电子病历管理 |

原则：**Orchestrator 负责 AI 结论，ReportService 负责医疗报告生命周期。**

---

## 4. 推荐目录结构

```text
HeadCTReportService/
├── ReportServer.py
├── config.py
├── db.py
├── schemas.py
├── exceptions.py
├── requirements.txt
├── README.md
├── migrations/
│   ├── 001_create_report_tables.sql
│   └── 002_create_report_indexes.sql
├── repositories/
│   ├── report_repository.py
│   ├── review_repository.py
│   └── audit_repository.py
├── services/
│   ├── report_service.py
│   ├── review_service.py
│   ├── signature_service.py
│   └── integration_service.py
├── service_clients/
│   ├── orchestrator_client.py
│   ├── examination_client.py
│   └── emr_client.py
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
└── tests/
    ├── test_report_contract.py
    ├── test_report_workflow.py
    ├── test_orchestrator_adapter.py
    └── test_emr_integration.py
```

初期可沿用 FastAPI；生产数据使用 PostgreSQL，不再使用 JSON 文件作为正式报告和审核记录的主存储。

---

## 5. 核心数据模型

### 5.1 检查任务 `examination_orders`

建议字段：

- `id`：内部主键；
- `order_id`：上级检查申请 ID；
- `study_id`：影像检查 ID；
- `accession_number`：检查流水号；
- `patient_id`：患者标识，测试环境可使用脱敏 ID；
- `patient_name`：仅在合规环境保存；
- `department`：申请科室；
- `ordering_doctor_id`：申请医生；
- `study_instance_uid`：DICOM Study UID，后续接入 DICOM 时使用；
- `status`：检查业务状态；
- `created_at`、`updated_at`。

### 5.2 AI 分析快照 `ai_analysis_snapshots`

正式报告不能只引用可能变化的 AI 任务结果，应保存生成报告时的只读快照：

- `id`；
- `examination_order_id`；
- `orchestrator_task_id`；
- `pipeline_version`；
- `model_versions`；
- `quality_control_json`；
- `lesion_analysis_json`；
- `report_assist_json`；
- `rag_references_json`；
- `source_result_hash`；
- `created_at`。

不得在此表保存阿里百炼 API Key、完整系统提示词或数据库口令。

### 5.3 报告主表 `medical_reports`

- `id`：报告 ID；
- `examination_order_id`；
- `ai_snapshot_id`；
- `current_version_id`；
- `status`；
- `assigned_doctor_id`；
- `reviewer_doctor_id`；
- `signed_by`；
- `signed_at`；
- `released_at`；
- `created_at`、`updated_at`。

### 5.4 报告版本 `medical_report_versions`

- `id`；
- `report_id`；
- `version_number`；
- `findings`：影像所见；
- `impression`：诊断意见；
- `recommendations`：建议；
- `editor_id`；
- `change_reason`；
- `source_type`：`ai_draft`、`doctor_edit`、`amendment`；
- `content_hash`；
- `created_at`。

已签署版本必须只读，修改时创建新版本，不覆盖历史内容。

### 5.5 审核记录 `report_reviews`

- `id`；
- `report_id`；
- `report_version_id`；
- `reviewer_id`；
- `decision`：通过、退回、请求修订；
- `comment`；
- `created_at`。

### 5.6 审计事件 `report_audit_events`

记录报告创建、编辑、提交、审核、签署、发布、导出、推送和补充报告等事件：

- `actor_id`；
- `actor_role`；
- `action`；
- `target_type`；
- `target_id`；
- `request_id`；
- `client_ip`；
- `before_hash`、`after_hash`；
- `created_at`。

---

## 6. 状态机设计

### 6.1 检查状态

```text
ordered
 -> acquired
 -> ai_analyzing
 -> ai_completed
 -> reporting
 -> reported
 -> archived
```

异常状态包括：

- `ai_failed`；
- `report_rejected`；
- `integration_failed`；
- `cancelled`。

### 6.2 报告状态

```text
draft
 -> pending_review
 -> revision_required
 -> pending_review
 -> approved
 -> signed
 -> released
```

发布后如需修改：

```text
released -> amendment_draft -> amendment_signed -> released
```

必须遵守以下约束：

- AI 只能创建 `draft`，不能直接签署或发布；
- 提交审核后，当前版本应锁定或采用乐观锁；
- 签署必须由具有权限的医生执行；
- 已发布报告不能直接覆盖，只能创建补充报告；
- 每次状态变化必须写入审计事件。

---

## 7. Orchestrator 接入方式

### 7.1 推荐调用方向

推荐由报告服务主动读取已完成的 Orchestrator 任务，或由上级平台在确认任务成功后创建报告：

```text
上级平台
 -> 创建 Orchestrator 分析任务
 -> 轮询/接收任务完成事件
 -> 调用 ReportService 创建报告草稿
```

不建议让 Orchestrator 直接承担报告状态管理。

### 7.2 创建草稿接口

```http
POST /api/v1/reports/from-analysis/{task_id}
Idempotency-Key: <业务幂等键>
```

请求体至少包含：

```json
{
  "order_id": "ORDER-20260615-001",
  "study_id": "STUDY-20260615-001",
  "patient_id": "PATIENT-DEIDENTIFIED-001",
  "assigned_doctor_id": "doctor-001"
}
```

处理步骤：

1. 检查幂等键和 `task_id` 是否已创建报告；
2. 从 Orchestrator 获取任务状态与统一结果；
3. 仅允许消费 `succeeded` 状态；
4. 校验质量控制、病灶结果和报告辅助结构；
5. 保存 AI 分析快照；
6. 根据 `report_assist` 创建初始报告版本；
7. 写入 `report_created_from_ai` 审计事件；
8. 返回报告 ID、版本号和状态。

### 7.3 输入字段映射

报告服务应消费以下 Orchestrator 结果：

- `task_id`；
- `case_context`；
- `quality_control`；
- `lesion_analysis`；
- `report_assist`；
- `rag_context` 或引用来源；
- 模型和管线版本；
- 各阶段警告、失败信息和降级标识。

对于质量不合格、模型缺失或结果置信度不足的任务，报告必须显示明确警示，不能包装为确定诊断。

---

## 8. 报告服务 API

### 8.1 工作列表

```http
GET /api/v1/reports?status=pending_review&doctor_id=doctor-001
```

支持按状态、医生、科室、检查时间、患者脱敏标识和检查流水号筛选。

### 8.2 查询报告

```http
GET /api/v1/reports/{report_id}
GET /api/v1/reports/{report_id}/versions
GET /api/v1/reports/{report_id}/audit-events
GET /api/v1/reports/{report_id}/references
```

### 8.3 编辑草稿

```http
PATCH /api/v1/reports/{report_id}/draft
If-Match: <version-or-etag>
```

使用版本号或 ETag 防止多个医生覆盖彼此修改。

### 8.4 审核和签署

```http
POST /api/v1/reports/{report_id}/submit-review
POST /api/v1/reports/{report_id}/approve
POST /api/v1/reports/{report_id}/request-revision
POST /api/v1/reports/{report_id}/sign
POST /api/v1/reports/{report_id}/release
POST /api/v1/reports/{report_id}/amendments
```

审核、签署和发布接口必须校验当前用户、角色、报告状态及目标版本。

---

## 9. 检查检验模块接入

检查检验模块是本阶段最重要的上级业务入口，至少要统一以下标识：

| 标识 | 用途 |
| --- | --- |
| `order_id` | 检查申请唯一标识 |
| `study_id` | 本次影像检查标识 |
| `accession_number` | 医院检查流水号 |
| `patient_id` | 患者标识 |
| `orchestrator_task_id` | AI 分析任务标识 |
| `report_id` | 正式报告标识 |

建议定义两个平台接口：

```http
POST /api/v1/integrations/examinations
POST /api/v1/integrations/examinations/{study_id}/analysis
```

第一接口登记检查上下文，第二接口启动或绑定 AI 分析任务。

检查检验模块查询报告时，不应直接读取 Orchestrator 内部文件，而应调用 ReportService。

---

## 10. 电子病历接入

只有 `signed` 或 `released` 的报告可以同步到电子病历。

推荐采用可靠事件或 Outbox 模式：

```text
报告签署
 -> 本地事务写入报告状态和 outbox_event
 -> 后台投递任务推送电子病历
 -> 成功后记录外部文档 ID
 -> 失败时指数退避重试并告警
```

必须具备：

- 幂等键，避免重复写入电子病历；
- 推送失败重试；
- 失败人工补偿入口；
- 请求与响应摘要审计；
- 患者和检查标识一致性校验；
- 接口超时、熔断和访问日志。

若上级平台采用医疗互操作标准，可将报告映射为 `DiagnosticReport`，影像检查映射为 `ImagingStudy`，结构化发现映射为 `Observation`；具体字段以平台现有规范为准。

---

## 11. 医生报告工作台

阶段 J 应同步提供医生端页面，不仅提供后端接口。

### 11.1 页面布局

建议使用三栏或两栏可伸缩布局：

- 左侧：待审核、待修订、已签署报告工作列表；
- 中间：CT 关键切片或当前已有预览结果；
- 右侧：AI 结构化发现、报告编辑器、RAG 引用和审核操作。

### 11.2 必备功能

- 按状态和时间筛选工作列表；
- 展示图像质量和伪影警告；
- 展示病灶类别、概率及不确定性；
- 编辑“影像所见”“诊断意见”“建议”；
- 查看 RAG 引用来源，但不允许引用替代医生判断；
- AI 草稿与医生修改差异对比；
- 提交审核、退回、通过、签署；
- 查看历史版本和审计记录；
- 网络失败时保留未提交编辑内容；
- 对签署、发布和补充报告进行二次确认。

### 11.3 页面安全提示

页面应固定显示：

- AI 结果仅供辅助；
- 当前是否使用真实模型权重；
- 图像质量是否合格；
- 报告是否已由医生签署；
- 引用知识的来源和更新时间。

---

## 12. 身份、权限和安全

至少定义以下角色：

| 角色 | 权限 |
| --- | --- |
| `technician` | 登记检查、启动 AI 分析、查看处理状态 |
| `reporting_doctor` | 编辑草稿、提交审核 |
| `reviewing_doctor` | 审核、退回、批准 |
| `signing_doctor` | 签署和补充报告 |
| `administrator` | 配置、任务分配、审计查询，不默认拥有诊断签署权 |
| `integration_service` | 受限的系统间接口调用 |

安全要求：

- 使用统一身份认证，不从请求体直接信任 `doctor_id`；
- 服务间调用使用独立凭证；
- API Key、数据库密码只通过环境变量或密钥管理服务配置；
- 日志中脱敏患者姓名、身份证号、手机号等信息；
- 所有报告读取、导出、签署和发布行为留痕；
- 签署接口应具备短时令牌或再次认证机制；
- 开发和测试数据不得混入生产数据库。

---

## 13. 异常处理

建议统一错误结构：

```json
{
  "error": {
    "code": "REPORT_STATE_CONFLICT",
    "message": "当前报告状态不允许执行该操作",
    "request_id": "...",
    "details": {}
  }
}
```

重点错误码：

- `ANALYSIS_TASK_NOT_FOUND`；
- `ANALYSIS_NOT_COMPLETED`；
- `ANALYSIS_RESULT_INVALID`；
- `REPORT_ALREADY_EXISTS`；
- `REPORT_STATE_CONFLICT`；
- `REPORT_VERSION_CONFLICT`；
- `REVIEW_PERMISSION_DENIED`；
- `SIGNATURE_REQUIRED`；
- `EMR_PUSH_FAILED`；
- `EXAMINATION_ID_MISMATCH`。

---

## 14. 测试方案

### 14.1 单元测试

- 状态机合法与非法转换；
- 报告版本创建和内容哈希；
- 权限检查；
- Orchestrator 结果字段映射；
- 幂等创建；
- AI 风险提示保留；
- 签署后禁止原地修改。

### 14.2 数据库集成测试

- PostgreSQL 迁移可重复执行；
- 报告、版本、审核和审计事件事务一致；
- 乐观锁冲突正确返回；
- Outbox 投递成功和失败重试；
- 重复回调不会生成重复报告。

### 14.3 契约测试

- Orchestrator 成功、失败和部分结果契约；
- 检查检验模块的标识映射；
- 电子病历推送请求结构；
- API 错误结构和状态码；
- 前端依赖字段保持兼容。

### 14.4 端到端测试

至少覆盖以下完整流程：

```text
登记检查
 -> 创建 AI 任务
 -> AI 分析成功
 -> 创建报告草稿
 -> 医生修改
 -> 提交审核
 -> 审核通过
 -> 医生签署
 -> 发布报告
 -> 推送电子病历
 -> 查询版本与审计记录
```

还应覆盖 AI 失败、低质量图像、审核退回、并发编辑、电子病历暂时不可用和补充报告流程。

---

## 15. 分阶段实施计划

### J0：契约和数据库设计

- 确定检查、任务、报告三类主标识；
- 固化 Orchestrator 输出契约；
- 完成 PostgreSQL 表和迁移脚本；
- 完成报告状态机和权限矩阵。

交付物：数据库设计、API 契约、状态机测试。

### J1：报告服务基础能力

- 新建 `HeadCTReportService`；
- 实现从 Orchestrator 任务创建 AI 报告草稿；
- 实现报告查询、编辑、版本和审计；
- 将现有 JSON 审核能力迁移到 PostgreSQL。

交付物：可运行的报告服务和自动化测试。

### J2：医生审核与签署闭环

- 实现工作列表；
- 实现提交、退回、批准、签署和补充报告；
- 接入身份认证和 RBAC；
- 完成并发编辑控制。

交付物：可由医生完成报告生命周期的前后端功能。

### J3：检查检验模块接入

- 对接检查申请和检查流水号；
- 建立检查任务、AI 任务和报告映射；
- 提供报告状态和结果查询接口；
- 完成幂等、超时和错误补偿。

交付物：检查检验模块可发起分析并读取报告。

### J4：电子病历接入

- 实现已签署报告推送；
- 建立 Outbox 和失败重试；
- 支持外部文档 ID 回写；
- 完成补充报告同步策略。

交付物：正式报告可稳定进入电子病历。

### J5：生产化验收

- 完成权限、审计、脱敏和密钥管理检查；
- 完成压力、故障恢复和接口降级测试；
- 完成临床测试账号与测试数据隔离；
- 输出部署、回滚、监控和操作手册。

---

## 16. 验收标准

阶段 J 完成需同时满足：

1. 可根据一个成功的 Orchestrator 任务创建唯一报告草稿；
2. 报告与 `order_id`、`study_id`、`task_id` 能稳定关联；
3. 医生可以编辑、提交、审核、签署和创建补充报告；
4. 每次修改形成新版本，已签署版本不可覆盖；
5. 报告状态机拒绝非法操作；
6. 所有敏感操作具有用户身份和审计记录；
7. 已签署报告可通过接口提供给检查检验模块；
8. 已发布报告可可靠推送至电子病历，失败可重试；
9. 前端明确区分 AI 草稿、医生审核状态和正式报告；
10. 自动化测试覆盖主要正常流程和异常流程；
11. 未接入真实模型权重时，系统必须显式标识演示或测试状态；
12. AI 和 LLM 在任何情况下都不能自动替代医生完成签署。

---

## 17. 本阶段之后的路线

完成阶段 J 后，再按照业务图向更上层推进：

### 阶段 K：门诊与 AI 助理医生接入

将已签署的检查报告、结构化 AI 发现和患者就诊上下文提供给门诊医生工作台，支持病历摘要、检查结果归纳和诊疗提示。

### 阶段 L：AI 分诊台与线上问诊

接入患者主诉、既往史和检查结果，进行风险分层和科室推荐。该模块必须与影像诊断模型解耦，并设置急症规则和人工兜底。

### 阶段 M：挂号、排班和平台运营整合

连接患者端挂号、医生排班、门诊流程和管理员端配置，形成业务图中完整的平台闭环。

---

## 18. 当前最先执行的任务

建议立即从 J0 和 J1 开始：

1. 在根目录创建 `HeadCTReportService`；
2. 固化 Orchestrator 到报告服务的输入契约；
3. 建立 PostgreSQL 报告、版本、审核和审计表；
4. 将现有本地 JSON 审核记录迁移为数据库实现；
5. 完成“成功 AI 任务 -> 报告草稿 -> 医生修改 -> 审核签署”的最小闭环；
6. 再接入检查检验和电子病历，不让外部平台直接依赖 Orchestrator 内部数据结构。

这条路线与 `project.png` 的模块关系一致，也能最大程度复用当前已经完成的 Filter、病灶识别、Orchestrator 和标准 RAG 能力。
