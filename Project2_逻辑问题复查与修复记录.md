# Project2 逻辑问题复查与修复记录

更新时间：2026-06-25

## 本次复查目标

围绕患者端“我的”数量、缴费页列表、管理员财务页、医生开立项目之间的数据一致性，复查是否存在同类逻辑问题。

## 已修复问题

### 1. 患者缴费项目状态不一致

问题：
- 患者首页统计显示存在待缴费项目，但缴费页可能显示为空。
- 原因是前端分页参数被包装成 `query.xxx`，后端 DTO 没有正确接收。

处理：
- 前端 API wrapper 对查询类接口统一展开 `params.query`。
- 患者缴费页查询页大小调整到后端允许范围。

### 2. 收费接口只按 itemId 猜测项目类型

问题：
- 检查、检验、处方、处置可能出现相同 `itemId`。
- 原收费逻辑在未传 `itemType` 时容易串单，导致“应付金额不正确”。

处理：
- `ChargeRequestDTO`、`RefundRequestDTO` 增加 `itemTypes`。
- 收费/退费按 `itemIds + itemTypes` 精确定位项目。
- 患者缴费页和管理员财务页均传递项目类型。

### 3. 检查/检验/处置未完整纳入收费链路

问题：
- 原收费逻辑主要覆盖处方。
- 处置申请已能创建，但患者订单、待缴费统计、收费状态流转没有完整纳入。

处理：
- 检查、检验、处置统一进入患者订单。
- `DISPOSAL` 纳入收费、退费、患者待缴费统计、管理员待收费金额统计。
- 订单状态统一映射：
  - `CREATED -> UNPAID`
  - `CHARGED / PAID / DISPENSED -> PAID`
  - `REFUNDED -> REFUNDED`

### 4. 管理员收费记录和日结为空实现

问题：
- 管理员财务页即使完成真实收费，也显示“暂无收费记录”。
- 日结统计无法反映收费、退费。

处理：
- 新增正式表 `finance_record`。
- 收费、退费、退药时写入财务流水。
- `/api/admin/finance/records` 从流水表查询。
- `/api/admin/finance/daily-summary` 从流水表汇总收费笔数、退费笔数、收费金额、退费金额。

### 5. 退药缺少退费流水

问题：
- 药房退药会把处方状态更新为 `REFUNDED`，但不会产生财务退费记录。

处理：
- `drugRefund` 成功后写入 `finance_record`，`recordType=REFUND`。

### 6. 医生端开立项目存在硬编码风险

问题：
- 医生端开检查/检验/处置时，曾存在固定使用医疗技术 ID 的风险。
- 开处方时也存在固定医生 ID 的风险。

处理：
- 医疗技术 ID 使用医生实际选择的项目。
- 处方医生 ID 使用当前登录医生。

## 数据库变更

正式 schema 已补充：

```sql
CREATE TABLE IF NOT EXISTS finance_record (...);
CREATE INDEX IF NOT EXISTS idx_finance_record_create_time ON finance_record(create_time);
CREATE INDEX IF NOT EXISTS idx_finance_record_register_id ON finance_record(register_id);
```

本地 `hospital` 数据库已执行：

```powershell
$env:PGPASSWORD='<your-postgres-password>'
D:\PostgreSQL\bin\psql.exe -h localhost -p 5432 -U postgres -d hospital -v ON_ERROR_STOP=1 -f D:\exam\Project2\sql\001_project2_schema.sql
```

## 验收结果

已执行：

```powershell
cd D:\exam\Project2
$env:MAVEN_USER_HOME='D:\exam\.maven'
.\mvnw.cmd "-Dmaven.repo.local=D:\exam\.m2\repository" -q test

cd D:\exam\frontend
npm run type-check

cd D:\exam
python scripts\e2e_project2_core_business.py
```

关键结果：
- Project2 健康检查：`UP`
- 完整业务脚本：`status=success`
- 新病例患者订单：`orders_count=4`
- 患者待缴费：`unpaidOrderCount=3`
- 患者待缴费金额：`240.0`
- 检查、检验、处置、处方均能在订单中显示。
- 对同一就诊下 `CHECK / INSPECTION / DISPOSAL` 三类项目一次性缴费后：
  - `UNPAID_COUNT=0`
  - `PAID_COUNT=3`
  - `REFUNDED_COUNT=1`
- 管理员财务流水可查询到：
  - 检查收费
  - 检验收费
  - 处置收费
  - 处方收费
  - 处方退费
- 日结统计可正确返回：
  - `chargeCount`
  - `refundCount`
  - `totalAmount`
  - `refundAmount`

## 后续建议

1. 如果要进一步规范财务审计，可将收费员 ID、退费原因、支付流水号纳入 `finance_record`。
2. 如果要支持部分退费，应新增收费明细状态和可退金额校验。
3. 如果要长期维护数据库版本，建议引入 Flyway 或 Liquibase。

