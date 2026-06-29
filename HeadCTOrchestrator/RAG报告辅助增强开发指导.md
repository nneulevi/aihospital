# RAG 鎶ュ憡杈呭姪澧炲己寮€鍙戞寚瀵?

## 当前标准实现摘要

当前标准 RAG 方案为：

```text
DashScope text-embedding-v4
-> PostgreSQL + pgvector HNSW 召回
-> DashScope gte-rerank-v2 二阶段重排
-> top_k 证据片段
-> 阿里百炼 qwen-plus 报告辅助生成
-> safety_rules 医疗安全校验
```

早期 deterministic embedding、ivfflat 索引和无 rerank 检索仅作为原型/测试路径，不作为正式方案。
鏇存柊鏃堕棿锛?026-06-12

## 1. 鐩爣瀹氫綅

鏈ā鍧楃敤浜庡寮?`HeadCTOrchestrator` 鐨?`report_assist`锛岃绯荤粺鍦ㄥ凡鏈夊奖鍍忔ā鍨嬬粨鏋勫寲缁撴灉鐨勫熀纭€涓婏紝妫€绱㈠彈鎺у尰瀛︾煡璇嗐€侀」鐩枃妗ｃ€佹姤鍛婃ā鏉垮拰瀹夊叏琛ㄨ揪瑙勮寖锛岀敓鎴愬彲杩芥函銆佸彲澶嶆牳鐨勬姤鍛婅緟鍔╁缓璁€?
鏍稿績鍘熷垯锛?
```text
RAG 鍙寮烘姤鍛婅緟鍔╄〃杈惧拰鍙傝€冧緷鎹紝涓嶆敼鍙樺奖鍍忔ā鍨嬬殑鍘熷鍒ゆ柇銆?RAG 杈撳嚭鍙緵鍖荤敓鍙傝€冿紝鏈€缁堟姤鍛婂繀椤荤敱鍖荤敓瀹℃牳銆?```

RAG 鍙互鍋氾細

- 浼樺寲 `report_assist.summary` 鐨勪笓涓氳〃杈俱€?- 鏍规嵁浼奖绛夌骇琛ュ厖鈥滅粨鏋滃彲鑳藉彈闄愨€濈殑瑙ｉ噴銆?- 鏍规嵁鐥呯伓绫诲瀷鍖归厤鎶ュ憡妯℃澘鐗囨銆?- 缁欏嚭寤鸿澶嶆牳鍔ㄤ綔銆?- 寮曠敤椤圭洰鍐呴儴鏂囨。銆佸尰瀛﹁鏄庛€佹暟鎹泦瀛楁璇存槑銆?- 妫€鏌ユ姤鍛婅緟鍔╂枃鏈腑鏄惁鍖呭惈绂佹琛ㄨ堪銆?
RAG 涓嶅簲鍋氾細

- 鐩存帴鍒ゆ柇 CT 鏄惁瀛樺湪鍑鸿鎴栧叾浠栫梾鐏躲€?- 淇敼妯″瀷杈撳嚭鐨?`detected`銆乣confidence`銆乣severity`銆?- 浠ユ枃鏈煡璇嗘帹缈诲奖鍍忔ā鍨嬬粨鏋溿€?- 杈撳嚭鈥滅‘璇娾€濃€滄帓闄も€濃€滄棤闇€鍖荤敓瀹℃牳鈥濈瓑缁濆缁撹銆?- 鐢熸垚鏃犻渶鍖荤敓澶嶆牳鐨勬渶缁堣瘖鏂€?
## 2. 鎺ㄨ崘鎬讳綋鏋舵瀯

```text
Filter / LesionDetection
  -> 杈撳嚭褰卞儚绠楁硶缁撴灉銆佺疆淇″害銆佷吉褰辩瓑绾с€佺梾鐏剁粨鏋?
Orchestrator
  -> 姹囨€?quality_control 鍜?lesion_analysis
  -> 鏋勯€?RAG 鏌ヨ涓婁笅鏂?
RAG
  -> 鏌ヨ鍚戦噺鏁版嵁搴?  -> 杩斿洖鐭ヨ瘑鐗囨銆佹潵婧愩€佺浉浼煎害
  -> 鐢熸垚澧炲己 report_assist
  -> 鎵ц瀹夊叏琛ㄨ揪妫€鏌?  -> 鍙€夎皟鐢ㄥ閮?LLM 鐢熸垚鎶ュ憡鑽夌

鍖荤敓
  -> 澶嶆牳鍘熷褰卞儚銆佹ā鍨嬬粨鏋溿€丷AG 寮曠敤鍜岃緟鍔╂枃鏈?  -> 褰㈡垚鏈€缁堟姤鍛?```

