## 2026-06-27 头部 CT 正常业务链路验收口径更新

用户明确要求：头部 CT AI 流程、报告/EMR 链路不要使用 smoke，而应按正常工作环境走。

本轮已完成调整：

- 不再将 `scripts/smoke_test_headct_platform.py` 作为头部 CT AI、报告、EMR 链路通过依据。
- 将正式验收样本放入 `testdata/headct/head_ct_positive_case.nii.gz`。
- 更新 `scripts/e2e_project2_real_business.py`：
  - 从 Project2 主平台入口创建并执行真实业务链路；
  - 触发 AI 问诊、AI 辅助诊断、CT 上传、AI 影像分析、AI 报告生成；
  - 调用 HeadCTReportService 完成医生修改、提交审核、审核通过、签名、发布；
  - 调用 HeadCTEMRService 完成归档；
  - 回查 Project2 数据库持久化记录；
  - 不再运行时自动创建缺失表，缺表会直接失败并提示初始化数据库。

本轮执行：

```powershell
python scripts\e2e_project2_real_business.py
```

结果：

```text
status=success
project2=UP
orchestrator=ok
report=ok
emr=ok
ai_imaging_project_status=ready_for_project_demo
ai_imaging_workflow_ready=true
report_service_status=released
emr_status=final
ai_consultation=1
ai_diagnosis_suggestion=3
ai_image_analysis=1
ai_generated_report=1
```

详细证据见：

```text
Project2_头部CT正常业务链路验收记录.md
```

# Project2 与头部 CT AI 子系统全链路验收进度记录

更新时间：2026-06-22

## 本阶段结论

本阶段已完成“主平台 Project2 -> AI 子系统 -> 报告服务 -> EMR”的真实业务链路验收。

验收不是仅调用单个健康检查或小规模 smoke，而是通过 Project2 主平台 API 入口创建并执行一次完整门诊头颅 CT 场景：

```text
准备患者/挂号/病历/检查申请
-> Project2 AI 问诊分诊
-> Project2 AI 辅助诊断
-> Project2 上传头颅 CT
-> Project2 发起 AI 影像分析
-> HeadCTOrchestrator 编排 Filter + Lesion + RAG/LLM
-> Project2 生成 AI 报告草稿
-> HeadCTReportService 医生复核、审核、签名、发布
-> HeadCTEMRService 接收 final 报告
```

## 已完成改动

### 1. 服务启动脚本增强

文件：

```text
scripts/start_headct_platform.ps1
```

完成内容：

- 支持 `-Restart`，自动释放旧监听端口，不再需要手动查 PID、手动关闭旧进程。
- 默认使用稳定启动模式，保证端到端验收优先通过。
- 支持 `-Reload` 作为开发热更新模式。
- `-Reload` 仅对轻量 Python 服务启用：
  - `HeadCTOrchestrator`
  - `HeadCTReportService`
  - `HeadCTEMRService`
- `Filter` 和 `HeadCTLesionDetection` 由于加载 Torch/GPU 模型权重，默认保持稳定模式；需要更新模型服务代码时使用 `-Restart` 自动重启。
- Project2 已纳入一键启动范围，默认同时启动：
  - Filter `8000`
  - HeadCTOrchestrator `8010`
  - HeadCTLesionDetection `8021`
  - HeadCTReportService `8030`
  - HeadCTEMRService `8040`
  - Project2 `8092`

常用启动命令：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_headct_platform.ps1 -Restart
```

轻量服务热更新开发命令：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_headct_platform.ps1 -Restart -Reload
```

### 2. 主平台真实业务验收脚本

新增文件：

```text
scripts/e2e_project2_real_business.py
```

脚本能力：

- 自动准备最小真实业务上下文：
  - `patient`
  - `register`
  - `medical_record`
  - `check_request`
