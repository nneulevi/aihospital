# Project2 全界面视觉与逻辑验收记录

更新时间：2026-06-27

## 1. 本轮目标

对 Project2 主平台、头部 CT AI 子系统、报告/EMR 服务和前端界面进行整体回归，验收重点如下：

- 截图级视觉验收：每个主要界面无红色错误提示，无 5xx/400 运行错误，跳转逻辑正确，桌面端和移动端均可展示。
- 逻辑验收：患者、医生、管理员、医技、药房等界面数据与后端业务数据一致。
- 头部 CT 流程：上传/分析/报告/EMR 链路合理，能给出稳定结构化结果与可视化输出入口。
- 修复发现的问题，并保留可复跑的证据。

## 2. 本轮发现并修复的问题

### 2.1 药房工作台分页参数不一致

问题表现：

- 视觉验收进入药房工作台时，前端请求库存/流水/预警接口返回 400。
- 后端 `PageQueryDTO` 限制 `pageSize <= 50`，而前端药房页面请求 `pageSize=100`。

修复内容：

- 将 `frontend/src/views/drugstore/DrugstoreWorkbench.vue` 中库存、库存流水、库存预警查询的 `pageSize` 统一调整为 `50`。
- 重新执行前端构建和截图级视觉验收，确认药房页面不再出现红色错误提示或 400 响应。

### 2.2 头部 CT 流程截图缺少真实业务节点

问题表现：

- 原有截图只覆盖页面路由，没有真实展示“上传 CT 图像、病灶识别、AI 辅助结论、报告发布、EMR 归档”。

修复内容：

- 新增 `frontend/tests/visual/headct-workflow-screenshots.spec.ts`。
- 该用例先执行正常业务 E2E，再进入医生接诊页真实上传 CT、触发 AI 识别、生成报告，并通过 ReportService/EMRService 真实 API 渲染发布和归档证据。

### 2.3 医生接诊页上传影像后 imageFileId 解析不稳

问题表现：

- 上传接口返回对象时，前端可能把对象直接转成 `[object Object]`，导致后续 AI 识别拿不到正确影像文件 ID。

修复内容：

- `frontend/src/views/doctor/PatientVisit.vue` 上传成功后优先读取 `imageFileId/id`，字符串返回时再尝试 JSON 解析。

### 2.4 同一检查申请重复分析/生成报告导致后端 500

问题表现：

- 同一检查申请多次 AI 影像分析后，Project2 查询 `ai_image_analysis` 使用单行查询但 SQL 返回多行，触发 MyBatis `selectOne()` 异常。
- 同一检查单重复生成报告时，HeadCTReportService 插入第二份主报告，触发 `medical_reports_examination_order_id_key` 唯一约束异常。

修复内容：

- `AiImageAnalysisMapper.selectByCheckRequestId` 改为按 `analysis_time DESC, id DESC LIMIT 1` 获取最新分析。
- `AiGeneratedReportMapper.selectByRequestId` 改为按 `generation_time DESC, id DESC LIMIT 1` 获取最新报告。
- `HeadCTReportService/repositories/report_repository.py` 在检查单已有主报告时返回已有报告，避免重复插入导致 500。

## 3. 服务状态证据

启动脚本：

```powershell
.\scripts\start_headct_platform.ps1
```

端口监听结果：

```text
127.0.0.1:8000  Filter 金属伪影服务
127.0.0.1:8010  HeadCTOrchestrator
127.0.0.1:8021  HeadCTLesionDetection
127.0.0.1:8030  HeadCTReportService
127.0.0.1:8040  HeadCTEMRService
0.0.0.0:8092    Project2 主平台
```

## 4. 逻辑验收证据

### 4.1 Project2 核心业务链路

命令：

```powershell
python scripts\e2e_project2_core_business.py
```

结果：通过。

关键证据：

- 挂号、退号、医生接诊、病历、检查、检验、处置、处方、缴费/退费链路完成。
- 医生端、患者端、管理员端 dashboard 数据能够回读。
- 患者端就诊记录、待缴费数量和订单金额与后端数据一致。

### 4.2 医技、药房、排班号源扩展业务

命令：

```powershell
python scripts\e2e_project2_extended_business.py
```

结果：通过。

关键证据：

- 科室排班、号源生成、医技检查/检验/处置、药品入库、审核、发药、退药链路完成。
- 药品库存流水包含入库、审核、发药、退药记录，库存前后数量连续一致。

### 4.3 头部 CT AI 正常业务链路

命令：

```powershell
python scripts\e2e_project2_real_business.py
```

