---
source_id: model_result_interpretation_v1
title: 头颅 CT 模型结果解释规范
type: model_interpretation
tags: [head_ct, model_result, lesion, artifact, report]
version: v1
language: zh-CN
---

# 头颅 CT 模型结果解释规范

## 质控模型

金属伪影检测模型输出用于提示影像质量和局部可评价性。伪影掩膜和严重程度不能被解释为病灶本身。

## 病灶模型

病灶识别模型输出包括病灶类型、置信度和可能受影响层面。模型结果应与原始影像、临床症状和医生阅片结合使用。

## 置信度解释

置信度是模型内部评分，不等同于疾病发生概率。高置信度提示医生重点复核，低置信度或阴性结果也不能替代医生判断。

## 报告使用

报告中可以引用 AI 辅助分析提示，但应避免绝对化表达。推荐使用“AI 辅助分析提示”“建议医生复核”“可能受伪影影响”等措辞。