- 自动校准开发库中可能落后的 PostgreSQL sequence。
- 通过 Project2 API 调用 AI 问诊、AI 辅助诊断、CT 上传、AI 分析、报告生成。
- 从 Project2 落库快照中读取 HeadCTReportService 报告 ID。
- 继续执行报告医生复核、审核医生通过、签名、发布、EMR 分发。
- 校验 Project2 与下游服务均有持久化结果。

运行命令：

```powershell
python scripts\e2e_project2_real_business.py
```

## 本次验收结果

执行结果：

```json
{
  "status": "success",
  "business_case": {
    "patient_id": 2,
    "register_id": 8,
    "medical_record_id": 2,
    "check_request_id": 3,
    "case_suffix": "7245eac441"
  },
  "health": {
    "project2": "UP",
    "orchestrator": "ok",
    "report": "ok",
    "emr": "ok"
  },
  "consultation_id": 2,
  "consultation_recommendation_count": 2,
  "diagnosis_suggestion_count": 2,
  "image_file_id": 4,
  "analysis_id": 4,
  "analysis_confidence": 0.4617331326007843,
  "report_id": 3,
  "project2_report_status": "draft",
  "report_service_id": "abd3fd8f-129c-478e-bcd2-2812569f551f",
  "report_service_status": "released",
  "report_version_after_review": 2,
  "emr_document_id": "DR-D7DBE13114CC49F7B58CEF431FC2E3F8",
  "emr_status": "final",
  "persisted": {
    "ai_consultation": 1,
    "ai_diagnosis_suggestion": 2,
    "ai_image_analysis": 1,
    "ai_generated_report": 1
  }
}
```

验收结论：

- Project2 数据库连接正常。
- AI 问诊已通过 Project2 调用 HeadCTOrchestrator RAG + 阿里百炼 LLM。
- AI 辅助诊断已通过 Project2 调用 HeadCTOrchestrator RAG + 阿里百炼 LLM。
- CT 上传、AI 分析、报告生成均从 Project2 主平台入口完成。
- HeadCTReportService 的医生审核闭环已完成到 `released`。
- HeadCTEMRService 已收到 final 报告。

## 当前限制与处理策略

### 1. Python reload 的边界

Windows 当前环境中，Filter/Lesion 这类加载 Torch/GPU 模型的服务使用 `uvicorn --reload` 会触发 multiprocessing named pipe 权限错误。因此：

- 模型服务默认不启用 reload。
- Orchestrator/RAG、Report、EMR 可使用 `-Reload` 开发。
- 模型服务代码或权重变化时，使用 `-Restart` 自动释放端口并重启。

### 2. Project2 Java 热更新

Project2 当前未引入 `spring-boot-devtools`，本地 Maven 仓库也暂未缓存该依赖。因此本阶段先完成：

- Project2 一键启动。
- 旧端口监听自动释放。
- 真实业务端到端验收。

如后续允许下载依赖，可引入：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-devtools</artifactId>
    <scope>runtime</scope>
    <optional>true</optional>
</dependency>
```

然后在 IDEA 或 `spring-boot:run` 中启用 Java 侧热重载。

## 下一步建议

1. 将 `scripts/e2e_project2_real_business.py` 纳入阶段验收命令。
2. 为 Project2 补正式数据库迁移脚本，替代验收脚本中的最小表结构兜底。
3. 后续接入真实病灶模型 checkpoint 后，重复执行本脚本，比较 `analysis_confidence`、报告内容和医生审核链路。

## 2026-06-22 Project2 独立业务功能验收补充

主平台与头部 CT AI 子系统衔接验收完成后，已单独验证 Project2 独立业务功能。

详见：

```text
Project2_独立业务功能验收进度记录.md
```

关键结论：

- 新增医生接诊接口 `PUT /api/doctor/patients/{registerId}/receive`，补齐挂号到医生工作站流程断点。
- 新增 `scripts/e2e_project2_core_business.py`，覆盖挂号、接诊、病历、检查/检验/处置、处方、收费、发药、退药、诊断确认、退号。
- 独立业务验收结果为 `status=success`，处方最终状态 `REFUNDED`，金额保留 `37.00`，药品库存恢复为 `100`。

## 2026-06-25 真实业务流程复验

本次按“真实业务流程”重新执行端到端验收，覆盖服务健康、Project2 独立业务、头颅 CT AI 链路、报告审核/EMR 同步、前端类型检查与生产构建。

### 1. 服务健康检查

执行命令：

```powershell
.\scripts\check_headct_platform.ps1
```

结果：

```text
Filter          ok  http://127.0.0.1:8000/api/ct-artifact/health
Orchestrator    ok  http://127.0.0.1:8010/api/head-ct-ai/health
LesionDetection ok  http://127.0.0.1:8021/api/head-ct-lesion/health
ReportService   ok  http://127.0.0.1:8030/api/v1/health
EMRService      ok  http://127.0.0.1:8040/api/v1/health
```

Project2 额外通过 `http://127.0.0.1:8092/actuator/health` 验证，状态为 `UP`，数据库连接为 `UP`。