结果：通过。

关键证据：

- 由 Project2 主平台创建真实门诊头颅 CT 业务上下文。
- 通过 Project2 调用 AI 问诊、AI 辅助诊断、CT 影像上传、AI 影像分析和 AI 报告生成。
- Project2 调用 HeadCTOrchestrator 编排 Filter、Lesion、RAG/LLM。
- Project2 调用 HeadCTReportService 创建报告草稿，并继续完成医生修改、提交审核、审核通过、签名、发布。
- HeadCTReportService 调用 HeadCTEMRService 完成 EMR 归档。
- 本轮输出：`report_service_status=released`，`emr_status=final`。
- 持久化记录：`ai_consultation=1`，`ai_diagnosis_suggestion=3`，`ai_image_analysis=1`，`ai_generated_report=1`。

### 4.4 Project2 真实业务链路联调结果

命令：

```powershell
python scripts\e2e_project2_real_business.py
```

结果：通过。

关键证据：

- AI 问诊、AI 辅助诊断、AI 影像分析、AI 报告生成、报告审核、报告服务发布、EMR 归档链路完成。
- 持久化记录包含 `ai_consultation`、`ai_diagnosis_suggestion`、`ai_image_analysis`、`ai_generated_report`。
- Project2、Orchestrator、Report、EMR 健康状态均正常。

## 5. 前端视觉验收证据

### 5.1 构建

命令：

```powershell
npm run build
```

结果：通过。

说明：

- 构建成功。
- 仅存在既有 Rollup 注释告警和 chunk size 提示，不影响运行。

### 5.2 截图级视觉验收

命令：

```powershell
npm run test:visual
```

结果：通过。

关键证据：

```text
20 passed
```

覆盖视口：

- `desktop-chrome`
- `mobile-chrome`

覆盖界面：

- 登录页
- 患者端：AI 咨询、预约挂号、挂号成功、就诊记录、就诊详情、缴费订单、个人中心
- 医生端：工作台、患者接诊、个人资料
- 管理端：工作台、排班管理、号源管理、财务管理、药品管理
- 医技端：医技工作台
- 药房端：药房工作台

自动验收规则：

- 不允许出现 `.el-message--error`。
- 不允许出现 `.van-toast--fail`。
- 不允许出现 `Request failed`、`Internal Server Error`、`服务器内部错误`、`登录失败`、`加载失败` 等错误文本。
- 不允许出现页面级 `console.error`、`pageerror` 或 5xx 响应。

截图产物：

```text
frontend/visual-results
```

当前截图数量：43 张。

### 5.3 头部 CT 正常业务流程截图

命令：

```powershell
npx playwright test -c playwright.config.ts tests/visual/headct-workflow-screenshots.spec.ts --project=desktop-chrome
```

结果：通过。

关键证据：

```text
1 passed
```

截图目录：

```text
frontend/visual-results/headct-workflow
```

有效截图：

```text
desktop-chrome-01-upload-ct-image.png
desktop-chrome-02-lesion-recognition.png
desktop-chrome-03-ai-assisted-conclusion-and-report.png
desktop-chrome-04-report-released.png
desktop-chrome-05-emr-archive.png
```

覆盖节点：

- 上传 CT 图像：可见文件名、检查申请 ID、影像文件 ID、上传成功提示。
- 病灶识别：可见病灶模型 `vinbigdata_midl2020_cnn_lstm_ich`、输出类型、链路状态。
- AI 辅助结论：可见影像所见、AI 结论、置信度、报告生成结果。
- 报告发布：可见 ReportService 报告状态 `released`、报告 ID、版本、影像所见和诊断意见。
- EMR 归档：可见 EMR 状态 `final`、归档文档号和归档 JSON。

## 6. 当前结论

本轮已达到稳定可用版本要求：

- 主平台独立业务链路通过。
- 医技、药房、排班号源扩展业务链路通过。
- 头部 CT AI 链路能稳定完成项目级真实业务演示。
- 前端主要界面在桌面端和移动端均通过截图级视觉验收。
- 已修复本轮发现的药房分页参数逻辑错误。

## 7. 后续建议

- 若后续接入新的真实模型权重，应继续保持 `scripts\e2e_project2_real_business.py` 与视觉验收用例同步更新。
- 若新增前端菜单或后端接口，应同步补充 `project2-full-acceptance.spec.ts`，保证新增功能也进入截图级验收范围。
- 若面向更高并发演示，可在现有阶段 K 性能优化方案基础上继续引入 Redis 缓存和异步任务队列压测。
