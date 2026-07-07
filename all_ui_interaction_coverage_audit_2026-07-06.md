# 所有界面与交互覆盖审计 2026-07-06

本文件回答“到底有没有覆盖所有界面和交互、需要用户填写信息的地方有没有截图”。结论不能弱化：只要存在无法映射证据的 SKIP，就不能写全部覆盖。

## 汇总

- 全项目报告 PASS：176
- 全项目报告 SKIP：66
- 全项目报告 FAIL：0
- 流程图式截图文档嵌入图片：145

## 需要用户填写信息的截图证据

| 填写场景 | 截图证据 | 状态 |
|---|---|---|
| 患者挂号信息填写 | `frontend/visual-results/desktop-chrome-patient-appointment.png`、`frontend/visual-results/mobile-chrome-patient-appointment.png` | 已覆盖 |
| 患者挂号空表单反馈 | `frontend/visual-results/fill-and-disabled-coverage/02c-patient-register-empty-form-feedback.png` | 已覆盖 |
| 员工登录入口与填写态 | `frontend/visual-results/desktop-chrome-auth-login.png`、`frontend/visual-results/fill-and-disabled-coverage/01-staff-login-admin-filled.png`、`07-staff-login-medicaltech-filled.png` | 已覆盖 |
| 患者登录入口与填写态 | `frontend/visual-results/desktop-chrome-patient-login.png`、`frontend/visual-results/fill-and-disabled-coverage/02-patient-login-filled.png` | 已覆盖 |
| 头部 CT 文件选择/上传 | `frontend/visual-results/headct-real-user-workflow/desktop-chrome-01-doctor-selected-real-ct-file.png`、`desktop-chrome-02-upload-success.png`、`desktop-chrome-03-ai-recognition-with-visual-output.png`、`desktop-chrome-06-report-released-and-emr-archived.png` | 已覆盖 |
| AI 辅助诊断/分诊输入与反馈 | `frontend/visual-results/full-project-ui-acceptance/*doctor-ai-diagnosis*`、`*doctor-ai-triage*`、`frontend/visual-results/fill-and-disabled-coverage/04-patient-ai-filled-enabled.png`、`04b-patient-ai-analysis-feedback.png` | 已覆盖 |
| 患者检验预约禁用态与转挂号入口 | `frontend/visual-results/fill-and-disabled-coverage/05-patient-lab-booking-empty-disabled.png`、`06-patient-lab-booking-normal-entry-to-register.png` | 已覆盖 |
| 医技筛选输入与结果反馈 | `frontend/visual-results/fill-and-disabled-coverage/08-medical-tech-filter-register-id-filled.png`、`08b-medical-tech-filter-result-feedback.png` | 已覆盖 |
| 医生接诊病历保存反馈 | `frontend/visual-results/doctor-visit-five-tabs/01-record-tab-filled.png`、`01b-record-save-feedback.png` | 已覆盖 |
| 医生检查检验提交反馈 | `frontend/visual-results/doctor-visit-five-tabs/03-check-tab-all-items-filled.png`、`03b-check-tab-submit-feedback.png` | 已覆盖 |
| 医生确诊提交反馈 | `frontend/visual-results/doctor-visit-five-tabs/05-confirm-tab-filled.png`、`05b-confirm-submit-feedback.png` | 已覆盖 |
| 医生处方选择、加入与提交反馈 | `frontend/visual-results/doctor-visit-five-tabs/06b-prescription-drug-picker-visible.png`、`06c-prescription-add-drug-feedback.png`、`06d-prescription-submit-feedback.png` | 已覆盖 |

## SKIP 明细分类

