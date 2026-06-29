# Project2 独立业务功能验收进度记录

更新时间：2026-06-22

## 本阶段结论

在主平台与头部 CT AI 子系统衔接已经完成的基础上，本阶段单独验证了 Project2 主平台自身业务功能。

本次验收不依赖头部 CT AI 分析链路，重点覆盖门诊主业务：

```text
排班/医生列表
-> 患者挂号
-> 医生接诊
-> 病历保存
-> 检查/检验/处置申请
-> 开立处方
-> 患者订单查询
-> 收费
-> 药房发药
-> 退药
-> 诊断确认
-> 无医嘱挂号退号
```

验收结果：通过。

## 已完成改动

### 1. 新增医生接诊 API

文件：

```text
Project2/src/main/java/com/neuedu/his/controller/DoctorController.java
Project2/src/main/java/com/neuedu/his/service/DoctorService.java
Project2/src/main/java/com/neuedu/his/service/impl/DoctorServiceImpl.java
```

新增接口：

```http
PUT /api/doctor/patients/{registerId}/receive
```

用途：

- 将挂号记录从 `REGISTERED` 推进到 `DOCTOR_RECEIVED`。
- 解决原有业务断点：挂号后医生无法通过 API 正式进入病历、检查、处方流程。
- 接口幂等：若已经是 `DOCTOR_RECEIVED`，重复调用不会破坏状态。

### 2. 修正挂号 DTO 性别校验

文件：

```text
Project2/src/main/java/com/neuedu/his/model/dto/PatientRegisterRequestDTO.java
```

完成内容：

- 修复原文件中乱码导致的性别正则不可用问题。
- 支持 `男/女/M/F`。
- 恢复关键校验提示为正常中文。

### 3. 修正处方状态更新时金额丢失

文件：

```text
Project2/src/main/resources/mapper/PrescriptionMapper.xml
```

修复前：

```sql
total_amount = #{totalAmount}
```

在收费、退费、退药等只更新状态的场景中，`totalAmount = null` 会导致处方金额被清空。

修复后：

```sql
total_amount = COALESCE(#{totalAmount}, total_amount)
```

结果：

- 创建处方后金额为 `37.00`。
- 收费、发药、退药后金额仍保留 `37.00`。

### 4. 新增独立业务验收脚本

文件：

```text
scripts/e2e_project2_core_business.py
```

脚本能力：

- 校验 Project2 主业务数据库 schema 是否已初始化。
- 自动准备本次验收所需的业务种子数据。
- 自动校准 PostgreSQL sequence，避免开发库手工导入后自增序列落后。
- 通过真实 Project2 HTTP API 完成完整门诊业务流程。
- 通过数据库核对最终状态和落库结果。

运行命令：

```powershell
python scripts\e2e_project2_core_business.py
```

### 5. 补全正式数据库初始化脚本

新增文件：

```text
Project2/sql/001_project2_schema.sql
Project2/sql/init_project2_db.ps1
```

完成内容：

- 将 Project2 主平台所需表结构从验收脚本中移出。
- 正式纳入 24 张核心表：
  - 主数据：`department`、`employee`、`regist_level`、`settle_category`、`scheduling`
  - 患者就诊：`patient`、`register`、`medical_record`、`medical_record_disease`、`disease`
  - 医技医嘱：`medical_technology`、`check_request`、`inspection_request`、`disposal_request`
  - 药房处方：`drug_info`、`prescription`、`prescription_detail`
  - AI 业务：`ai_consultation`、`ai_diagnosis_suggestion`、`ai_image_file`、`ai_image_analysis`、`ai_generated_report`、`ai_schedule_rule`、`ai_schedule_result`
- 本地 `hospital` 数据库已执行初始化脚本并确认 24 张表均存在。

初始化命令：

```powershell
$env:PGPASSWORD='你的 PostgreSQL 密码'
powershell -ExecutionPolicy Bypass -File .\Project2\sql\init_project2_db.ps1
```

## 本次验收结果

执行结果：

```json
{
  "status": "success",
  "health": "UP",
  "register_id": 11,
  "cancel_register_id": 12,
  "prescription_id": 2,
  "doctor_list_count": 1,
  "waiting_patient_count": 1,
  "orders_count": 3,
  "check_result_sections": {
    "checks": 1,
    "inspections": 1,
    "disposals": 1
  },
  "db_summary": {
    "register": {
      "patient_id": 5,
      "visit_state": "DIAGNOSIS_DONE"
    },
    "medical_record_count": 1,
    "check_count": 1,
    "inspection_count": 1,
    "disposal_count": 1,
    "prescription": {
      "prescription_status": "REFUNDED",
      "total_amount": "37.00"
    },
    "drug_stock": 100
  }
}
```

验收结论：

- Project2 服务健康状态为 `UP`。
- 挂号 API 可用。
- 医生列表、候诊队列可用。
- 医生接诊、保存病历、开检查、开检验、开处置、开处方可用。
- 患者订单查询可返回 3 类医嘱。
- 收费、发药、退药可用。
- 退药后库存恢复到初始值 `100`。
- 诊断确认后挂号状态进入 `DIAGNOSIS_DONE`。
- 无医嘱挂号退号可用。

