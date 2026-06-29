---
source_id: hemorrhage_reporting_v2
title: 颅内出血 AI 辅助报告表达规范
type: report_template
tags: [head_ct, hemorrhage, report, safety]
version: v2
language: zh-CN
---

# 颅内出血 AI 辅助报告表达规范

## 模型输出解释

颅内出血模型输出属于 AI 辅助分析结果。`confidence` 表示模型置信度，不代表临床确诊概率，也不能作为单独诊断依据。

## 阴性或低置信度结果

当模型未提示明确颅内出血，或置信度较低时，推荐表达为：AI 辅助分析未提示明确颅内出血征象，建议医生结合原始影像、临床表现和必要的复查结果审核。

不得使用“排除颅内出血”“无出血”“无需复核”等绝对化表达。

## 可疑阳性结果

当模型提示疑似颅内出血时，推荐表达为：AI 辅助分析提示疑似颅内出血相关征象，请医生结合原始 CT 图像、窗宽窗位、多平面重建和临床资料复核。

如果存在金属伪影、运动伪影或层厚较大，应在 limitations 中说明局部判断可能受限。

## 报告结构建议

- findings：描述影像质量、AI 提示区域、受限区域和需要复核的层面。
- impression：使用“疑似”“倾向”“建议复核”等审慎表达。
- limitations：必须说明 AI 结果仅供辅助参考，最终结论需医生审核。
- recommended_actions：可建议 review_original_ct、review_artifact_area、manual_report_review。

## 禁止表达

不得输出“确诊颅内出血”“排除出血”“最终诊断为”“无需医生审核”“自动完成诊断”。