## 3. 鎶€鏈€夊瀷

绗竴鐗堝缓璁紭鍏堜娇鐢細

```text
PostgreSQL + pgvector
```

鍘熷洜锛?
- 鏃㈣兘淇濆瓨鐭ヨ瘑鐗囨鍏冩暟鎹紝鍙堣兘鍋氬悜閲忕浉浼煎害妫€绱€?- 涓庡悗缁钩鍙版暟鎹簱鎺ュ叆璺緞涓€鑷淬€?- 鏂逛究瀹¤銆佸浠姐€佹潈闄愭帶鍒跺拰鐗堟湰绠＄悊銆?- 閬垮厤杩囨棭寮曞叆鐙珛鍚戦噺鏁版嵁搴撴湇鍔★紝闄嶄綆閮ㄧ讲澶嶆潅搴︺€?
鍙€夋浛浠ｏ細

| 鏂规 | 閫傜敤鍦烘櫙 |
| --- | --- |
| PostgreSQL + pgvector | 鎺ㄨ崘绗竴鐗堬紝閫傚悎缁撴瀯鍖栧厓鏁版嵁 + 鍚戦噺妫€绱竴浣撳寲 |
| Milvus | 鐭ヨ瘑搴撹妯¤緝澶с€侀渶瑕佺嫭绔嬮珮鎬ц兘鍚戦噺鏈嶅姟 |
| Qdrant | 杞婚噺鍚戦噺鏈嶅姟锛岄儴缃插拰 API 浣跨敤鐩稿鐩存帴 |
| FAISS | 鏈湴瀹為獙鎴栫绾块獙璇侊紝涓嶉€傚悎浣滀负闀挎湡鐢熶骇瀛樺偍 |

## 4. 鎺ㄨ崘鏂囦欢缁撴瀯

```text
HeadCTOrchestrator/
  rag/
    __init__.py
    config.py
    db.py
    schema.sql
    knowledge_base.py
    embedding_provider.py
    retriever.py
    report_enhancer.py
    llm_provider.py
    safety_rules.py
    ingest_knowledge.py
    knowledge/
      artifact_quality.md
      hemorrhage_reporting.md
      safety_expression_rules.md
      report_templates.md
      cq500_label_notes.md
  tests/
    test_report_rag_enhancer.py
    test_rag_retriever_pgvector.py
    test_rag_ingest_knowledge.py
    test_rag_safety_rules.py
    test_rag_llm_provider.py
```

鑱岃矗鍒掑垎锛?
| 鏂囦欢 | 鑱岃矗 |
| --- | --- |
| `config.py` | RAG銆佸悜閲忓簱銆乪mbedding銆丩LM 閰嶇疆 |
| `db.py` | PostgreSQL 杩炴帴銆佷簨鍔″拰鍋ュ悍妫€鏌?|
| `schema.sql` | pgvector 琛ㄧ粨鏋勫拰绱㈠紩 |
| `knowledge_base.py` | 瑙ｆ瀽 Markdown 鐭ヨ瘑鐗囨鍜?front matter |
| `embedding_provider.py` | 鐢熸垚鏂囨湰 embedding |
| `retriever.py` | 鎵ц鍚戦噺妫€绱㈠拰杩囨护 |
| `report_enhancer.py` | 鍚堟垚 `report_assist` |
| `llm_provider.py` | 鍙€夋帴鍏ラ樋閲岀櫨鐐肩瓑澶栭儴 LLM |
| `safety_rules.py` | 绂佹琛ㄨ堪銆佸尰鐢熷鏍告彁绀哄拰杈撳嚭鏍￠獙 |
| `ingest_knowledge.py` | 灏嗙煡璇嗗簱鍐欏叆 pgvector |

## 5. 鏁版嵁搴撹璁★細PostgreSQL + pgvector