## 当前边界

当前已不再依赖验收脚本兜底建表。正式建表入口为：

```text
Project2/sql/001_project2_schema.sql
Project2/sql/init_project2_db.ps1
```

验收脚本只负责检查 schema 是否存在、准备本次业务验收数据并执行 API 流程。

## 后续建议

1. 将 `scripts/e2e_project2_core_business.py` 和 `scripts/e2e_project2_real_business.py` 作为主平台验收双脚本：
   - `e2e_project2_core_business.py`：验证 Project2 独立业务。
   - `e2e_project2_real_business.py`：验证 Project2 + 头部 CT AI + 报告 + EMR 全链路。
2. 后续如需要更规范的版本管理，可继续引入 Flyway 或 Liquibase。
3. 继续补齐收费流水、退费流水、发药流水等正式财务/药房审计表。

## 2026-06-26 医技、药房库存、排班号源补强验收

### 本阶段目标

参考 `p2.png` 中医技人员、药房管理员、管理员排班号源三类角色，将原先偏薄的模块补强为独立业务模块：

- 医技人员：查看已收费任务、执行检查/检验/处置、录入报告、AI 解读。
- 药房库存：库存查询、入库、盘点、低库存预警、库存流水、发药、退药。
- 排班号源：创建正式号源、调整号源、停诊、恢复、查询号源。

指导文档：

```text
Project2_医技药房排班号源真实业务补强指导.md
```

### 数据库补强

新增正式库存流水表：

```text
drug_stock_record
```

本地 `hospital` 数据库已执行建表，正式 SQL 已同步到：

```text
Project2/sql/001_project2_schema.sql
```

### 新增接口

医技工作台：

```http
GET  /api/medical-tech/tasks
POST /api/medical-tech/tasks/{itemType}/{itemId}/execute
POST /api/medical-tech/tasks/{itemType}/{itemId}/report
POST /api/medical-tech/tasks/{itemType}/{itemId}/ai-interpret
```

药房库存：

```http
GET  /api/drugstore/inventory
POST /api/drugstore/stock/in
POST /api/drugstore/stock/check
GET  /api/drugstore/stock/alerts
GET  /api/drugstore/stock/records
POST /api/drugstore/dispense
POST /api/drugstore/refund
```

排班号源：

```http
GET  /api/schedule/sources
POST /api/schedule/sources
PUT  /api/schedule/sources/{scheduleId}/quota
PUT  /api/schedule/sources/{scheduleId}/suspend
PUT  /api/schedule/sources/{scheduleId}/resume
```

### 关键业务修正

修正处方与库存扣减时机：

```text
开方：只校验库存，不扣库存
收费：只改变收费状态
发药：扣减库存并写 DISPENSE 流水
退药：回补库存并写 REFUND 流水
```

这样避免“医生开方扣一次、药房发药再扣一次”的双扣库存问题。

### TDD 红灯

新增验收脚本后先运行：

```powershell
python scripts\e2e_project2_extended_business.py
```

初始失败：

```text
Project2 schema missing tables: drug_stock_record
```

说明测试确实覆盖了尚未实现的正式库存流水能力。

### 最终验收

编译与单元测试：

```powershell
cd Project2
$env:MAVEN_USER_HOME='D:\exam\.maven'
.\mvnw.cmd "-Dmaven.repo.local=D:\exam\.m2\repository" -q test
```

结果：通过。

扩展业务验收：

```powershell
python scripts\e2e_project2_extended_business.py
```

结果：

```json
{
  "status": "success",
  "register_id": 52,
  "schedule_id": 20,
  "medical_tech": {
    "check_id": 32,
    "inspection_id": 16,
    "disposal_id": 16
  },
  "stock": {
    "stock": 25,
    "records": [
      {"record_type": "IN", "quantity": 20, "before_stock": 8, "after_stock": 28},
      {"record_type": "CHECK", "quantity": 3, "before_stock": 28, "after_stock": 25},
      {"record_type": "DISPENSE", "quantity": 2, "before_stock": 25, "after_stock": 23},
      {"record_type": "REFUND", "quantity": 2, "before_stock": 23, "after_stock": 25}
    ]
  }
}
```

旧核心业务回归：

```powershell
python scripts\e2e_project2_core_business.py
```

结果：`status=success`，处方最终状态 `REFUNDED`，药品库存恢复为 `100`。

Project2 + 头部 CT AI 全链路回归：

```powershell
python scripts\e2e_project2_real_business.py
python scripts\smoke_test_headct_platform.py
```

结果：均通过。

### 当前结论

截至本次验收，`p2.png` 中此前偏薄的医技人员、药房库存管理、科室医生排班号源三块，已具备独立 API、正式数据表、状态流转、库存流水和端到端验收脚本。当前可视作符合本地真实业务场景的后端实现。
