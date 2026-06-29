# 智慧云脑诊疗平台主平台后端

`Project2` 是智慧云脑诊疗平台的 Spring Boot 主平台后端，负责门诊、患者、医生、药房、收费和主平台 AI 入口。

完整整理与下一步整合建议见：

```text
../Project2_主平台整理与AI子系统整合指导.md
```

## 技术栈

- Java 17
- Spring Boot 3.4.7
- Spring Web
- MyBatis
- PostgreSQL
- PageHelper
- Lombok
- Jakarta Validation / Hibernate Validator
- JWT
- Spring Boot Actuator
- SpringDoc OpenAPI

## 当前模块

- 患者端：挂号、退号、缴费项目、病历查看
- 医生端：待诊列表、病历保存、检查/检验/处置/处方、门诊确诊
- 管理端：收费、费用记录、日结、药品库存、发药、退药
- AI 入口：AI 问诊、AI 辅助诊断、AI 影像上传/分析、AI 检查报告、AI 排班

## 启动

按照项目约束，`.java` 文件运行和调试使用本机 IDEA 环境。

入口类：

```text
src/main/java/com/neuedu/his/HisApplication.java
```

默认端口：

```text
http://localhost:8092
```

健康检查：

```text
http://localhost:8092/actuator/health
```

接口文档：

```text
http://localhost:8092/swagger-ui/index.html
```

## AI 子系统整合方向

主平台业务代码建议只直接调用：

```text
HeadCTOrchestrator     http://127.0.0.1:8010
HeadCTReportService    http://127.0.0.1:8030
```

最小闭环：

```text
开检查申请 -> 上传 CT -> AI 分析 -> 生成报告草稿
```

下一步优先改造：

- `ImageServiceRealImpl`
- `ReportServiceRealImpl`
- `application.yml` 中 AI 配置
- `api-test.http` 中 AI/药房/门诊端口
