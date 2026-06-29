# 阶段K：性能优化与异步任务队列详细指导

更新时间：2026-06-23

## 1. 阶段目标

当前系统已经完成主平台 Project2 与 HeadCT AI 子系统的端到端联调：

```text
Project2
  -> HeadCTOrchestrator
  -> Filter 金属伪影识别
  -> HeadCTLesionDetection 病灶识别
  -> RAG + LLM 报告/问诊/辅助诊断增强
  -> HeadCTReportService
  -> HeadCTEMRService
```

阶段K的目标不是新增医学能力，而是让已有能力具备更好的性能、稳定性和并发承载能力。

核心建设内容：

1. Redis 缓存与短期状态层。
2. AI 异步任务队列。
3. 模型推理结果缓存、并发控制与批处理预留。

设计原则：

- 保持现有接口兼容，已有 E2E 不应失效。
- 新能力以扩展方式接入，遵守开闭原则。
- 优先解决真实瓶颈：外部 LLM/RAG 调用慢、影像推理耗时长、重复请求浪费 GPU/LLM 资源。
- 不急于引入 Kafka、复杂服务治理平台等重型组件。

## 2. 当前性能风险

### 2.1 同步请求链路过长

当前真实业务链路中，一个主平台请求可能串联：

```text
Project2 HTTP 请求
  -> Orchestrator
  -> Filter 模型推理
  -> Lesion 模型推理
  -> pgvector 检索
  -> DashScope rerank
  -> 阿里百炼 LLM
  -> ReportService
  -> EMRService
```

风险：

- 单个请求耗时长。
- 任一外部服务抖动都会拖慢主平台接口。
- 浏览器/网关/HTTP 客户端超时风险较高。

### 2.2 外部 AI 调用成本高

高成本调用包括：

- DashScope embedding。
- DashScope rerank。
- 阿里百炼 LLM。
- GPU 模型推理。

同一患者、同一影像、同一报告上下文重复触发时，当前缺少统一缓存。

### 2.3 GPU 推理并发不可控

Filter 和 Lesion 服务使用模型权重进行推理。若多个请求同时进入：

- GPU 显存可能被打满。
- 推理延迟可能明显抖动。
- Windows 本地环境下多进程模型加载也可能占用大量资源。

## 3. 总体架构建议

阶段K建议加入 Redis，但仍保持 PostgreSQL 为主数据源。

```text
Project2
  -> HeadCTOrchestrator
      -> Redis
          - 短期任务状态
          - 请求幂等缓存
          - RAG/LLM 响应缓存
          - 模型推理结果缓存索引
          - 轻量任务队列
      -> PostgreSQL
          - 持久化业务结果
          - 报告、EMR、AI 结构化结果
      -> Filter / Lesion / Report / EMR
```

Redis 定位：

- 快速缓存。
- 临时状态。
- 队列协调。
- 限流计数。

PostgreSQL 定位：

- 最终事实数据。
- 可审计结果。
- 医疗业务记录。

## 4. K1：Redis 缓存与状态层

### 4.1 建议新增目录

```text
HeadCTOrchestrator/
  cache/
    __init__.py
    redis_client.py
    cache_keys.py
    cache_service.py
    rate_limiter.py
  tests/
    test_cache_keys.py
    test_cache_service.py
```

如后续多个 Python 服务共用，可再抽取：

```text
HeadCTShared/
  cache/
  observability/
```

第一阶段先放在 `HeadCTOrchestrator/cache/`，避免过早抽象。

### 4.2 配置项

新增环境变量：

```text
REDIS_ENABLED=true
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_CONNECT_TIMEOUT_SECONDS=2
REDIS_SOCKET_TIMEOUT_SECONDS=3

CACHE_RAG_RETRIEVAL_TTL_SECONDS=1800
CACHE_LLM_RESPONSE_TTL_SECONDS=1800
CACHE_MODEL_RESULT_TTL_SECONDS=86400
CACHE_PROJECT2_DICT_TTL_SECONDS=3600
```

要求：

- Redis 不可用时，默认降级为“不使用缓存”，不能影响主链路。
- 生产模式可配置为 Redis 必需，测试模式可禁用。

### 4.3 缓存 key 设计

统一 key 前缀：

```text
headct:{env}:{module}:{kind}:{hash}
```

示例：

```text
headct:local:rag:retrieval:{query_hash}
headct:local:rag:rerank:{query_hash}:{doc_hash}
headct:local:llm:clinical:{payload_hash}
headct:local:llm:report:{payload_hash}
headct:local:model:artifact:{file_sha256}:{model_version}
headct:local:model:lesion:{file_sha256}:{model_version}
headct:local:project2:dict:department
```

hash 规则：

- JSON payload 必须先做稳定序列化：`sort_keys=True`。
- 文件类缓存使用 SHA256。
- 模型类缓存必须包含 `model_name/model_version/checkpoint_hash/threshold`，避免模型更新后误用旧结果。

### 4.4 RAG 缓存策略

缓存对象：

- `retrieve_context(query_text, filter_tags)` 的结果。
- DashScope rerank 排序结果。