### 5.1 鎵╁睍鍒濆鍖?
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 5.2 鐭ヨ瘑鐗囨琛?
embedding 缁村害闇€瑕佷笌鎵€閫?embedding 妯″瀷涓€鑷淬€備笅闈互 `1536` 涓虹ず渚嬶紝瀹為檯瀹炵幇鏃跺簲浠庨厤缃鍙栥€?
```sql
CREATE TABLE IF NOT EXISTS rag_documents (
    id BIGSERIAL PRIMARY KEY,
    source_id TEXT NOT NULL,
    title TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    tags TEXT[] NOT NULL DEFAULT '{}',
    version TEXT NOT NULL DEFAULT 'v1',
    language TEXT NOT NULL DEFAULT 'zh-CN',
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_rag_documents_source_hash
ON rag_documents(source_id, content_hash);

CREATE INDEX IF NOT EXISTS idx_rag_documents_tags
ON rag_documents USING GIN(tags);

CREATE INDEX IF NOT EXISTS idx_rag_documents_metadata
ON rag_documents USING GIN(metadata);

DROP INDEX IF EXISTS idx_rag_documents_embedding;

CREATE INDEX IF NOT EXISTS idx_rag_documents_embedding_hnsw
ON rag_documents USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

正式实现使用 HNSW 召回索引；ivfflat 仅保留为历史原型说明，不用于当前标准方案。
### 5.3 妫€绱?SQL 绀轰緥

```sql
SELECT
    source_id,
    title,
    doc_type,
    tags,
    content,
    metadata,
    1 - (embedding <=> $1) AS similarity
FROM rag_documents
WHERE enabled = TRUE
  AND ($2::text[] IS NULL OR tags && $2::text[])
ORDER BY embedding <=> $1
LIMIT $3;
```

## 6. 鐭ヨ瘑搴撳唴瀹硅鑼?
绗竴鐗堝彧浣跨敤鏈」鐩唴閮ㄥ彲鎺х煡璇嗭紝涓嶇洿鎺ヨ仈缃戞绱€?
鎺ㄨ崘鐭ヨ瘑鏂囦欢锛?
```text
HeadCTOrchestrator/rag/knowledge/
  artifact_quality.md
  hemorrhage_reporting.md
  safety_expression_rules.md
  report_templates.md
  cq500_label_notes.md
  orchestrator_contract.md
```

鍐呭鏉ユ簮锛?
- Filter 閲戝睘浼奖绛夌骇璇存槑銆?- LesionDetection 鐥呯伓绫诲瀷璇存槑銆?- CQ500 瀛楁璇存槑銆?- 鍖诲瀹夊叏琛ㄨ揪瑙勫垯銆?- 鎶ュ憡鑽夌妯℃澘銆?- Orchestrator API 鍚堝悓銆?
姣忎釜鐭ヨ瘑鐗囨寤鸿鍖呭惈 front matter锛?
```markdown
---
source_id: hemorrhage_reporting_v1
title: 棰呭唴鍑鸿鎶ュ憡杈呭姪璇存槑
type: report_template
tags: [head_ct, hemorrhage, report]
version: v1
---