## 2026-06-25 追加复查：医生端、管理员端与头部 CT 链路

### 1. doctor / admin 登录失败感的根因

复查结果：
- 后端 `/api/auth/login` 对 `doctor / 123456`、`admin / 123456` 均能返回 JWT。
- 失败主要不是登录接口本身，而是演示医生账号没有稳定业务数据，医生首页进入后显示空队列，容易被判断为不可用。
- 医生队列接口原本只返回 `registerId` 和 `caseNumber`，患者姓名、性别、年龄、登记时间、状态为空，页面卡片信息不完整。

修复：
- 正式数据库 schema 增加稳定演示业务种子：
  - `doctor / 123456`
  - `admin / 123456`
  - 演示科室、挂号级别、结算类别
  - 今日医生排班
  - 一个挂到 `doctor` 名下的真实待诊患者
- `DoctorPatientListVO` 增加 `visitState`。
- `Register` 增加 `caseNumber` 扩展字段映射。
- `RegisterMapper.xml` 补充患者姓名、性别、生日、病历号等 join 字段映射。
- `DoctorServiceImpl.getPatients()` 补齐患者卡片字段。
- 医生首页按真实状态分别请求：
  - `REGISTERED`
  - `DOCTOR_RECEIVED`
  - `DIAGNOSIS_DONE`
- 员工端认证 API 统一改用项目自定义 `request` 实例。
- 员工端 401 失效后跳转 `/auth/login`，不再错误跳到患者登录页。
- 医生退出登录后跳转 `/auth/login`。

验证结果：

```text
doctor 登录：employeeId=17, roleType=DOCTOR
doctor dashboard：pendingCount=1
doctor patients：total=1，包含 patientName/gender/age/registrationTime/visitState

admin 登录：employeeId=18, roleType=ADMIN
admin dashboard：可返回今日挂号、在诊患者、待收费金额、AI 报告等统计
Vite 代理 /api/auth/login：doctor/admin 均 HTTP 200
```

### 2. Project2 独立业务链路复核

执行：

```powershell
python scripts\e2e_project2_core_business.py
```

结果：

```text
status=success
orders_count=4
check_result_sections.checks=1
check_result_sections.inspections=1
check_result_sections.disposals=1
patient.unpaidOrderCount=3
patient.unpaidAmount=240.0
prescription_status=REFUNDED
drug_stock=100
```

结论：
- 挂号、医生接诊、病历、检查、检验、处置、处方、收费、发药、退药、确诊、退号链路通过。
- 检查、检验、处置、处方四类项目均能进入患者订单。

### 3. HeadCT 五服务链路复核

执行：

```powershell
python scripts\smoke_test_headct_platform.py
```

结果：

```text
orchestrator_status=success
filter_backend=unet3d
lesion_status=success
rag_status=success
llm_status=success
report_status=released
emr_status=final
```

### 4. Project2 调 HeadCT 真实业务链路复核

执行：

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
consultation_recommendation_count=2
diagnosis_suggestion_count=2
analysis_confidence=0.4617331326007843
report_service_status=released
emr_status=final
persisted.ai_consultation=1
persisted.ai_diagnosis_suggestion=2
persisted.ai_image_analysis=1
persisted.ai_generated_report=1
```

结论：
- 主平台调用 AI 问诊、AI 辅助诊断、影像上传、头部 CT 编排、报告生成、报告服务审核发布、EMR 回写链路通过。
- 当前使用的是本地 smoke checkpoint，业务链路真实可用；模型医学效果仍取决于后续真实训练权重。

## 2026-06-25 三端登录与真实链路再复查

### 1. doctor/admin 登录失败根因

截图中的橙色登录页是患者登录页，不是员工登录页。该页面原本会把所有密码登录都按：

```json
{ "loginType": "PATIENT" }
```

提交到 `/api/auth/login`。因此在患者页手动输入 `doctor / 123456` 或 `admin / 123456` 时，后端会进入患者登录分支，查不到对应患者并抛出业务异常；由于 Project2 原先缺少全局业务异常处理器，该业务异常被前端表现为 HTTP 500。

### 2. 已完成修复

- `frontend/src/views/patient/Login.vue`
  - 患者页测试账号点击 `doctor/admin` 时不再直接跳转，而是填入账号密码。
  - 密码登录会根据账号推断 `PATIENT / DOCTOR / ADMIN`，并按后端返回的 `roleType` 跳转到 `/patient`、`/doctor` 或 `/admin`。
- `Project2/src/main/java/com/neuedu/his/advice/GlobalExceptionHandler.java`
  - 补全 `@RestControllerAdvice`。
  - `BusinessException` 统一返回对应 4xx/5xx 业务状态码，不再误报为未处理 500。
  - 校验异常返回 400，未知异常返回 500。

### 3. 本次验证结果

后端和 Vite 代理登录验证：

```text
POST http://127.0.0.1:8092/api/auth/login doctor + DOCTOR -> 200, roleType=DOCTOR
POST http://127.0.0.1:5173/api/auth/login doctor + DOCTOR -> 200, roleType=DOCTOR
POST http://127.0.0.1:5173/api/auth/login admin + ADMIN -> 200, roleType=ADMIN
POST http://127.0.0.1:8092/api/auth/login doctor + PATIENT -> 400, 不再是 500
```

三端业务接口验证：

```text
doctor dashboard: pendingCount=1
doctor patients: total=1
admin dashboard: todayRegistrations=18, pendingChargeAmount=4450.00
```

核心业务脚本：

```powershell
python scripts\e2e_project2_core_business.py
```

结果：

```text
status=success
orders_count=4
checks=1
inspections=1
disposals=1
patient.unpaidOrderCount=3
patient.unpaidAmount=240.0
```

主平台 + 头部 CT 真实业务脚本：

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
consultation_recommendation_count=2
diagnosis_suggestion_count=3
report_service_status=released
emr_status=final
persisted.ai_consultation=1
persisted.ai_diagnosis_suggestion=3
persisted.ai_image_analysis=1
persisted.ai_generated_report=1
```

