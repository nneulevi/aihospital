# HeadCTReportService API Contract

## 通用约定

基础路径：`/api/v1`

除健康检查和前端静态资源外，所有接口必须携带可信身份网关注入的请求头：

```http
X-Actor-Id: doctor-001
X-Actor-Role: reporting_doctor
X-Request-Id: optional-trace-id
```

签署接口还必须携带：

```http
X-Signature-Confirmation: confirm
```

生产部署必须由统一认证网关覆盖客户端传入的身份请求头。

错误响应：

```json
{
  "error": {
    "code": "REPORT_STATE_CONFLICT",
    "message": "当前报告状态不允许执行该操作",
    "details": {}
  }
}
```

## 检查检验接入

### 登记检查

```http
POST /api/v1/integrations/examinations
```

### 绑定 AI 分析任务并创建报告

```http
POST /api/v1/integrations/examinations/{study_id}/analysis
Idempotency-Key: unique-business-key
```

```json
{
  "orchestrator_task_id": "task-id",
  "assigned_doctor_id": "doctor-001"
}
```

## 报告创建和查询

```http
POST /api/v1/reports/from-analysis/{task_id}
GET  /api/v1/reports
GET  /api/v1/reports/{report_id}
GET  /api/v1/reports/{report_id}/versions
GET  /api/v1/reports/{report_id}/audit-events
GET  /api/v1/reports/{report_id}/references
```

直接创建报告请求：

```json
{
  "order_id": "ORDER-001",
  "study_id": "STUDY-001",
  "patient_id": "PATIENT-001",
  "accession_number": "ACC-001",
  "department": "神经外科",
  "assigned_doctor_id": "doctor-001"
}
```

相同 `task_id` 或相同 `Idempotency-Key` 返回同一报告，不重复创建。

## 编辑和并发控制

```http
PATCH /api/v1/reports/{report_id}/draft
```

```json
{
  "findings": "影像所见",
  "impression": "诊断意见",
  "recommendations": "建议",
  "expected_version": 1,
  "change_reason": "医生复核修订"
}
```

`expected_version` 必须等于报告当前 `version_lock`。冲突返回 `REPORT_VERSION_CONFLICT`，客户端应重新加载报告后再编辑。

## 审核、签署和发布

```http
POST /api/v1/reports/{report_id}/submit-review
POST /api/v1/reports/{report_id}/approve
POST /api/v1/reports/{report_id}/request-revision
POST /api/v1/reports/{report_id}/sign
POST /api/v1/reports/{report_id}/release
POST /api/v1/reports/{report_id}/amendments
```

状态主流程：

```text
draft -> pending_review -> approved -> signed -> released
                    \-> revision_required -> pending_review
```

AI 和 LLM 只能创建 `draft`，不能执行审核、签署和发布。

## EMR Outbox

```http
POST /api/v1/integrations/emr/dispatch?limit=20
```

发布报告时，同一数据库事务写入 `report_outbox_events`。投递失败会记录错误并按指数退避再次尝试，成功后回写 `external_document_id`。

