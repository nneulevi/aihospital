# 阶段 J 开发接入记录

## 完成范围

已按《阶段J_AI智能检查报告与检查检验平台接入详细指导》建立独立根级模块 `HeadCTReportService`，没有将报告业务放入 Filter、病灶服务或 Orchestrator。

已完成：

- J0：报告契约、数据库表、状态机和角色权限；
- J1：从 Orchestrator 成功任务创建 PostgreSQL 报告草稿；
- J2：医生编辑、版本、审核、退回、签署、发布和补充报告；
- J3：检查登记及 `study_id` 与 AI 任务绑定接口；
- J4：EMR Outbox、幂等投递、失败记录和重试时间；
- J5：医生工作台、接口文档、真实 PostgreSQL 自动化测试和运行脚本。

## 数据库对象

- `examination_orders`
- `ai_analysis_snapshots`
- `medical_reports`
- `medical_report_versions`
- `report_reviews`
- `report_audit_events`
- `report_outbox_events`

报告内容采用不可变版本设计。修改报告会创建新版本，已发布报告只能通过补充报告流程继续修改。

## 安全边界

- AI 与 LLM 仅能生成草稿；
- 医生审核、签署和发布由状态机与 RBAC 控制；
- 签署要求二次确认请求头；
- 身份由可信网关请求头传入；
- API Key、数据库密码和完整提示词不写入报告快照；
- 发布报告通过事务 Outbox 进入 EMR 集成队列。

## 验证结果

真实 PostgreSQL 集成测试覆盖：

- AI 草稿幂等创建；
- 报告编辑和乐观锁；
- 审核通过与退回修订；
- 医生签署和发布；
- 补充报告；
- 检查登记和任务绑定；
- EMR Outbox 投递；
- 角色权限拒绝；
- 版本和审计记录查询。

## EMR 接入结果

已新增独立 `HeadCTEMRService`，并完成以下正式本地接入：

- `EMR_BASE_URL=http://127.0.0.1:8040`；
- Bearer 服务令牌认证；
- PostgreSQL `emr_diagnostic_reports` 持久化；
- `Idempotency-Key` 与源报告 ID 双重幂等；
- EMR 接收审计事件；
- 报告服务 Outbox 成功后回写 `external_document_id`。

五服务端到端烟雾测试已验证：

```text
CT 上传
 -> Filter 3D U-Net
 -> LesionDetection
 -> Orchestrator
 -> pgvector HNSW/Rerank
 -> DashScope LLM
 -> 报告编辑/审核/签署/发布
 -> Outbox
 -> HeadCTEMRService PostgreSQL 入库
```

当前本地 EMR 是可实际运行的项目后端，不是 Fake；但它仍不代表医院生产 HIS/EMR。接入具体医院时，应根据厂商认证协议、患者主索引和数据标准增加适配器。

## LLM 安全修正

真实联调中发现 LLM 二次生成后仍可能出现“排除”等绝对化词语。现已改为：

1. LLM 真实调用和二次改写；
2. 对残余禁用词执行确定性谨慎表达重写；
3. 在 `llm_context.safety_rewrites` 中记录修正；
4. 再次执行最终安全校验；
5. 不回落到规则模板，也不因单个词语使整条任务失败。