### 2. Project2 独立核心业务

执行命令：

```powershell
python scripts\e2e_project2_core_business.py
```

结果为 `status=success`，本次真实落库业务数据摘要：

```json
{
  "register_id": 28,
  "cancel_register_id": 29,
  "prescription_id": 8,
  "doctor_list_count": 1,
  "waiting_patient_count": 1,
  "orders_count": 3,
  "check_result_sections": {
    "checks": 1,
    "inspections": 1,
    "disposals": 1
  },
  "prescription_status": "REFUNDED",
  "drug_stock": 100
}
```

同时验证三端 dashboard 数据可由后端返回：

```json
{
  "admin": {
    "todayRegistrations": 3,
    "activePatients": 8,
    "pendingChargeAmount": 3080.0,
    "pendingReportCount": 7
  },
  "doctor": {
    "doctorId": 19,
    "finishedToday": 1,
    "pendingCheckCount": 1
  },
  "patient": {
    "patientId": 22,
    "recordCount": 1,
    "unpaidOrderCount": 2,
    "latestVisitState": "DIAGNOSIS_DONE"
  }
}
```

### 3. Project2 -> AI 子系统 -> 报告 -> EMR 全链路

执行命令：

```powershell
python scripts\e2e_project2_real_business.py
```

结果为 `status=success`，本次真实业务链路摘要：

```json
{
  "patient_id": 24,
  "register_id": 30,
  "medical_record_id": 16,
  "check_request_id": 17,
  "consultation_id": 8,
  "consultation_recommendation_count": 2,
  "diagnosis_suggestion_count": 1,
  "image_file_id": 9,
  "analysis_id": 9,
  "analysis_confidence": 0.4617331326007843,
  "report_id": 8,
  "project2_report_status": "draft",
  "report_service_status": "released",
  "report_version_after_review": 2,
  "emr_document_id": "DR-EDD0E251F59949DB930F13369F707846",
  "emr_status": "final",
  "persisted": {
    "ai_consultation": 1,
    "ai_diagnosis_suggestion": 1,
    "ai_image_analysis": 1,
    "ai_generated_report": 1
  }
}
```

说明：

- AI 问诊和 AI 辅助诊断通过 Project2 API 入口触发。
- 影像分析通过 Orchestrator 编排 Filter、Lesion、RAG/LLM 服务。
- 报告服务完成医生复核、审核、签名、发布。
- EMR 服务收到最终报告，状态为 `final`。
- Project2 本地库中 AI 问诊、诊断建议、影像分析、AI 报告均有持久化记录。

### 4. 后端与前端构建验证

三端登录入口：

```powershell
POST http://127.0.0.1:8092/api/auth/login
```

结果：

```json
{
  "doctorRole": "DOCTOR",
  "doctorHasToken": true,
  "doctorId": 17,
  "adminRole": "ADMIN",
  "adminHasToken": true,
  "adminId": 18,
  "patientRole": "PATIENT",
  "patientHasToken": true,
  "patientId": 22
}
```

