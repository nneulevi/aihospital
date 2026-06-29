# HeadCTReportService

主平台完整调用时序、身份、状态和异常处理见 [主平台协同工作与接入说明.md](../主平台协同工作与接入说明.md)。

阶段 J 的独立智能检查报告服务，负责将 `HeadCTOrchestrator` 的成功结果转化为可编辑、可审核、可签署、可发布和可追溯的正式报告流程。

## 已实现

- PostgreSQL 报告、版本、审核、审计和 Outbox 持久化；
- 从 Orchestrator 成功任务幂等创建 AI 报告草稿；
- 检查申请、影像检查、AI 任务和报告 ID 关联；
- 草稿编辑和乐观锁并发控制；
- 提交审核、退回修订、审核通过、签署和发布状态机；
- 已发布报告补充版本；
- EMR Outbox 投递、失败记录和指数退避；
- 基于可信身份网关请求头的 RBAC；
- 医生报告工作台、RAG 引用、版本和审计展示。

## 启动

先配置 `REPORT_DB_DSN`，并确保 Orchestrator 已在 `8010` 端口启动：

```powershell
$env:REPORT_DB_DSN = "postgresql://user:password@localhost:5432/headct_ai"
python -m uvicorn HeadCTReportService.ReportServer:app --host 0.0.0.0 --port 8030
```

浏览器访问 `http://localhost:8030`，接口文档访问 `http://localhost:8030/docs`。

## 完整平台启动

项目已提供统一启动和健康检查脚本：

```powershell
.\scripts\start_headct_platform.ps1
.\scripts\check_headct_platform.ps1
```

默认本地端口：

- Filter：`8000`
- Orchestrator：`8010`
- LesionDetection：`8021`，因为本机 `8020` 已被其他程序占用
- ReportService：`8030`
- EMRService：`8040`

本地 EMR 使用独立模块 [HeadCTEMRService](../HeadCTEMRService/README.md)，通过 PostgreSQL、Bearer 服务令牌和幂等键接收已发布报告。

## 身份请求头

当前实现假定请求已经通过医院统一身份网关，业务服务读取：

```text
X-Actor-Id: doctor-001
X-Actor-Role: reporting_doctor
```

生产部署时应由反向代理或统一认证服务写入并清洗这些请求头，不能允许客户端绕过认证自行伪造。

## 主要角色

- `technician`
- `reporting_doctor`
- `reviewing_doctor`
- `signing_doctor`
- `administrator`
- `integration_service`

## 主要接口

- `POST /api/v1/reports/from-analysis/{task_id}`
- `GET /api/v1/reports`
- `PATCH /api/v1/reports/{report_id}/draft`
- `POST /api/v1/reports/{report_id}/submit-review`
- `POST /api/v1/reports/{report_id}/approve`
- `POST /api/v1/reports/{report_id}/request-revision`
- `POST /api/v1/reports/{report_id}/sign`
- `POST /api/v1/reports/{report_id}/release`
- `POST /api/v1/reports/{report_id}/amendments`
- `POST /api/v1/integrations/emr/dispatch`

可运行以下脚本验证 CT 上传到 EMR 入库的完整链路：

```powershell
python scripts\smoke_test_headct_platform.py
```