褰撴ā鍨嬫湭鎻愮ず鏄庣‘棰呭唴鍑鸿鏃讹紝鎶ュ憡杈呭姪鏂囨湰搴斾娇鐢ㄢ€滄湭瑙佹槑纭€︹€﹀緛璞★紝寤鸿缁撳悎鍘熷褰卞儚澶嶆牳鈥濄€?涓嶅緱浣跨敤鈥滄帓闄ゅ嚭琛€鈥濃€滄棤闇€澶嶆牳鈥濈瓑缁濆琛ㄨ堪銆?```

### 6.1 artifact_quality.md

寤鸿鍖呭惈锛?
- 閲戝睘浼奖绛夌骇锛歯one銆乵ild銆乵oderate銆乻evere銆?- 鍚勭瓑绾у闃呯墖鍜岀梾鐏惰瘑鍒殑褰卞搷銆?- 浼奖閭昏繎鍖哄煙闇€瑕佸鏍哥殑琛ㄨ揪妯℃澘銆?- `LESION_SKIP_ON_SEVERE_ARTIFACT=true` 鏃剁殑璇存槑銆?
### 6.2 hemorrhage_reporting.md

寤鸿鍖呭惈锛?
- 棰呭唴鍑鸿浜屽垎绫绘ā鍨嬭緭鍑鸿В閲娿€?- 闃虫€с€侀槾鎬с€佷綆缃俊搴︿笁绫昏〃杈炬ā鏉裤€?- `confidence` 鍙〃绀烘ā鍨嬬疆淇″害锛屼笉浠ｈ〃涓村簥纭瘖姒傜巼銆?- 闇€瑕佸尰鐢熺粨鍚堝師濮嬪奖鍍忓鏍搞€?
### 6.3 safety_expression_rules.md

寤鸿鍖呭惈锛?
- 绂佹琛ㄨ堪娓呭崟銆?- 鎺ㄨ崘鏇夸唬琛ㄨ堪銆?- 鍖荤枟瀹夊叏鍏嶈矗澹版槑銆?- 鍖荤敓瀹℃牳浼樺厛鍘熷垯銆?
### 6.4 report_templates.md

寤鸿鍖呭惈锛?
- findings 妯℃澘銆?- impression 妯℃澘銆?- limitations 妯℃澘銆?- recommended_actions 妯℃澘銆?
### 6.5 cq500_label_notes.md

寤鸿鍖呭惈锛?
- CQ500 鏍囩瀛楁瑙ｉ噴銆?- 鍑鸿浜氬瀷鑱氬悎瑙勫垯銆?- 鏁版嵁闆嗘爣绛剧矑搴﹂檺鍒躲€?- 鐮旂┒/婕旂ず妯″瀷杈圭晫銆?
## 7. RAG 杈撳叆涓婁笅鏂?
RAG 涓嶇洿鎺ヨ鍘熷褰卞儚锛岃€屾槸鎺ユ敹缁撴瀯鍖栧垎鏋愮粨鏋滐細

```json
{
  "case_context": {
    "patient_id": "anonymous_patient_001",
    "study_id": "anonymous_study_001",
    "series_id": "anonymous_series_001"
  },
  "quality_control": {
    "artifact_detected": true,
    "severity": "moderate",
    "analysis_reliability": "limited_by_artifact",
    "affected_slices": [42, 43, 44]
  },
  "lesion_analysis": {
    "enabled": true,
    "status": "success",
    "results": [
      {
        "lesion_type": "intracranial_hemorrhage",
        "detected": false,
        "confidence": 0.08,
        "reliability": "limited_by_artifact"
      }
    ]
  },
  "warnings": []
}
```

RAG 杈撳嚭鍙兘澧炲己鏂囨湰鍜屽缓璁姩浣滐紝涓嶅緱淇敼涓婇潰鐨勬ā鍨嬪瓧娈点€?
## 8. 妫€绱㈡祦绋?
鎺ㄨ崘娴佺▼锛?
```text
1. Orchestrator 寰楀埌 quality_control 鍜?lesion_analysis
2. 鏋勯€?query_text 鍜?filter_tags
3. embedding_provider 鐢熸垚 query embedding
4. retriever 浠?pgvector 妫€绱?top_k 鐗囨
5. rerank 鎴栬鍒欒繃婊や綆鐩镐技搴︾墖娈?6. report_enhancer 缁撳悎鐗囨鐢熸垚 enhanced_report_assist
7. safety_rules 妫€鏌ョ姝㈣〃杩?8. 杈撳嚭 report_assist.rag_context.sources
9. 鍖荤敓鍦?review 涓‘璁ゃ€佷慨鏀规垨鎷掔粷
```

query 绀轰緥锛?
```text
head ct moderate metal artifact intracranial hemorrhage negative limited by artifact report template doctor review
```

tag 杩囨护绀轰緥锛?
```python
filter_tags = ["head_ct", "artifact", "hemorrhage", "report"]
```

## 9. retriever.py 璁捐

寤鸿鎺ュ彛锛?
```python
def retrieve_context(
    query_text: str,
    *,
    filter_tags: list[str] | None = None,
    top_k: int = 5,
    min_similarity: float = 0.55,
) -> dict:
    ...