说明：医生、管理员、患者均使用统一登录入口 `/api/auth/login`，通过 `loginType` 区分角色；登录成功后由 JWT 与角色信息决定前端进入医生端、管理员端或患者端。

后端测试：

```powershell
cd Project2
$env:MAVEN_USER_HOME='D:\exam\.maven'
.\mvnw.cmd "-Dmaven.repo.local=D:\exam\.m2\repository" -q test
```

结果：通过。

前端类型检查：

```powershell
cd frontend
npm run type-check
```

结果：通过。

前端生产构建：

```powershell
cd frontend
npm run build
```

结果：通过。构建中存在 Vite chunk size warning 与第三方依赖注释 warning，不影响构建产物生成。

### 5. 本次复验结论

截至 2026-06-25，本地环境中主平台与头部 CT AI 子系统的真实业务链路可以视作已打通：

- 服务层：Filter、Orchestrator、LesionDetection、ReportService、EMRService、Project2 均可用。
- 主平台业务层：挂号、接诊、病历、检查/检验/处置、收费、药房、退号、三端 dashboard 均通过脚本验证。
- AI 链路层：问诊、辅助诊断、CT 上传、影像分析、报告草稿、医生审核、EMR 分发均通过真实 API 验证。
- 前端交付层：TypeScript 类型检查与生产构建通过，三端页面所需 dashboard/API 数据已由后端提供。

遗留说明：

- 本次未使用内置浏览器做逐按钮 UI 自动化，因为当前 Codex 浏览器插件技能文件在本机环境缺失；已通过前端生产构建、类型检查与后端真实 API 验证覆盖主要交付风险。
- 影像病灶模型仍使用当前项目配置的可运行模型链路；若后续替换为真实训练 checkpoint，需要重复执行本记录中的两条 e2e 命令复验。

## 2026-06-25 doctor/admin 登录问题复验

### 问题定位

doctor/admin 登录失败并非 Project2 认证接口不可用，而是用户从患者登录页输入员工账号时，前端按 `loginType=PATIENT` 提交，导致后端进入患者登录分支。此前缺少全局业务异常处理，业务异常显示为 HTTP 500。

### 修复摘要

- 患者登录页密码登录增加账号角色推断：
  - `doctor` -> `DOCTOR`
  - `admin` -> `ADMIN`
  - 其他账号 -> `PATIENT`
- 登录成功后按 `roleType` 跳转对应三端首页。
- Project2 增加 `GlobalExceptionHandler`，业务异常不再冒泡成未处理 500。

### 复验结果

```text
doctor 直连登录 8092: 200, roleType=DOCTOR
doctor Vite 代理登录 5173: 200, roleType=DOCTOR
admin Vite 代理登录 5173: 200, roleType=ADMIN
doctor + PATIENT 错角色登录: 400, 不再是 500
```

真实业务链路：

```text
scripts/e2e_project2_core_business.py -> success
scripts/e2e_project2_real_business.py -> success
scripts/smoke_test_headct_platform.py -> success
```

前端：

```text
npm run type-check -> passed
npm run build-only -> passed
```

结论：三端登录、Project2 独立业务、Project2 + 头部 CT AI 子系统链路均已按当前本地环境复验通过。

## 2026-06-26 成熟权重链路复验

### 修正目标

本次针对真实业务场景继续收紧两个判断：

- VinBigData `best_resnet50.pth` 不能因为本地适配器架构不兼容而静默 fallback。
- InDuDoNet `InDuDoNet_latest.pt` 不能仅因 checkpoint 存在就标记为已执行图像校正。

### 代码与契约调整

