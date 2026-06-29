# Project2 后端功能扩充与前端映射指导

## 目标

在现有 Project2 门诊主平台与头部 CT AI 子系统已经打通的基础上，继续扩充后端能力时必须遵守一个约束：新增后端功能要么已有前端入口，要么同步补齐前端展示，避免出现“接口数量增加但业务不可见”的空扩展。

本阶段验收标准：

1. 新增后端接口可以通过 OpenAPI 暴露；
2. 新增后端接口有自动化测试覆盖；
3. 前端页面能调用并展示新增结果；
4. Project2 编译测试通过；
5. 前端类型检查与构建通过；
6. 真实业务端到端脚本仍能通过。

## 当前基线

当前前端已映射 Project2 现有 41 个 API 包装函数，主业务链路包括：

- 患者端：验证码、登录/注册、挂号、病历、缴费、AI 问诊；
- 医生端：接诊、病历、检查/检验/处置/处方、AI 辅助诊断、AI 影像分析、AI 报告；
- 管理端：AI 排班、收费/退费、药房库存/发药/退药；
- AI 子系统：Project2 统一调用 HeadCTOrchestrator 与 HeadCTReportService。

当前不足：

- 管理端首页仍为静态统计数字；
- 医生首页的接诊统计部分依赖前端临时计算；
- 患者“我的”页只显示登录信息，没有个人业务概览；
- 登录验证码目前为演示固定码，后续应落库或接 Redis；
- JWT 已能签发，但还未形成完整的认证过滤、刷新、失效与审计闭环。

## 扩充原则

### 1. 先补“可见能力”

优先扩充首页、工作台、列表页中能够直接展示的后端能力。避免先新增后台孤立接口，导致前端不可见、验收不可感知。

### 2. 保持 Project2 为主平台入口

前端仍只调用 Project2。AI、报告、EMR、RAG、病灶识别等子系统继续由 Project2 或 HeadCTOrchestrator 编排，不让前端绕过主平台直接调用多个后端。

### 3. 分阶段推进

P0：三端首页真实统计  
P1：验证码落库、登录审计、JWT 过滤与角色校验  
P2：Redis 缓存、异步任务队列、操作审计、通知中心  
P3：检查检验平台、报告平台、EMR 的正式业务闭环增强

## 本阶段 P0 实施范围

### 后端新增接口

```text
GET /api/admin/dashboard/summary
GET /api/doctor/dashboard/summary?doctorId=1
GET /api/patient/dashboard/summary?patientId=1
```

### 返回内容

管理员首页统计：

- 今日挂号数；
- 在诊患者数；
- 待收费金额；
- 库存预警药品数；
- 今日 AI 分析数；
- 待确认 AI 报告数。

医生首页统计：

- 待诊数；
- 就诊中数；
- 今日已完成数；
- 待处理检查数。

患者个人概览：

- 累计就诊记录数；
- 待缴费订单数；
- 待缴费金额；
- 最近一次就诊状态。

### 前端映射

```text
frontend/src/views/admin/AdminHome.vue
frontend/src/views/doctor/DoctorDashboard.vue
frontend/src/views/patient/Profile.vue
frontend/src/api/index.ts
```

前端展示方式：

- 管理员首页用真实统计替换静态数字；
- 医生首页顶部统计优先使用后端统计；
- 患者“我的”页新增业务概览卡片。

## 后续 P1 指导

### 验证码正式化

新增表：

```sql
CREATE TABLE auth_verification_code (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(64) NOT NULL,
    code VARCHAR(16) NOT NULL,
    code_type VARCHAR(32),
    expire_time TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    create_time TIMESTAMP DEFAULT NOW()
);
```

正式实现：

- `send-code` 写入验证码记录；
- `login-by-code` 校验最新未使用验证码；
- 校验成功后标记 `used=true`；
- 保留演示模式时，可用配置项控制是否固定 `123456`。

### 登录审计

新增表：

```sql
CREATE TABLE auth_login_audit (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    role_type VARCHAR(32),
    phone VARCHAR(64),
    login_type VARCHAR(32),
    success BOOLEAN,
    failure_reason TEXT,
    login_time TIMESTAMP DEFAULT NOW()
);
```

用途：

- 管理端显示最近登录记录；
- 安全侧统计异常验证码、失败登录；
- 后续与 Redis 限流、账号锁定衔接。

### JWT 过滤与权限校验

建议新增：

```text
JwtAuthenticationFilter
CurrentUserContext
@RequireRole 或基于 Spring Security 的角色校验
```

正式验收：

- 未登录访问受保护接口返回 401；
- 角色不符返回 403；
- 患者只能访问自己的病历、订单和报告；
- 医生只能访问自己接诊或授权患者数据。

## 后续 P2 指导

### Redis

建议用于：

- 验证码缓存；
- 登录失败限流；
- 首页统计短 TTL 缓存；
- AI 任务状态缓存；
- 幂等键与接口防重复提交。

### 异步队列

建议用于：

- AI 影像分析；
- 报告生成；
- EMR 分发；
- 短信/站内通知；
- 大文件处理。

如果暂不引入 MQ，可先用数据库任务表 + Spring 定时轮询，之后迁移到 RabbitMQ/Redis Stream。

## 验收清单

本阶段完成后必须执行：

```powershell
cd D:\exam\Project2
$env:MAVEN_USER_HOME='D:\exam\.maven'
.\mvnw.cmd "-Dmaven.repo.local=D:\exam\.m2\repository" -q test
```

```powershell
cd D:\exam\frontend
npm run type-check
npm run build
```

```powershell
cd D:\exam
python scripts\e2e_project2_core_business.py
```

若头部 CT 全链路服务已启动，再执行：

```powershell
cd D:\exam
python scripts\e2e_project2_real_business.py
```

最终要求：

- 后端接口可用；
- 前端页面能展示真实数据；
- 端到端业务脚本通过；
- 进度文档记录本阶段完成内容与剩余风险。
