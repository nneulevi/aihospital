---
source_id: doctor_review_workflow_v1
title: 医生审核闭环与报告发布工作流
type: workflow_guideline
tags: [report, doctor_review, emr, workflow]
version: v1
language: zh-CN
---

# 医生审核闭环与报告发布工作流

## 报告生命周期

AI 报告辅助内容应先生成草稿，随后由报告医生编辑和复核。报告进入审核后，由审核医生确认或退回修改。审核通过后由签名医生签名，最后发布并分发到 EMR。

## 状态流转

推荐状态流转为：draft -> pending_review -> approved -> signed -> released。若审核医生要求修改，可流转到 revision_required，再由报告医生修改后重新提交。

## 审计要求

每次编辑、审核、签名、发布都应记录操作者、角色、时间、请求 ID 和变更原因。AI 生成草稿不能覆盖医生最终报告。

## RAG 引用

RAG 参考片段应作为辅助证据保存，用于解释报告建议来源。报告正文不应大量复制知识库原文，应由医生审核后形成最终表达。