- `HeadCTLesionDetection` 新增 VinBigData 原始 `baseline_resnet50` 适配器，直接识别并加载 `layer0..layer4 + decoder.recurrent + decoder.fc` 权重结构。
- `Filter` 的 `artifact_reduction` 契约新增 `registered`、`executable`、`execution_blockers` 字段。
- InDuDoNet 当前状态固定为“已登记但不可执行”，直到官方网络源码、ODL/Astra 投影算子、sinogram/metal_trace/LI 输入链路补齐。

### 验证命令

```powershell
python scripts\validate_true_checkpoints.py --strict-mature
python -m pytest Filter\Fastapi\tests\test_ct_artifact_api.py HeadCTLesionDetection\tests\test_lesion_contract.py HeadCTOrchestrator\tests\test_orchestrator_pipeline.py -q
.\scripts\start_headct_platform.ps1 -Restart
python scripts\smoke_test_headct_platform.py
python scripts\e2e_project2_real_business.py
```

### 验证结果

```text
validate_true_checkpoints.py --strict-mature -> selected VinBigData raw mature checkpoint, selected InDuDoNet MAR checkpoint
pytest Filter/Lesion/Orchestrator -> 23 passed
smoke_test_headct_platform.py -> success
e2e_project2_real_business.py -> success
```

服务健康：

```text
Filter           ok
LesionDetection  ok
Orchestrator     ok
EMRService       ok
ReportService    ok
Project2         UP
```

stderr 日志大小复查：

```text
filter.stderr.log          202 bytes
lesion.stderr.log          202 bytes
orchestrator.stderr.log    202 bytes
emr.stderr.log             202 bytes
report.stderr.log          202 bytes
project2.stderr.log          0 bytes
```

### 真实链路证据

Head CT smoke：

```json
{
  "task_id": "c8d9e0a5eade48da9825ab181b6a9531",
  "orchestrator_status": "success",
  "filter_backend": "unet3d",
  "lesion_status": "success",
  "rag_status": "success",
  "llm_status": "success",
  "report_id": "8c7951a1-e8b2-4df5-ad77-86664d5e47ee",
  "report_status": "released",
  "report_version": 2,
  "emr_document_id": "DR-161374079D0E438B9136C9FECF089615",
  "emr_status": "final"
}
```

Project2 真实业务链路：

```json
{
  "status": "success",
  "patient_id": 44,
  "register_id": 50,
  "medical_record_id": 29,
  "check_request_id": 30,
  "consultation_id": 17,
  "analysis_id": 16,
  "analysis_confidence": 0.06743263453245163,
  "report_service_status": "released",
  "report_version_after_review": 2,
  "emr_document_id": "DR-0B63F5C8FE3E4BFBB19594CDF797DEC8",
  "emr_status": "final",
  "persisted": {
    "ai_consultation": 1,
    "ai_diagnosis_suggestion": 1,
    "ai_image_analysis": 1,
    "ai_generated_report": 1
  }
}
```

Orchestrator 结果关键字段：

```text
quality_control.artifact_reduction.registered=true
quality_control.artifact_reduction.executable=false
quality_control.artifact_reduction.correction_status=checkpoint_registered_not_executable
quality_control.lesion_input_policy.used_input=original_ct
quality_control.lesion_input_policy.corrected_ct_used=false
lesion_analysis.results[0].provider=vinbigdata
lesion_analysis.results[0].checkpoint_framework=state_dict
lesion_analysis.results[0].checkpoint_fallback_used=false
```

### 结论

当前链路已符合“真实业务安全”口径：

- 颅内出血分类实际使用 VinBigData raw mature checkpoint，不再因架构不兼容进入本地 fallback。
- 金属伪影识别仍由当前 U-Net3D 分割模型执行。
- InDuDoNet 仅登记为成熟 MAR checkpoint，尚未执行校正；病灶识别明确使用原始 CT，不伪造 corrected CT。
## 2026-06-26 五角色端补齐后验收

### 服务状态

已通过 `scripts/start_headct_platform.ps1 -Restart` 重启并确认：

```text
Filter           ok
LesionDetection  ok
Orchestrator     ok
EMRService       ok
ReportService    ok
Project2         UP
```

