# 阶段K：性能优化与异步任务队列进度记录

更新时间：2026-06-23

## 1. 本轮完成范围

本轮完成阶段K中的第一批可落地任务：

- Redis 可选缓存基础设施。
- RAG retrieval 缓存。
- 临床问诊/辅助诊断 LLM 响应缓存。
- 报告辅助增强 LLM 响应缓存。
- `-Reload` 模式安全保护，避免 Windows 环境下 stderr 日志快速膨胀。
- 端到端回归验收。

异步任务队列、模型结果文件 hash 缓存、GPU 分布式并发锁尚未在本轮实现，作为下一批任务继续。

## 2. Redis 缓存基础设施

新增目录：

```text
HeadCTOrchestrator/cache/
  __init__.py
  cache_keys.py
  cache_service.py
  rate_limiter.py
  redis_client.py
```

新增配置：

```text
HEADCT_DEPLOY_ENV / APP_ENV
REDIS_ENABLED
REDIS_URL
REDIS_CONNECT_TIMEOUT_SECONDS
REDIS_SOCKET_TIMEOUT_SECONDS
CACHE_RAG_RETRIEVAL_TTL_SECONDS
CACHE_LLM_RESPONSE_TTL_SECONDS
CACHE_MODEL_RESULT_TTL_SECONDS
CACHE_PROJECT2_DICT_TTL_SECONDS
```

当前默认：

```text
REDIS_ENABLED=false
```

说明：

- Redis 未启用或不可用时自动旁路，不影响现有链路。
- 缓存 key 使用稳定 JSON 序列化和 SHA256。
- 依赖已补充：`redis>=5.0`。

## 3. RAG retrieval 缓存

改动文件：

```text
HeadCTOrchestrator/rag/retriever.py
```

缓存 key 包含：

- `query_text`
- `filter_tags`
- `top_k`
- `recall_top_n`
- `min_similarity`
- `hnsw_ef_search`

返回结果新增诊断字段：

```json
{
  "cache_hit": false,
  "cache_backend": "disabled"
}
```

当 Redis 启用并命中时：

```json
{
  "cache_hit": true,
  "cache_backend": "redis"
}
```

## 4. LLM 响应缓存

改动文件：

```text
HeadCTOrchestrator/rag/clinical_assist.py
HeadCTOrchestrator/rag/llm_provider.py
```

已缓存链路：

- AI 问诊分诊：`clinical_consultation`
- AI 辅助诊断：`clinical_diagnosis`
- 报告辅助增强：`report_assist`

安全要求：

- 只缓存结构化 JSON。
- 缓存命中后仍执行安全校验。
- 若缓存内容包含禁用词，仍会走安全改写或失败，不允许绕过医生审核规则。

## 5. Reload 安全处理

改动文件：

```text
scripts/start_headct_platform.ps1
```

处理原因：

- 在当前 Windows Python 环境中，`uvicorn --reload` 会触发 `multiprocessing.resource_sharer` 的 `PermissionError: [WinError 5] 拒绝访问。`
- 该错误会快速刷大 `stderr.log`。

处理策略：

- `-Reload` 参数仍可传入。
- 默认不启用 `uvicorn --reload`。
- 如确需强制启用，需显式设置：

```powershell
$env:HEADCT_ALLOW_UVICORN_RELOAD = "true"
```

同时脚本增加：

```text
WATCHFILES_IGNORE_PERMISSION_DENIED=1
PYTHONDONTWRITEBYTECODE=1
```

并保留更窄的 reload 目录和 exclude 规则。

本轮已清理历史大日志：

```text
orchestrator.stderr.log
report.stderr.log
emr.stderr.log
```

安全模式重启后日志大小：

```text
filter.stderr.log          201
lesion.stderr.log          201
orchestrator.stderr.log    201
emr.stderr.log             202
report.stderr.log          202
project2.stderr.log          0
```

## 6. 验收结果

### 6.1 单元测试

命令：

```powershell
python -m pytest HeadCTOrchestrator\tests -q
```

结果：

```text
36 passed
```

### 6.2 HeadCT smoke

命令：

```powershell
python scripts\smoke_test_headct_platform.py
```

结果摘要：

```json
{
  "orchestrator_status": "success",
  "filter_backend": "unet3d",
  "lesion_status": "success",
  "rag_status": "success",
  "llm_status": "success",
  "report_status": "released",
  "emr_status": "final"
}
```

### 6.3 Project2 核心业务 E2E

命令：

```powershell
python scripts\e2e_project2_core_business.py
```

结果摘要：

```json
{
  "status": "success",
  "health": "UP",
  "orders_count": 3,
  "check_result_sections": {
    "checks": 1,
    "inspections": 1,
    "disposals": 1
  },
  "prescription_status": "REFUNDED"
}
```

### 6.4 Project2 + HeadCT AI 真实业务 E2E

命令：

```powershell
python scripts\e2e_project2_real_business.py
```

结果摘要：

```json
{
  "status": "success",
  "project2": "UP",
  "orchestrator": "ok",
  "report": "ok",
  "emr": "ok",
  "consultation_recommendation_count": 2,
  "diagnosis_suggestion_count": 2,
  "analysis_confidence": 0.4617331326007843,
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

## 7. 下一批任务

下一批建议按以下顺序继续：

1. 启用真实 Redis 服务并设置：

```text
REDIS_ENABLED=true
REDIS_URL=redis://127.0.0.1:6379/0
```

2. 增加 Redis cache hit 集成测试。
3. 实现影像文件 SHA256 级模型推理结果缓存。
4. 实现 GPU 推理并发限制。
5. 引入 Redis Queue/RQ，新增异步任务接口。
6. Project2 增加 `ai_task` 状态表和前端轮询展示。

