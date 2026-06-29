# Project2 后端功能扩充与前端映射验收记录

## 本阶段完成内容

本阶段按照 `Project2_后端功能扩充与前端映射指导.md` 的 P0 范围完成三端首页真实统计接入，目标是让新增后端能力能被前端页面直接显示，而不是只增加孤立接口。

## 后端新增接口

```text
GET /api/admin/dashboard/summary
GET /api/doctor/dashboard/summary?doctorId={doctorId}
GET /api/patient/dashboard/summary?patientId={patientId}
```

## 后端新增文件

```text
Project2/src/main/java/com/neuedu/his/model/vo/AdminDashboardSummaryVO.java
Project2/src/main/java/com/neuedu/his/model/vo/DoctorDashboardSummaryVO.java
Project2/src/main/java/com/neuedu/his/model/vo/PatientDashboardSummaryVO.java
Project2/src/main/java/com/neuedu/his/service/DashboardService.java
Project2/src/main/java/com/neuedu/his/service/impl/DashboardServiceImpl.java
Project2/src/main/java/com/neuedu/his/mapper/DashboardMapper.java
Project2/src/test/java/com/neuedu/his/controller/DashboardContractTest.java
```

## 后端修改文件

```text
Project2/src/main/java/com/neuedu/his/controller/AdminController.java
Project2/src/main/java/com/neuedu/his/controller/DoctorController.java
Project2/src/main/java/com/neuedu/his/controller/PatientController.java
Project2/src/main/java/com/neuedu/his/model/vo/LoginResponseVO.java
```

其中 `LoginResponseVO` 显式补全 getter/setter，避免 IDEA 或 Maven 在不同 Lombok 注解处理状态下出现 `setRealName`、`setRealname` 识别不一致。

## 前端映射

新增 API 包装：

```text
frontend/src/api/index.ts
```

新增前端展示：

```text
frontend/src/views/admin/AdminHome.vue
frontend/src/views/doctor/DoctorDashboard.vue
frontend/src/views/patient/Profile.vue
```

展示内容：

- 管理员首页：今日挂号、待收费金额、库存预警、在诊患者、今日 AI 分析、待确认报告；
- 医生首页：待诊、就诊中、今日已接诊、待处理检查；
- 患者我的页：就诊记录、待缴费、待缴金额、最近就诊状态。

## 端到端脚本更新

```text
scripts/e2e_project2_core_business.py
```

新增校验：

- 管理员 dashboard 今日挂号数大于 0；
- 医生 dashboard 返回的 doctorId 与本轮种子医生一致；
- 患者 dashboard recordCount 大于 0；
- 脚本输出 dashboard 三端统计快照。

## 已完成验证

```powershell
cd D:\exam\Project2
$env:MAVEN_USER_HOME='D:\exam\.maven'
.\mvnw.cmd "-Dmaven.repo.local=D:\exam\.m2\repository" -q test
```

结果：通过。

```powershell
cd D:\exam\frontend
npm run type-check
```

结果：通过。

```powershell
cd D:\exam\frontend
npm run build
```

结果：非沙箱环境通过。沙箱环境曾出现 `spawn EPERM`，与此前记录一致，不是代码编译错误。

```powershell
cd D:\exam
python scripts\e2e_project2_core_business.py
```

结果：通过，输出 `status=success`，并返回三端 dashboard 真实统计。

## 本阶段结论

本阶段新增后端功能已同步映射到前端，并通过后端契约测试、前端类型检查、前端生产构建和 Project2 核心业务端到端脚本验证。

## 后续建议

下一阶段进入 P1：

1. 验证码从固定演示码升级为数据库或 Redis 存储；
2. 登录审计落库并在管理端显示最近登录/异常登录；
3. JWT 过滤器与角色权限校验；
4. 患者数据按登录身份隔离，避免 `/api/patient/list` 暴露全量患者；
5. 首页统计增加短 TTL 缓存，降低高频访问数据库压力。
