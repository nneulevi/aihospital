---
source_id: orchestrator_contract_v2
title: HeadCTOrchestrator 结果合同说明
type: api_contract
tags: [head_ct, orchestrator, report, integration]
version: v2
language: zh-CN
---

# HeadCTOrchestrator 结果合同说明

## 核心结构

HeadCTOrchestrator 汇总以下结果：

- quality_control：来自 Filter 的伪影质控结果。
- lesion_analysis：来自病灶识别服务的结构化模型结果。
- report_assist：RAG/LLM 生成的报告辅助内容。
- warnings：流程级风险提示。

## 使用边界

`report_assist` 是报告草稿辅助字段，不是最终医学诊断。它可以进入 HeadCTReportService 生成草稿，但必须经过医生复核、审核、签名和发布。

## 审核记录

医生审核结果通过 review 相关接口和报告服务审计事件保存。原始 orchestrator_result.json 不应被覆盖，便于追溯模型输入、模型输出、RAG 引用和 LLM 生成上下文。

## 平台接入

Project2 主平台应优先调用 Orchestrator，而不是直接调用 Filter 或 LesionDetection。这样可以保证质控、病灶识别、RAG 报告辅助和后续报告服务使用统一合同。