头部 CT 子系统 smoke：

```powershell
python scripts\smoke_test_headct_platform.py
```

结果：

```text
orchestrator_status=success
filter_backend=unet3d
lesion_status=success
rag_status=success
llm_status=success
report_status=released
emr_status=final
```

前端验证：

```powershell
npm run type-check
npm run build-only
```

结果：均通过。`npm run build-only` 在普通沙箱下因 esbuild 子进程 `spawn EPERM` 失败，提升权限后通过；构建仅有 Vite chunk size warning，不影响产物生成。
## 2026-06-26 角色端业务映射与运行逻辑补齐

### 本次发现的逻辑问题

1. 后端已存在 `/api/medical-tech/*`，但前端没有独立医技人员端，医技执行、报告录入、AI 解读无法从页面完成。
2. 后端已存在 `/api/drugstore/*`，但前端没有独立药房端，入库、盘点、低库存预警、库存流水、发药、退药无法完整显示和操作。
3. 后端已存在 `/api/schedule/sources/*`，但前端只有 AI 排班视图，没有正式号源新增、停诊、恢复、改号源入口。
4. 员工认证只严格校验了 DOCTOR/ADMIN，MEDICAL_TECH/PHARMACIST 场景下存在 loginType 与员工 role_type 不一致仍可进入后续逻辑的风险。
5. 本地演示数据缺少稳定的 `medicaltech / 123456`、`pharmacist / 123456` 账号。

### 本次修复

- 新增前后端映射检查脚本：`scripts/check_project2_frontend_business_mapping.py`。
- 新增医技工作台：`frontend/src/views/medical-tech/MedicalTechWorkbench.vue`。
- 新增药房工作台：`frontend/src/views/drugstore/DrugstoreWorkbench.vue`。
- 新增管理员号源管理页：`frontend/src/views/admin/ScheduleSourceManage.vue`。
- 新增员工登录页：`frontend/src/views/auth/StaffRoleLogin.vue`，支持 DOCTOR、ADMIN、MEDICAL_TECH、PHARMACIST。
- 新增医技、药房布局：`MedicalTechLayout.vue`、`DrugstoreLayout.vue`。
- 管理员端切换到干净布局：`AdminBusinessLayout.vue`，加入号源入口。
- `frontend/src/api/index.ts` 补齐医技、药房、号源 API 封装。
- `AuthServiceImpl` 改为员工登录角色严格匹配。
- `Project2/sql/001_project2_schema.sql` 补齐医技和药师演示账号。
- 本地 `hospital` 数据库已执行 schema 初始化，账号已写入。

### 本次验证

```text
python scripts/check_project2_frontend_business_mapping.py -> passed
npm run type-check -> passed
npm run build-only -> passed
mvn -Dtest=AuthServiceImplBehaviorTest test -> passed
doctor/admin/medicaltech/pharmacist 登录 -> 均返回 JWT
doctor + PHARMACIST 错配登录 -> 已拒绝
python scripts/e2e_project2_core_business.py -> success
python scripts/e2e_project2_extended_business.py -> success
python scripts/e2e_project2_real_business.py -> success
python scripts/smoke_test_headct_platform.py -> success
```

### 当前结论

Project2 独立业务、头部 CT AI 链路、医技执行闭环、药房库存闭环、科室医生号源管理均已有后端接口和前端入口。AI 影像识别仍定位为医生审核前辅助能力，不等同于临床生产级自动诊断。