### 新增验收范围

- 医技人员端：待执行任务查询、执行、报告录入、AI 解读。
- 药房端：库存列表、入库、盘点、低库存预警、库存流水、处方发药、处方退药。
- 管理员端：正式号源新增、改号源、停诊、恢复。
- 员工认证：医生、管理员、医技、药师四类登录；错配角色拒绝。
- 前端映射：后端新增业务接口均有前端 API 封装和页面入口。

### 验收命令与结果

```text
python scripts/check_project2_frontend_business_mapping.py
Project2 frontend business mapping check passed.

npm run type-check
exit 0

npm run build-only
exit 0

mvn -Dtest=AuthServiceImplBehaviorTest test
exit 0

python scripts/e2e_project2_core_business.py
status=success

python scripts/e2e_project2_extended_business.py
status=success

python scripts/e2e_project2_real_business.py
status=success

python scripts/smoke_test_headct_platform.py
orchestrator_status=success
report_status=released
emr_status=final
```

### 登录验收

```text
doctor / 123456 / DOCTOR -> token ok
admin / 123456 / ADMIN -> token ok
medicaltech / 123456 / MEDICAL_TECH -> token ok
pharmacist / 123456 / PHARMACIST -> token ok
doctor / 123456 / PHARMACIST -> rejected
```

### 结论

主平台与头部 CT AI 子系统的业务链路仍保持通过；本次补齐后，医技、药房、号源三个此前“后端有、前端缺”的模块已经具备可操作页面。AI 影像识别链路可用于演示和医生审核前辅助，不作为无人工审核的临床生产诊断。
## 2026-06-26 Playwright 自动截图级视觉验收

### 接入内容

- 前端新增 `@playwright/test`，通过系统 Chrome 运行，不下载 Playwright 浏览器包。
- 新增配置：`frontend/playwright.config.ts`。
- 新增视觉验收用例：`frontend/tests/visual/project2-visual.spec.ts`。
- 新增命令：

```powershell
cd D:\exam\frontend
npm run test:visual
```

### 覆盖范围

桌面端与移动端各覆盖 5 个核心页面：

- 患者端：`/patient/profile`
- 医生端：`/doctor`
- 管理员端：`/admin/schedule-sources`
- 医技端：`/medical-tech`
- 药房端：`/drugstore`

### 截图产物

截图输出目录：

```text
D:\exam\frontend\visual-results
```

本次生成：

```text
desktop-chrome-patient-profile.png
desktop-chrome-doctor-dashboard.png
desktop-chrome-admin-schedule-sources.png
desktop-chrome-medical-tech-workbench.png
desktop-chrome-drugstore-workbench.png
mobile-chrome-patient-profile.png
mobile-chrome-doctor-dashboard.png
mobile-chrome-admin-schedule-sources.png
mobile-chrome-medical-tech-workbench.png
mobile-chrome-drugstore-workbench.png
```

### 验收结果

```text
npm run type-check -> passed
python scripts/check_project2_frontend_business_mapping.py -> passed
npm run test:visual -> 10 passed
npm run build-only -> passed
```

说明：`playwright.config.ts` 已关闭 video，避免额外下载 Playwright ffmpeg 到系统盘；失败时仍保留 trace 与失败截图。

## 2026-07-01 用户视角全局逻辑验收扩展

### 本次目标

本次不再只验证接口能返回成功，而是从真实用户视角检查同一业务在多角色、多页面、多模块之间是否一致：

- 患者：挂号、就诊记录、待缴费/已缴费/已退费订单、个人中心统计。
- 医生：待诊队列、接诊中队列、病历、检查/检验/处置/处方、确诊后病历状态。
- 管理员：收费、退费、财务流水、日结汇总。
- 医技：收费后任务可见、执行、报告录入、AI 解读、医生端结果回读。
- 药房：库存字段完整、入库、盘点、低库存预警、发药、退药、库存流水。
- 头部 CT：Project2 上传 CT、AI 分析、报告生成、报告服务审核发布、EMR 归档。
- 前端：桌面/移动核心页面截图级验收，无红色错误提示，真实 CT 流程页面可完成。