推荐 TTL：

```text
RAG retrieval: 30 分钟
Rerank result: 30 分钟
```

失效条件：

- 重新执行 `ingest_knowledge.py` 后，应清理 `headct:*:rag:*`。
- 知识库版本变化时，key 中加入 `knowledge_version`。

验收标准：

- 相同 query 第二次请求不再访问 DashScope rerank。
- RAG 结果包含 `cache_hit=true/false` 诊断字段，便于日志观察。
- RAG 单元测试仍通过。

### 4.5 LLM 缓存策略

缓存对象：

- AI 问诊 triage 结果。
- AI 辅助诊断建议。
- 报告辅助增强结果。

推荐 TTL：

```text
临床问诊/辅助诊断：15-30 分钟
报告辅助增强：15-30 分钟
```

注意：

- 不缓存含有患者姓名、身份证、手机号等明文隐私字段的原始请求。
- key 使用脱敏后的结构化 payload hash。
- value 可以保存结构化 JSON，但不应保存原始 API key、请求头。

验收标准：

- 同一脱敏 payload 重复请求时返回一致结果。
- 返回结构中保留 `requires_doctor_review=true`。
- 安全改写仍生效，禁用词不能因为缓存绕过校验。

## 5. K2：AI 异步任务队列

### 5.1 为什么需要异步化

以下操作不适合长期占用 HTTP 请求：

- 影像文件上传后的完整 AI 分析。
- Filter/Lesion 模型推理。
- 报告生成 + RAG + LLM。
- EMR 归档。

目标模式：

```text
提交任务 -> 立即返回 task_id -> 轮询/订阅状态 -> 获取结果
```

### 5.2 推荐技术选型

当前阶段推荐：

```text
Redis + RQ 或 Celery
```

优先级：

1. Python AI 子系统内部：Redis Queue/RQ。
2. Project2 侧继续使用 HTTP 调用 Orchestrator 的任务接口。
3. 暂不引入 Kafka，除非后续需要多系统事件流。

### 5.3 建议新增目录

```text
HeadCTOrchestrator/
  worker/
    __init__.py
    queue.py
    jobs.py
    worker_main.py
    task_models.py
  scripts/
    start_orchestrator_worker.ps1
```

### 5.4 任务状态模型

任务状态：

```text
queued
running
success
failed
cancelled
timeout
```

任务结构：

```json
{
  "task_id": "string",
  "task_type": "head_ct_analysis | report_generation | clinical_assist",
  "status": "queued",
  "progress": 0,
  "created_at": "datetime",
  "started_at": null,
  "finished_at": null,
  "input_hash": "sha256",
  "result_ref": null,
  "error_code": null,
  "error_message": null
}
```

Redis 保存短期状态，PostgreSQL 保存最终结果。

### 5.5 接口扩展建议

保留现有同步接口，同时增加异步接口：

```text
POST /api/head-ct-ai/async/tasks
GET  /api/head-ct-ai/async/tasks/{task_id}
GET  /api/head-ct-ai/async/results/{task_id}
POST /api/head-ct-ai/async/tasks/{task_id}/cancel
```

Project2 后续可从同步调用迁移到：

```text
Project2
  -> POST async/tasks
  -> 保存 task_id
  -> 前端轮询 status
  -> success 后读取 result
```

### 5.6 队列拆分

建议至少拆分：

```text
headct:queue:high
headct:queue:normal
headct:queue:gpu
headct:queue:llm
```

使用建议：

- `gpu`：Filter、Lesion 推理。
- `llm`：RAG + LLM 报告/问诊/诊断。
- `high`：医生正在等待的交互任务。
- `normal`：后台归档、补充生成任务。

### 5.7 超时与重试

推荐：

```text
Filter/Lesion 推理：1 次重试
DashScope embedding/rerank：2 次重试，指数退避
LLM：1 次重试，失败后返回可审核的规则兜底草稿
EMR 归档：3 次重试
```

注意：

- 医疗安全相关任务不能静默失败。
- 失败必须落库，方便医生/管理员看到。

验收标准：

- 提交任务接口 1 秒内返回 `task_id`。
- 长任务状态可轮询。
- 任务失败有明确 `error_code`。
- worker 重启后不会丢失已经成功落库的结果。

## 6. K3：模型推理缓存、并发控制与批处理预留

### 6.1 文件 hash 缓存

上传影像后计算：

```text
file_sha256
file_size
model_version
inference_params_hash
```

缓存 key：

```text
headct:local:model:artifact:{file_sha256}:{model_version}:{params_hash}
headct:local:model:lesion:{file_sha256}:{model_version}:{params_hash}
```

命中后直接返回已有推理结果引用。

### 6.2 结果复用边界

可以复用：

- 同一文件。
- 同一模型版本。
- 同一阈值/patch 参数。
- 同一预处理配置。

不能复用：

- 模型权重变化。
- 阈值变化。
- patch size/overlap 变化。
- 输入文件发生改变。

### 6.3 GPU 并发控制

建议每个模型服务增加并发限制：

