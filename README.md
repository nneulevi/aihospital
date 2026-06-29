# AI Hospital / Head CT AI Project

这是一个课程项目级的医院业务平台与头部 CT AI 辅助分析系统，包含：

- `Project2`：Spring Boot 主平台，含患者、医生、管理员、医技、药房等业务模块。
- `frontend`：Vue 前端，含 Web 端与患者小程序式移动端入口。
- `Filter`：头部 CT 金属伪影识别服务。
- `HeadCTLesionDetection`：头部 CT 病灶识别服务。
- `HeadCTOrchestrator`：头部 CT AI 编排、RAG、LLM 辅助报告服务入口。
- `HeadCTReportService`：报告审核、发布服务。
- `HeadCTEMRService`：EMR 归档服务。

## 未随仓库上传的内容

以下内容不提交到 GitHub，需要协作者按需本地准备：

- CT/DICOM/NIfTI 数据集。
- 模型权重、训练输出、`runs/`、`external_weights/`。
- `.tmp/`、`.m2/`、`.maven/`、`node_modules/`、`__pycache__/` 等缓存。
- `headct_rag_env.local.ps1`、`.env`、API Key、真实数据库密码。
- `cf1100/`、`hdu9/`、`ICPC-Problem-Creator.skill-master/` 等无关目录。

## 环境要求

- Windows + PowerShell
- Python 3.9+
- Node.js 18+
- JDK 17+
- PostgreSQL 15+，推荐安装 pgvector
- Maven 可使用 `Project2/mvnw.cmd`

## 数据库初始化

创建两个数据库：

```sql
CREATE DATABASE hospital;
CREATE DATABASE headct_rag;
```

初始化 Project2：

```powershell
cd D:\exam
$env:PGPASSWORD="postgres"
.\Project2\sql\init_project2_db.ps1 -Database hospital -User postgres
```

初始化 RAG/报告/EMR 数据库：

```powershell
cd D:\exam
.\HeadCTOrchestrator\scripts\headct_rag_init_db.ps1 -Database headct_rag -AppUser postgres -AppPassword postgres
```

如果本地密码不是 `postgres`，请改用环境变量覆盖，不要把密码提交：

```powershell
$env:PROJECT2_DB_USERNAME="postgres"
$env:PROJECT2_DB_PASSWORD="your_password"
$env:PROJECT2_DB_URL="jdbc:postgresql://localhost:5432/hospital?useSSL=false&serverTimezone=Asia/Shanghai&characterEncoding=utf8"
$env:RAG_DB_DSN="postgresql://postgres:your_password@localhost:5432/headct_rag"
```

## API Key 配置

真实 RAG/LLM 需要阿里百炼 / DashScope API Key。

```powershell
Copy-Item .\HeadCTOrchestrator\scripts\headct_rag_env.example.ps1 .\HeadCTOrchestrator\scripts\headct_rag_env.local.ps1
notepad .\HeadCTOrchestrator\scripts\headct_rag_env.local.ps1
```

在 local 文件中填写：

```powershell
$env:DASHSCOPE_API_KEY="your_key"
$env:ALI_BAILIAN_API_KEY="your_key"
$env:RAG_DB_DSN="postgresql://postgres:your_password@localhost:5432/headct_rag"
```

`headct_rag_env.local.ps1` 已被 `.gitignore` 忽略。

## 安装依赖

Python 依赖按模块安装，例如：

```powershell
python -m pip install -r .\Filter\Fastapi\requirements.txt
python -m pip install -r .\HeadCTOrchestrator\requirements.txt
python -m pip install -r .\HeadCTLesionDetection\requirements.txt
python -m pip install -r .\HeadCTReportService\requirements.txt
python -m pip install -r .\HeadCTEMRService\requirements.txt
```

前端依赖：

```powershell
cd D:\exam\frontend
npm install
```

Project2 依赖由 Maven Wrapper 自动下载：

```powershell
cd D:\exam\Project2
.\mvnw.cmd -q -DskipTests compile
```

## 启动全链路

```powershell
cd D:\exam
.\scripts\start_headct_platform.ps1 -Restart
```

启动前端：

```powershell
cd D:\exam\frontend
npm run dev
```

默认入口：

- 前端：`http://localhost:5173`
- Project2 API：`http://127.0.0.1:8092`
- HeadCT Orchestrator：`http://127.0.0.1:8010`
- Report Service：`http://127.0.0.1:8030`

默认演示账号：

- 患者：`13800001111 / 123456`
- 医生：`doctor / 123456`
- 管理员：`admin / 123456`
- 医技：`medicaltech / 123456`
- 药房：`pharmacist / 123456`

## 验收命令

```powershell
python -m pytest HeadCTOrchestrator/tests -q
python -m pytest HeadCTReportService/tests -q
python -m pytest Filter/Fastapi/tests HeadCTLesionDetection/tests -q
```

```powershell
python scripts\e2e_project2_core_business.py
python scripts\e2e_project2_extended_business.py
python scripts\e2e_project2_real_business.py
```

```powershell
cd D:\exam\frontend
npm run build
npm run test:visual -- tests/visual/project2-full-acceptance.spec.ts tests/visual/mini-patient.spec.ts tests/visual/headct-workflow-screenshots.spec.ts
```

最近一次完整验收记录见：

- `最终交付验收记录_2026-06-29.md`

## 模型权重说明

仓库不包含大模型权重。服务会按以下顺序寻找本地权重：

- `Filter/model/external_weights/...`
- `Filter/model/runs/...`
- `HeadCTLesionDetection/models/hemorrhage/external_weights/...`
- `HeadCTLesionDetection/models/hemorrhage/runs/...`

未提供真实权重时，可用于链路验证；需要真实模型效果时，请按各模块 README 放置权重文件。