### 新增验收脚本

```text
scripts/e2e_user_logic_acceptance.py
```

该脚本会主动种子化一组真实业务数据，并断言：

- 五类登录角色均可正常登录，错配角色被拒绝。
- 患者端 `dashboard.recordCount` 与 `/api/patient/records.total` 一致。
- 患者端 `dashboard.unpaidOrderCount` 与 `/api/patient/orders?orderState=UNPAID` 一致。
- 患者端 `dashboard.unpaidAmount` 与待缴费订单金额合计一致。
- 医生接诊后患者从待诊转入接诊中。
- 检查、检验、处置、处方均进入患者订单。
- 医技执行并录入结果后，医生端检查结果可见。
- 药房库存列表必须包含药品编码、名称、规格、单位、价格、厂家、库存。
- 药品入库、盘点、发药、退药均写入库存流水。
- 处方退药后患者订单显示 `REFUNDED`。
- 财务流水必须同时包含 `CHARGE` 和 `REFUND`。
- 日结汇总必须反映收费和退费。
- 头部 CT AI 分析必须返回 `positiveProbability` 和 `subtypeProbabilities`。
- 头部 CT 病灶模型不能使用 checkpoint fallback。
- 报告服务发布后必须写入 EMR，且 EMR 状态为 `final`。

### 本次发现并修复的问题

#### 药房端退药缺少财务退费流水

现象：

- 药房端 `/api/drugstore/refund` 能恢复库存、更新处方状态。
- 但管理员财务流水中没有对应 `REFUND` 记录。
- 从用户视角看，药房退药和财务日结不一致。

修复：

- `Project2/src/main/java/com/neuedu/his/service/impl/DrugstoreServiceImpl.java`
- 在药房退药成功后写入 `finance_record`：
  - `itemType=PRESCRIPTION`
  - `recordType=REFUND`
  - `chargeMethod=REFUND`
  - `operatorName=药房退药`

### 验收结果

后端编译：

```text
cmd /c ".\mvnw.cmd -q -DskipTests -Dmaven.test.skip=true compile -Dmaven.repo.local=D:\exam\.m2\repository"
passed
```

综合用户逻辑验收：

```powershell
python -X utf8 scripts\e2e_user_logic_acceptance.py
```

关键结果：

```text
status=success
Project2=UP
Orchestrator=ok
Report=ok
EMR=ok
medical_tech_tasks_checked=3
stock_record_types=[CHECK, DISPENSE, IN, REFUND]
finance_record_types=[CHARGE, REFUND]
final_patient_record.visitState=DIAGNOSIS_DONE
headct.positive_probability=0.06768138706684113
headct.persisted_ai.ai_image_analysis=1
headct.persisted_ai.ai_generated_report=1
```

前端类型检查：

```text
npm run type-check -> passed
```

前端截图级视觉验收：

```powershell
cd D:\exam\frontend
npm run test:visual
```

结果：

```text
24 passed
4 skipped
```

覆盖说明：

- 桌面端真实 CT 流程：医生页面真实上传 CT -> AI 识别 -> 可视化输出 -> 生成报告 -> 报告服务审核/签署/发布 -> EMR 归档。
- 桌面与移动端：患者、医生、管理员、医技、药房核心页面。
- 检查项：页面无红色错误提示、无 500 响应、无登录失败/加载失败/AI 失败提示。

### 结论

当前全局验收已经从“能跑通”提升到“用户视角逻辑一致”：

- 多角色入口可用。
- 核心业务状态在患者端、医生端、管理员端、医技端、药房端之间一致。
- 头部 CT AI 结果能在医生端页面真实生成并进入报告/EMR 链路。
- 前端核心页面通过桌面和移动截图级验收。