```text
FILTER_MAX_GPU_CONCURRENCY=1
LESION_MAX_GPU_CONCURRENCY=1
```

实现方式：

- 进程内 `asyncio.Semaphore`。
- 多进程/多服务场景使用 Redis 分布式锁。

锁 key 示例：

```text
headct:local:lock:gpu:filter
headct:local:lock:gpu:lesion
```

要求：

- 锁必须设置 TTL，避免 worker 崩溃后死锁。
- 超时后返回 `GPU_BUSY` 或进入队列等待。

### 6.4 模型预热

服务启动时执行：

- 加载 checkpoint。
- 构造最小 dummy tensor。
- 完成一次 no_grad 推理。
- `/health` 返回 `model_warmed=true/false`。

收益：

- 避免首个真实请求被模型初始化拖慢。
- 方便验收时判断服务是否真正可推理。

### 6.5 批处理预留

当前阶段不强制做批处理，但接口设计应预留：

```text
batch_id
case_id
series_id
file_sha256
```

后续可支持：

- 多个 CT 序列批量分析。
- 多患者后台队列批处理。
- 夜间批量质控。

验收标准：

- 同一 CT 文件重复分析时第二次明显更快，并返回 `cache_hit=true`。
- 并发请求不会导致 GPU OOM。
- 模型版本改变后不会命中旧缓存。
- 当前 `smoke_test_headct_platform.py` 与 Project2 E2E 仍通过。

## 7. Project2 接入建议

### 7.1 Redis 缓存

Project2 可使用 Spring Cache：

```text
spring-boot-starter-data-redis
spring-boot-starter-cache
```

适合缓存：

- 科室列表。
- 医生排班。
- 检查/检验项目字典。
- 药品字典。
- AI 服务健康状态短期缓存。

不建议缓存：

- 挂号支付状态。
- 医嘱执行状态。
- 医生审核后的最终报告。

### 7.2 AI 任务状态表

Project2 可增加：

```text
ai_task
  id
  task_id
  task_type
  patient_id
  register_id
  request_id
  status
  progress
  result_ref
  error_code
  error_message
  create_time
  update_time
```

用途：

- 前端展示“AI 分析中”。
- 医生工作站轮询任务状态。
- 失败后支持重新提交。

## 8. 推荐实施顺序

### 第一步：基础 Redis 接入

完成：

- Redis 配置读取。
- Redis client 封装。
- cache key 工具。
- Redis 不可用时降级。
- RAG retrieval 缓存。

验收：

```powershell
python -m pytest HeadCTOrchestrator/tests -q
python scripts\smoke_test_headct_platform.py
```

### 第二步：LLM/RAG 缓存

完成：

- 问诊 triage 缓存。
- 辅助诊断缓存。
- 报告辅助增强缓存。
- 安全校验在缓存返回前仍执行。

验收：

```powershell
python scripts\e2e_project2_real_business.py
```

### 第三步：模型结果缓存

完成：

- 文件 SHA256。
- 推理结果 cache key。
- Filter/Lesion cache hit 标记。
- 模型版本进入 cache key。

验收：

- 同一文件两次分析，第二次返回 `cache_hit=true`。
- 模型版本变更后重新推理。

### 第四步：异步任务队列

完成：

- Redis Queue/RQ。
- worker 启动脚本。
- async task API。
- Project2 保存 task_id。

验收：

- 提交任务立即返回。
- 后台完成后可查询结果。
- worker 停止时任务失败可见。

### 第五步：GPU 并发控制

完成：

- Filter 推理 semaphore/lock。
- Lesion 推理 semaphore/lock。
- GPU busy 状态和队列等待策略。

验收：

- 并发请求不 OOM。
- 超出并发限制时状态明确。

## 9. 端到端验收清单

每个阶段完成后至少执行：

```powershell
python -m pytest HeadCTOrchestrator\tests -q
python scripts\smoke_test_headct_platform.py
python scripts\e2e_project2_core_business.py
python scripts\e2e_project2_real_business.py
```

必须满足：

- Project2 health = `UP`
- Orchestrator health = `ok`
- RAG status = `success`
- LLM status = `success`
- Report status = `released`
- EMR status = `final`
- 禁用词安全规则仍生效
- 当前同步接口不破坏

## 10. 不建议本阶段做的事

暂不建议：

- 引入 Kafka。
- 引入完整 Service Mesh。
- 大规模拆分数据库。
- 把所有接口一次性改成异步。
- 为了缓存牺牲医疗结果可追溯性。

推荐策略：

```text
先缓存高成本、重复率高、非最终事实的数据；
再异步化耗时长、用户可等待的任务；
最后做 GPU 并发控制和批处理。
```

## 11. 阶段K完成定义

阶段K可以视为完成，当满足：

- Redis 已接入并可配置启停。
- RAG/LLM 至少一个高成本链路具备缓存。
- 影像分析具备文件 hash 级结果复用。
- 至少一个 AI 长任务支持异步提交和查询。
- GPU 推理有并发限制或队列保护。
- 所有现有 E2E 验收仍通过。