```

杩斿洖锛?
```python
{
    "status": "success",
    "retrieval_confidence": 0.82,
    "sources": [
        {
            "source_id": "hemorrhage_reporting_v1",
            "title": "棰呭唴鍑鸿鎶ュ憡杈呭姪璇存槑",
            "type": "report_template",
            "similarity": 0.82,
            "matched_terms": ["hemorrhage", "negative"],
            "used_for": ["lesion_text", "impression"]
        }
    ],
    "snippets": [
        {
            "source_id": "hemorrhage_reporting_v1",
            "content": "鏈鏄庣‘棰呭唴鍑鸿寰佽薄鏃讹紝搴旀彁绀哄尰鐢熺粨鍚堝師濮嬪奖鍍忓鏍搞€?
        }
    ],
    "fallback_reason": None
}
```

寮傚父琛屼负锛?
```text
濡傛灉 RAG_DB_DSN 鏈厤缃€乸gvector 涓嶅彲鐢ㄣ€佹绱㈡棤缁撴灉鎴?SQL 鎵ц澶辫触锛宺etrieve_context 搴旀姏鍑?RagRetrievalError銆?Orchestrator 搴斿皢浠诲姟鏍囪涓?failed锛屽苟杩斿洖 RAG_RETRIEVAL_FAILED銆?```

## 10. report_assist 杈撳嚭缁撴瀯

RAG 澧炲己鍚庡缓璁湪 `report_assist` 涓ˉ鍏咃細

```json
{
  "rag_enhanced": true,
  "suggested_report_sections": {
    "findings": [],
    "impression": [],
    "limitations": []
  },
  "recommended_actions": [],
  "rag_context": {
    "enabled": true,
    "status": "success",
    "retrieval_confidence": 0.82,
    "query_terms": [
      "head_ct",
      "metal_artifact",
      "intracranial_hemorrhage",
      "limited_by_artifact"
    ],
    "sources": [],
    "fallback_reason": null
  },
  "llm_context": {
    "enabled": false,
    "provider": "rule_template",
    "model": null,
    "status": "disabled",
    "prompt_version": "report_assist_v1",
    "fallback_reason": null
  },
  "requires_doctor_review": true
}
```

## 11. 澶栭儴 LLM 鍙€夋帴鍏ワ細闃块噷鐧剧偧

澶栭儴 LLM 鍙綔涓哄彲閫夊寮鸿兘鍔涳紝榛樿鍏抽棴銆傛帹鑽愬垎灞傦細

```text
缁撴瀯鍖栨ā鍨嬬粨鏋?  + RAG 妫€绱㈢墖娈?  + 瀹夊叏琛ㄨ揪绾︽潫
  -> LLM 鐢熸垚 report_assist 鑽夌
  -> safety_rules 浜屾妫€鏌?  -> 鍖荤敓瀹℃牳
```

娉ㄦ剰锛?
- LLM 涓嶈鍙栧師濮?CT銆?- LLM 涓嶄慨鏀?`quality_control`銆乣lesion_analysis` 鍘熷瀛楁銆?- LLM 鍙敓鎴愭姤鍛婅緟鍔╂枃鏈€佸缓璁姩浣滃拰闄愬埗璇存槑銆?- LLM 杈撳嚭蹇呴』缁忚繃 `safety_rules.py` 妫€鏌ャ€?- `LLM_ENABLED=true` 鏃跺繀椤昏皟鐢ㄧ湡瀹炲閮?LLM锛涘閮?LLM 涓嶅彲鐢ㄣ€丄PI Key 缂哄け銆佸搷搴旈潪娉曟垨瀹夊叏妫€鏌ュけ璐ユ椂锛屼换鍔″簲澶辫触锛屼笉鍥炶惤鍒拌鍒欐ā鏉裤€?
鎺ㄨ崘骞冲彴锛?
```text
闃块噷浜戠櫨鐐?/ DashScope / Model Studio
```

OpenAI 鍏煎鎺ュ彛绀轰緥锛?
```text
base_url = https://dashscope.aliyuncs.com/compatible-mode/v1
model    = qwen-plus
```

瀹樻柟鍙傝€冿細

```text
https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope
```

鐜鍙橀噺锛?
```powershell
$env:RAG_ENABLED="true"
$env:RAG_VECTOR_BACKEND="pgvector"
$env:LLM_PROVIDER="aliyun_bailian"
$env:LLM_ENABLED="false"
$env:ALI_BAILIAN_API_KEY="your_api_key"
$env:ALI_BAILIAN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:ALI_BAILIAN_MODEL="qwen-plus"
$env:ALI_BAILIAN_TIMEOUT_SECONDS="30"
```

榛樿寤鸿锛?
```text
RAG_ENABLED=true
RAG_VECTOR_BACKEND=pgvector
LLM_ENABLED=false
LLM_PROVIDER=rule_template
```

## 12. 闅愮涓庤劚鏁忚姹?
璋冪敤 embedding 鏈嶅姟鎴栧閮?LLM 鍓嶅繀椤昏劚鏁忥細

