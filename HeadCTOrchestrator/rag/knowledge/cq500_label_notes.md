---
source_id: cq500_label_notes_v2
title: CQ500 与颅内出血标签说明
type: dataset_note
tags: [head_ct, hemorrhage, cq500, dataset]
version: v2
language: zh-CN
---

# CQ500 与颅内出血标签说明

## 数据集用途

CQ500 可用于头颅 CT 急诊场景研究和颅内出血分类模型训练。数据集标签来自读片标注，适合训练辅助识别模型，但不能直接代表临床最终诊断。

## 出血亚型

常见字段包括 epidural、intraparenchymal、intraventricular、subarachnoid、subdural 等。任一亚型阳性时，可聚合为 hemorrhage 阳性。

## 标签局限

标签粒度、读片一致性、扫描协议差异和影像质量都会影响模型训练结果。模型输出应被解释为风险提示或辅助分析，不应直接写成确诊。

## 报告辅助要求

当模型提示出血阳性时，应建议医生结合原始影像复核出血部位、范围、密度、脑室受压、中线移位和临床症状。当模型阴性时，也应提示阴性结果不能替代医生阅片。
