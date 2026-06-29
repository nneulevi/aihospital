# HeadCTEMRService

与检查检验、Orchestrator、报告服务和主平台的整体协同方式见 [主平台协同工作与接入说明.md](../主平台协同工作与接入说明.md)。

阶段 J 的本地电子病历接收服务。它不是 Fake 客户端，而是使用 PostgreSQL 持久化、服务令牌认证和幂等约束的可运行后端，用于承接 `HeadCTReportService` 发布的正式检查报告。

## 边界

该模块可以完成项目内部电子病历链路和接口验收，但不代表已经接入某家医院的生产 HIS/EMR。医院部署时仍需按真实厂商接口、身份认证和数据标准替换或扩展适配层。

## 接口

- `GET /api/v1/health`
- `POST /api/v1/diagnostic-reports`
- `GET /api/v1/diagnostic-reports`
- `GET /api/v1/diagnostic-reports/{document_id}`

除健康检查外，接口需要：

```http
Authorization: Bearer <EMR_SERVICE_TOKEN>
```

## 启动

推荐直接启动完整平台：

```powershell
.\scripts\start_headct_platform.ps1
```

独立启动时：

```powershell
$env:EMR_DB_DSN = $env:RAG_DB_DSN
$env:EMR_SERVICE_TOKEN = "replace-before-production"
python -m uvicorn HeadCTEMRService.EmrServer:app --host 127.0.0.1 --port 8040
```

本地开发令牌仅用于项目联调，生产环境必须使用随机密钥或医院统一服务身份认证。