- 涓嶅彂閫佹偅鑰呭鍚嶃€?- 涓嶅彂閫佽韩浠借瘉鍙枫€佹墜鏈哄彿銆佷綇鍧€銆?- 涓嶅彂閫佸畬鏁存鏌ュ彿銆?- `patient_id`銆乣study_id`銆乣series_id` 濡傞渶鍙戦€侊紝搴斾娇鐢ㄥ唴閮ㄥ尶鍚?ID銆?- 涓嶅彂閫佸師濮嬪奖鍍忔枃浠躲€?- 涓嶅彂閫佸畬鏁存姤鍛婃鏂囷紝闄ら潪宸茬粡杩囪劚鏁忓拰鎺堟潈銆?
寤鸿鍙戦€侊細

```json
{
  "case_context": {
    "patient_id": "anonymous_patient_001",
    "study_id": "anonymous_study_001"
  }
}
```

## 13. 瀹夊叏琛ㄨ堪瑙勫垯

绂佹杈撳嚭锛?
```text
纭瘖
鎺掗櫎
鏃犻渶澶嶆牳
鏃犻渶鍖荤敓瀹℃牳
鑷姩瀹屾垚璇婃柇
鏈€缁堣瘖鏂负
```

鎺ㄨ崘杈撳嚭锛?
```text
鐤戜技
鏈鏄庣‘
寤鸿澶嶆牳
鍙兘鍙椾吉褰卞奖鍝?渚涘尰鐢熷弬鑰?璇风粨鍚堜复搴婁笌鍘熷褰卞儚
```

LLM 鎴栬鍒欐ā鏉胯緭鍑哄悗蹇呴』鎵ц锛?
```text
safety_rules.validate_report_safety(...)
```

妫€鏌ュ唴瀹癸細

- 鏄惁鍖呭惈绂佹琛ㄨ堪銆?- 鏄惁鍖呭惈鍖荤敓澶嶆牳鎻愮ず銆?- 鏄惁澹扮О鏈€缁堣瘖鏂€?- 鏄惁涓庢ā鍨嬬粨鏋勫寲缁撴灉鐭涚浘銆?- 鏄惁閬楁紡浼奖闄愬埗璇存槑銆?
濡傛灉鏈€氳繃锛?
```text
1. 涓㈠純涓嶅悎鏍艰緭鍑?2. 鎶涘嚭 LlmProviderError 鎴?ReportEnhancementError
3. Orchestrator 灏嗕换鍔℃爣璁颁负 failed
4. error_code = LLM_PROVIDER_FAILED
```

## 14. 瀹炵幇姝ラ

### Step 1锛氬垵濮嬪寲 pgvector

- 鍑嗗 PostgreSQL 鏁版嵁搴撱€?- 瀹夎骞跺惎鐢?`vector` 鎵╁睍銆?- 鎵ц `rag/schema.sql`銆?- 閰嶇疆杩炴帴鐜鍙橀噺銆?
寤鸿鐜鍙橀噺锛?
```powershell
$env:RAG_DB_DSN="postgresql://user:password@localhost:5432/head_ct_ai"
$env:RAG_VECTOR_BACKEND="pgvector"
$env:RAG_TOP_K="5"
$env:RAG_MIN_SIMILARITY="0.55"
```

### Step 2锛氭柊澧炵煡璇嗗簱 Markdown

鍏堣ˉ榻愶細

```text
artifact_quality.md
hemorrhage_reporting.md
safety_expression_rules.md
report_templates.md
cq500_label_notes.md
orchestrator_contract.md
```

### Step 3锛氬疄鐜?embedding_provider.py

寤鸿鍏堟娊璞℃帴鍙ｏ細

```python
def embed_text(text: str) -> list[float]:
    ...
```

绗竴鐗堝彲浠ユ敮鎸侊細

- 鏈湴 embedding 妯″瀷銆?- 澶栭儴 embedding API銆?- 娴嬭瘯鐜 deterministic fake embedding銆?
娴嬭瘯鐜蹇呴』涓嶄緷璧栧缃戙€?
### Step 4锛氬疄鐜?ingest_knowledge.py

鑱岃矗锛?
- 璇诲彇 `rag/knowledge/*.md`銆?- 鎸?front matter 鎴栨爣棰樺垏鍒嗙煡璇嗙墖娈点€?- 鐢熸垚 `content_hash`銆?- 鐢熸垚 embedding銆?- upsert 鍒?`rag_documents`銆?
### Step 5锛氬疄鐜?retriever.py