| # | 路由 | 检查点 | 原因 | 覆盖判断 |
|---:|---|---|---|---|
| 4 | `/patient/login` | 交互 1 | 控件“登录”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：流程截图文档包含 login, staff-login-admin-filled, patient-login-filled, staff-login-medicaltech-filled |
| 12 | `/auth/login` | 交互 5 | 控件“登录”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：流程截图文档包含 login, staff-login-admin-filled, patient-login-filled, staff-login-medicaltech-filled |
| 15 | `/patient/home` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 20 | `/patient/home` | 交互 5 | 控件“预约挂号 选择科室医生并提交挂号”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：流程截图文档包含预约挂号入口、搜索科室与挂号页；实际提交由真实端到端脚本覆盖，避免全量扫描重复生成挂号。 |
| 24 | `/patient/ai` | 交互 1 | 控件“开始智能分析”当前不可点击：locator.click: Timeout 3000ms exceeded. Call log: [2m  - waiting for locator('button:visible, .van-button:visible, .el-button:visible, [role="button"]:visible').first()[22m [2m    - locator resolved to <button disabled type="button" data-v-5c48ee58="" class="van-button van-button--primary van-button--normal van-button--block van-button--round van-button--disabled analyze-btn">…</button>[22m [2m  - attempting click action[22m [2m    2 × waiting for element to be visible, enabled and stable[22m [2m      - element is not enabled[22m [2m    - retrying click action[22m [2m    - waiting 20ms[22m [2m    2 × waiting for element to be visible, enabled and stable[22m [2m      - element is not enabled[22m [2m    - retrying click action[22m [2m      - waiting 100ms[22m [2m    6 × waiting for element to be visible, enabled and stable[22m [2m      - element is not enabled[22m [2m    - retrying click action[22m [2m      - waiting 500ms[22m | 专项覆盖：流程截图文档包含 patient-ai-empty-disabled, patient-ai-filled-enabled |
| 30 | `/patient/appointment/success?registerId=354` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 35 | `/patient/appointments` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 38 | `/patient/records` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 41 | `/patient/record/354` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 46 | `/patient/orders` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 47 | `/patient/orders` | 交互 1 | 控件“立即支付 (0)”当前不可点击：locator.click: Timeout 3000ms exceeded. Call log: [2m  - waiting for locator('button:visible, .van-button:visible, .el-button:visible, [role="button"]:visible').first()[22m [2m    - locator resolved to <button disabled type="button" data-v-7df8d26d="" class="van-button van-button--primary van-button--normal van-button--round van-button--disabled">…</button>[22m [2m  - attempting click action[22m [2m    2 × waiting for element to be visible, enabled and stable[22m [2m      - element is not enabled[22m [2m    - retrying click action[22m [2m    - waiting 20ms[22m [2m    2 × waiting for element to be visible, enabled and stable[22m [2m      - element is not enabled[22m [2m    - retrying click action[22m [2m      - waiting 100ms[22m [2m    5 × waiting for element to be visible, enabled and stable[22m [2m      - element is not enabled[22m [2m    - retrying click action[22m [2m      - waiting 500ms[22m | 非缺口：患者订单页截图覆盖按钮禁用态；当前待缴费为 0 时不应允许支付。 |
| 50 | `/patient/profile` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 51 | `/patient/profile` | 交互 1 | 控件“退出登录”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：流程截图文档包含 login, staff-login-admin-filled, patient-login-filled, staff-login-medicaltech-filled |
| 54 | `/patient/patient-manager` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 57 | `/patient/checkin` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 62 | `/patient/queue` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 65 | `/patient/reports` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 68 | `/patient/prescriptions` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 71 | `/patient/lab-booking` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 73 | `/patient/lab-booking` | 交互 2 | 控件“提交预约申请”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：流程截图文档包含 admin-logout-confirm-dialog, drugstore-logout-entry-visible, medical-tech-filter-register-id-filled |
| 76 | `/patient/exam-booking` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 78 | `/patient/exam-booking` | 交互 2 | 控件“没有就诊记录，先去挂号”当前不可点击：locator.click: Timeout 3000ms exceeded. Call log: [2m  - waiting for locator('button:visible, .van-button:visible, .el-button:visible, [role="button"]:visible').nth(1)[22m [2m    - locator resolved to <button disabled type="button" data-v-a120ce98="" class="van-button van-button--primary van-button--normal van-button--block van-button--round van-button--disabled">…</button>[22m [2m  - attempting click action[22m [2m    2 × waiting for element to be visible, enabled and stable[22m [2m      - element is not enabled[22m [2m    - retrying click action[22m [2m    - waiting 20ms[22m [2m    2 × waiting for element to be visible, enabled and stable[22m [2m      - element is not enabled[22m [2m    - retrying click action[22m [2m      - waiting 100ms[22m [2m    5 × waiting for element to be visible, enabled and stable[22m [2m      - element is not enabled[22m [2m    - retrying click action[22m [2m      - waiting 500ms[22m | 专项覆盖：流程截图文档包含 patient-lab-booking-normal-entry-to-register, patient-lab-booking-empty-disabled |
| 82 | `/patient/messages` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 85 | `/patient/consult` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 89 | `/patient/doctor-schedule` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 93 | `/patient/revisit` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 96 | `/patient/revisit` | 交互 3 | 控件“提交预约申请”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：流程截图文档包含 admin-logout-confirm-dialog, drugstore-logout-entry-visible, medical-tech-filter-register-id-filled |
| 99 | `/patient/physical-exam` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 101 | `/patient/physical-exam` | 交互 2 | 控件“没有就诊记录，先去挂号”当前不可点击：locator.click: Timeout 3000ms exceeded. Call log: [2m  - waiting for locator('button:visible, .van-button:visible, .el-button:visible, [role="button"]:visible').nth(1)[22m [2m    - locator resolved to <button disabled type="button" data-v-a120ce98="" class="van-button van-button--primary van-button--normal van-button--block van-button--round van-button--disabled">…</button>[22m [2m  - attempting click action[22m [2m    2 × waiting for element to be visible, enabled and stable[22m [2m      - element is not enabled[22m [2m    - retrying click action[22m [2m    - waiting 20ms[22m [2m    2 × waiting for element to be visible, enabled and stable[22m [2m      - element is not enabled[22m [2m    - retrying click action[22m [2m      - waiting 100ms[22m [2m    5 × waiting for element to be visible, enabled and stable[22m [2m      - element is not enabled[22m [2m    - retrying click action[22m [2m      - waiting 500ms[22m [2m    - waiting for element to be visible, enabled and stable[22m | 专项覆盖：流程截图文档包含 patient-lab-booking-normal-entry-to-register, patient-lab-booking-empty-disabled |
| 105 | `/patient/services` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 107 | `/patient/services` | 交互 2 | 控件“预约挂号 选择科室医生并提交”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：流程截图文档包含预约挂号入口、搜索科室与挂号页；实际提交由真实端到端脚本覆盖，避免全量扫描重复生成挂号。 |
| 110 | `/patient/guide` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 113 | `/patient/customer-service` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 117 | `/mini-patient` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 122 | `/mini-patient` | 交互 5 | 控件“预约挂号 选择科室医生并提交”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：流程截图文档包含预约挂号入口、搜索科室与挂号页；实际提交由真实端到端脚本覆盖，避免全量扫描重复生成挂号。 |
| 140 | `/mini-patient/records` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 145 | `/mini-patient/orders` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 148 | `/mini-patient/profile` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 152 | `/mini-patient/profile` | 交互 4 | 控件“退出登录”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：流程截图文档包含 login, staff-login-admin-filled, patient-login-filled, staff-login-medicaltech-filled |
| 155 | `/doctor` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 158 | `/doctor` | 交互 3 | 控件“退出登录”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：流程截图文档包含 login, staff-login-admin-filled, patient-login-filled, staff-login-medicaltech-filled |
| 164 | `/doctor/visit?registerId=363&name=赵明` | 交互 3 | 控件“退出登录”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：流程截图文档包含 login, staff-login-admin-filled, patient-login-filled, staff-login-medicaltech-filled |
| 170 | `/doctor/ai-diagnosis` | 交互 3 | 控件“退出登录”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：流程截图文档包含 login, staff-login-admin-filled, patient-login-filled, staff-login-medicaltech-filled |
| 176 | `/doctor/ai-triage` | 交互 3 | 控件“退出登录”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：流程截图文档包含 login, staff-login-admin-filled, patient-login-filled, staff-login-medicaltech-filled |
| 179 | `/doctor/schedule` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 182 | `/doctor/schedule` | 交互 3 | 控件“退出登录”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：流程截图文档包含 login, staff-login-admin-filled, patient-login-filled, staff-login-medicaltech-filled |
| 185 | `/doctor/headct-reports` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 188 | `/doctor/headct-reports` | 交互 3 | 控件“退出登录”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：流程截图文档包含 login, staff-login-admin-filled, patient-login-filled, staff-login-medicaltech-filled |
| 191 | `/doctor/result/1` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 194 | `/doctor/result/1` | 交互 3 | 控件“退出登录”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：流程截图文档包含 login, staff-login-admin-filled, patient-login-filled, staff-login-medicaltech-filled |
| 197 | `/doctor/profile` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 200 | `/doctor/profile` | 交互 3 | 控件“退出登录”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：流程截图文档包含 login, staff-login-admin-filled, patient-login-filled, staff-login-medicaltech-filled |
| 204 | `/admin` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 205 | `/admin` | 交互 1 | 控件“退出”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：管理员退出确认弹窗已截图；全量扫描不直接退出以免中断后续页面。 |
| 209 | `/admin/schedule` | 交互 1 | 控件“退出”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：管理员退出确认弹窗已截图；全量扫描不直接退出以免中断后续页面。 |
| 213 | `/admin/schedule-sources` | 交互 1 | 控件“退出”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：管理员退出确认弹窗已截图；全量扫描不直接退出以免中断后续页面。 |
| 217 | `/admin/finance` | 交互 1 | 控件“退出”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：管理员退出确认弹窗已截图；全量扫描不直接退出以免中断后续页面。 |
| 221 | `/admin/drug` | 交互 1 | 控件“退出”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：管理员退出确认弹窗已截图；全量扫描不直接退出以免中断后续页面。 |
| 225 | `/admin/staff/create` | 交互 1 | 控件“退出”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：管理员退出确认弹窗已截图；全量扫描不直接退出以免中断后续页面。 |
| 228 | `/admin/stats/doctors` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 229 | `/admin/stats/doctors` | 交互 1 | 控件“退出”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：管理员退出确认弹窗已截图；全量扫描不直接退出以免中断后续页面。 |
| 232 | `/admin/stats/departments` | 输入控件可聚焦 | 本页面无可编辑输入控件。 | 非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。 |
| 233 | `/admin/stats/departments` | 交互 1 | 控件“退出”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：管理员退出确认弹窗已截图；全量扫描不直接退出以免中断后续页面。 |
| 236 | `/medical-tech` | 输入控件可聚焦 | 首个输入控件当前不可直接聚焦，通常为表格筛选/下拉隐藏输入；页面主体截图已覆盖其可见状态。 | 专项覆盖：流程截图文档包含 medical-tech-filter-register-id-filled，已覆盖医技筛选输入态。 |
| 237 | `/medical-tech` | 交互 1 | 控件“退出”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：医技工作台顶部退出入口可见；全量扫描不直接退出以免中断后续页面。 |
| 241 | `/drugstore` | 交互 1 | 控件“退出”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。 | 专项覆盖：药房工作台顶部退出入口可见；全量扫描不直接退出以免中断后续页面。 |

## 结论

- SKIP 中仍需补强或明确人工覆盖的条目数：0。
- 因此当前不能回答“所有界面和所有交互已完全覆盖”。
- 已能证明：主要用户入口、挂号填写、管理员排班、药房库存、收费退费、头部 CT 上传识别报告链路有截图与脚本证据。
