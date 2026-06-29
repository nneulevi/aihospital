# Project2 医技、药房、排班号源真实业务补强指导

## 目标

参考根目录 `p2.png` 中的业务角色，将当前偏薄的三个模块补强为可以独立验收的真实业务链路：

1. 医技人员模块：医技人员可以查看已收费项目、执行检查/检验/处置、录入报告，并触发 AI 解读。
2. 药品库存管理：药房管理员可以查询库存、入库、盘点、查看低库存预警和库存流水。
3. 科室医生排班号源：管理员可以创建正式排班、调整号源、停诊、恢复，并给患者挂号使用。

## 设计原则

- 不拆已有 Project2 主结构，不影响已通过的挂号、收费、发药、AI 影像分析链路。
- 新模块必须有独立 controller/service，不再把所有操作塞进 `AdminController`。
- 所有关键状态变更必须可回查，库存变更必须有流水。
- 仍使用当前 Spring Boot + MyBatis + PostgreSQL 技术栈。
- 验收以真实 HTTP API 为准，不以 mock 或脚本临时建表兜底。

## 一、医技人员模块

### 角色

医技人员负责医生开立并已收费的检查、检验、处置项目。

### 接口

```http
GET  /api/medical-tech/tasks
POST /api/medical-tech/tasks/{itemType}/{itemId}/execute
POST /api/medical-tech/tasks/{itemType}/{itemId}/report
POST /api/medical-tech/tasks/{itemType}/{itemId}/ai-interpret
```

### 状态流转

```text
CREATED -> CHARGED -> EXECUTING -> COMPLETED
```

只有 `CHARGED` 项目允许执行，只有 `EXECUTING` 或 `COMPLETED` 项目允许录入报告。报告录入后状态为 `COMPLETED`，医生端 `GET /api/doctor/check-results/{registerId}` 能看到结果。

### 任务类型

```text
CHECK      检查
INSPECTION 检验
DISPOSAL   处置
```

## 二、药品库存管理

### 角色

药房管理员负责药品库存维护、处方发药、退药、库存预警与库存流水。

### 接口

```http
GET  /api/drugstore/inventory
POST /api/drugstore/stock/in
POST /api/drugstore/stock/check
GET  /api/drugstore/stock/alerts
GET  /api/drugstore/stock/records
POST /api/drugstore/dispense
POST /api/drugstore/refund
```

### 库存流水

新增正式表：

```text
drug_stock_record
```

流水类型：

```text
IN       入库
CHECK    盘点
DISPENSE 发药
REFUND   退药
```

发药和退药继续复用原业务规则，但药房工作台必须能独立调用，不再只能通过 `/api/admin/drug/*`。

## 三、科室医生排班号源

### 角色

管理员负责维护正式可挂号号源。AI 排班结果仍作为辅助建议，最终号源以 `scheduling` 表为准。

### 接口

```http
GET  /api/schedule/sources
POST /api/schedule/sources
PUT  /api/schedule/sources/{scheduleId}/quota
PUT  /api/schedule/sources/{scheduleId}/suspend
PUT  /api/schedule/sources/{scheduleId}/resume
```

### 状态

```text
NORMAL     正常可挂号
SUSPENDED  停诊，不可挂号
```

号源创建和调整后，患者端 `GET /api/patient/doctors` 应能看到 `NORMAL` 且有号源的医生。

## 四、验收标准

新增脚本：

```powershell
python scripts\e2e_project2_extended_business.py
```

脚本必须验证：

- 医生开立检查/检验/处置并收费后，医技人员能查询、执行、录入结果、AI 解读。
- 医生端能读取医技录入的结果。
- 药房管理员能入库、盘点、查询预警、查询库存流水。
- 药房发药/退药能改变库存并留下流水。
- 管理员能创建号源、调整号源、停诊、恢复。
- 患者端只能看到恢复后的正常号源。

## 五、完成口径

本阶段完成后，`p2.png` 中的医技人员、药房管理员、管理员排班号源三块不再只是共用接口或占位入口，而是具备独立 API、独立业务状态、可追溯数据和真实端到端验收。