鑱岃矗锛?
- 鎺ユ敹 query_text銆?- 鐢熸垚 query embedding銆?- 鎵ц pgvector 鐩镐技搴︽绱€?- 杩囨护浣庝簬 `RAG_MIN_SIMILARITY` 鐨勭墖娈点€?- 杩斿洖 snippets銆乻ources銆乺etrieval_confidence銆?
### Step 6锛氬疄鐜?report_enhancer.py

鑱岃矗锛?
- 鎺ユ敹 `base_report_assist`銆乣quality_control`銆乣lesion_analysis`銆乣case_context`銆?- 鏋勯€犳煡璇㈡枃鏈拰 tag銆?- 璋冪敤 retriever銆?- 閫氳繃瑙勫垯妯℃澘鐢熸垚澧炲己鏂囨湰銆?- 鍙€夎皟鐢?`llm_provider.py`銆?- 杩愯 `safety_rules.py`銆?- 鍐欏叆 `rag_context` 鍜?`llm_context`銆?
寤鸿鎺ュ彛锛?
```python
def enhance_report_assist(
    base_report_assist: dict,
    quality_control: dict,
    lesion_analysis: dict,
    case_context: dict,
) -> dict:
    ...
```

### Step 7锛氭帴鍏?OrchestratorServer.py

褰撳墠娴佺▼锛?
```text
combine_report_assist(...)
```

寤鸿鏀逛负锛?
```text
base_report_assist = combine_report_assist(...)
report_assist = enhance_report_assist(
    base_report_assist,
    quality_control,
    lesion_analysis,
    case_context,
)
```

娉ㄦ剰锛?
- RAG 澶辫触涓嶈兘瀵艰嚧涓讳换鍔″け璐ャ€?- RAG 澧炲己涓嶈兘鏀瑰啓 `quality_control` 鍜?`lesion_analysis`銆?- RAG 澧炲己缁撴灉搴斿啓鍏?`orchestrator_result.json.report_assist`銆?- 濡傛灉 LLM 璋冪敤澶辫触鎴栧畨鍏ㄦ鏌ュけ璐ワ紝蹇呴』璁╀换鍔″け璐ュ苟杩斿洖 `LLM_PROVIDER_FAILED`锛屼笉鑳界敓鎴愪吉鎴愬姛鐨勬姤鍛婅緟鍔╂枃鏈€?
## 15. 娴嬭瘯寤鸿

寤鸿鏂囦欢锛?
```text
HeadCTOrchestrator/tests/test_report_rag_enhancer.py
HeadCTOrchestrator/tests/test_rag_retriever_pgvector.py
HeadCTOrchestrator/tests/test_rag_ingest_knowledge.py
HeadCTOrchestrator/tests/test_rag_llm_provider.py
```

娴嬭瘯椤癸細

```text
test_rag_ingest_parses_markdown_front_matter
test_rag_retriever_returns_sources_from_pgvector
test_rag_retriever_requires_pgvector_dsn
test_rag_enhancer_adds_sources
test_rag_enhancer_fails_when_pgvector_unavailable
test_rag_does_not_change_model_fields
test_safety_rules_remove_prohibited_claims
test_report_assist_requires_doctor_review
test_report_assist_contains_limitations_when_artifact_is_moderate_or_severe
test_llm_provider_disabled_uses_rule_template
test_aliyun_bailian_provider_raises_on_timeout
test_llm_output_fails_when_contains_prohibited_claim
test_llm_prompt_does_not_include_raw_patient_identity
```

## 16. 閿欒鐮佸缓璁?
```text
RAG_RETRIEVAL_FAILED
RAG_EMBEDDING_FAILED
RAG_INGEST_FAILED
RAG_SAFETY_CHECK_FAILED
LLM_PROVIDER_FAILED
LLM_OUTPUT_INVALID
LLM_SAFETY_CHECK_FAILED
LLM_PRIVACY_CHECK_FAILED
```

| 閿欒鐮?| 鍚箟 |
| --- | --- |
| `RAG_RETRIEVAL_FAILED` | pgvector 鏈厤缃€佷笉鍙敤銆佹绱㈡棤缁撴灉鎴栧悜閲忔绱㈠け璐?|
| `RAG_EMBEDDING_FAILED` | 鏌ヨ鎴栫煡璇嗙墖娈?embedding 鐢熸垚澶辫触 |
| `RAG_INGEST_FAILED` | 鐭ヨ瘑搴撳叆搴撳け璐?|
| `RAG_SAFETY_CHECK_FAILED` | RAG 鐢熸垚鍐呭鏈€氳繃瀹夊叏琛ㄨ揪妫€鏌?|
| `LLM_PROVIDER_FAILED` | 闃块噷鐧剧偧璋冪敤瓒呮椂銆佺綉缁滃け璐ャ€丄PI Key 缂哄け銆佹湇鍔′笉鍙敤鎴栬緭鍑烘湭閫氳繃瀹夊叏妫€鏌?|
| `LLM_OUTPUT_INVALID` | 澶栭儴 LLM 杈撳嚭涓嶆槸鍚堟硶 JSON锛屾垨涓嶇鍚?`report_assist` 缁撴瀯 |
| `LLM_SAFETY_CHECK_FAILED` | 澶栭儴 LLM 杈撳嚭鍖呭惈绂佹琛ㄨ堪锛屾垨鏈€氳繃瀹夊叏琛ㄨ揪妫€鏌?|
| `LLM_PRIVACY_CHECK_FAILED` | prompt 涓瓨鍦ㄦ湭鑴辨晱鎮ｈ€呰韩浠戒俊鎭紝绂佹璋冪敤澶栭儴 LLM |

## 17. 楠屾敹鏍囧噯

- RAG 浣跨敤 pgvector 鎴栧叾浠栧悜閲忔暟鎹簱瀹屾垚璇箟妫€绱紝涓嶅啀浠ョ函鍏抽敭璇嶆绱綔涓烘寮忔柟妗堛€?- `rag_documents` 鑳戒繚瀛樼煡璇嗙墖娈点€佹潵婧愩€佹爣绛俱€佺増鏈€乵etadata 鍜?embedding銆?- 鐭ヨ瘑搴撳彲閲嶅鍏ュ簱锛屽悓涓€ `source_id + content_hash` 涓嶉噸澶嶆彃鍏ャ€?- `retrieve_context()` 鑳借繑鍥?top_k sources銆乻nippets 鍜?similarity銆?- 鍚敤 RAG 鍚庯紝鍚戦噺鏁版嵁搴撲笉鍙敤鏃朵换鍔″け璐ュ苟杩斿洖 `RAG_RETRIEVAL_FAILED`锛屼笉鍥炶惤鍒版湰鍦板叧閿瘝妫€绱€?- RAG 涓嶄慨鏀?`quality_control`銆乣lesion_analysis` 涓殑妯″瀷鍘熷瀛楁銆?- `report_assist.rag_context.sources` 鑳借鍖荤敓绔睍绀哄拰杩芥函銆?- `LLM_ENABLED=false` 鏃讹紝绯荤粺閫氳繃 pgvector RAG + 瑙勫垯妯℃澘鐢熸垚 `report_assist`銆?- `LLM_ENABLED=true` 涓?`LLM_PROVIDER=aliyun_bailian` 鏃讹紝蹇呴』鐪熷疄璋冪敤闃块噷鐧剧偧骞惰褰?provider銆乵odel銆乻tatus 鍜?prompt_version銆?- 澶栭儴 LLM 璋冪敤鍓嶅繀椤诲畬鎴愯劚鏁忔鏌ャ€?- API Key 涓嶅緱鍐欏叆鏃ュ織銆佸搷搴?JSON銆佸璁℃枃浠舵垨鍓嶇椤甸潰銆?- 绂佹琛ㄨ堪涓嶄細鍑虹幇鍦?`report_assist` 涓€?- 鑷姩鍖栨祴璇曢€氳繃銆?
## 18. 鍚庣画鎵╁睍

- 鎺ュ叆闄㈠唴姝ｅ紡鎶ュ憡妯℃澘搴撱€?- 鎺ュ叆鏇村鐥呯伓绫诲瀷瀵瑰簲鐭ヨ瘑鐗囨銆?- 澧炲姞 hybrid search锛氬叧閿瘝杩囨护 + 鍚戦噺妫€绱?+ rerank銆?- 澧炲姞鐭ヨ瘑鐗囨瀹℃牳宸ヤ綔娴侊紝鍖哄垎鑽夌銆佸凡瀹℃牳銆佸簾寮冪増鏈€?- 澧炲姞鍖荤敓瀵?RAG 杈撳嚭鐨勮瘎鍒嗗拰閲囩撼鐜囩粺璁°€?- 鑰冭檻浣跨敤鏁版嵁搴撳仛鎸佷箙鍖?
