# Project2 前端缺口接口补全与 JWT 接入记录

## 本次目标

根据前端 `frontend/src/api/index.ts` 暴露但当前 Project2 后端未映射的接口，补齐后端 Controller、Service、DTO、VO 与 JWT 返回逻辑。

重点：

- 前端导出的接口必须全部能映射到后端 OpenAPI。
- 登录、验证码登录、患者注册登录统一返回 JWT。
- 不引入额外前端改动，优先兼容当前 Orval 生成客户端。

## 补齐接口

### 认证接口

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/auth/send-code` | `POST` | 员工验证码发送入口，当前演示验证码为 `123456` |
| `/api/auth/login-by-code` | `POST` | 员工验证码登录，返回 JWT |

### 患者认证接口

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/patient/send-code` | `POST` | 患者验证码发送入口，当前演示验证码为 `123456` |
| `/api/patient/auth/register` | `POST` | 患者验证码注册/登录，存在患者则更新基础信息，不存在则创建患者档案，返回 JWT |
| `/api/patient/logout` | `POST` | 患者退出入口，JWT 无状态，客户端清理 token |
| `/api/patient/switch` | `POST` | 切换就诊人，按 `patientId` 重新签发患者 JWT |
| `/api/patient/list` | `GET` | 患者列表，供前端旧导出兼容 |

## JWT 接入说明

原项目已经存在 `JwtUtil` 和 `jjwt` 依赖，本次不是另起一套认证体系，而是扩展原有工具。

新增/调整：

- `JwtUtil.generatePatientToken(Integer patientId, String phone, String caseNumber)`
- 患者 JWT claims 包含：
  - `userId`
  - `patientId`
  - `username`
  - `phone`
  - `caseNumber`
  - `roleType=PATIENT`
- 员工登录、员工验证码登录继续使用 `JwtUtil.generateToken(employeeId, realname, roleType)`。

## 代码变更范围

新增：

- `Project2/src/main/java/com/neuedu/his/model/dto/SendCodeRequestDTO.java`
- `Project2/src/main/java/com/neuedu/his/model/dto/PatientAuthRegisterRequestDTO.java`
- `Project2/src/main/java/com/neuedu/his/model/vo/PatientListVO.java`
- `Project2/src/test/java/com/neuedu/his/controller/AuthPatientContractTest.java`

修改：

- `Project2/src/main/java/com/neuedu/his/controller/AuthController.java`
- `Project2/src/main/java/com/neuedu/his/controller/PatientController.java`
- `Project2/src/main/java/com/neuedu/his/service/AuthService.java`
- `Project2/src/main/java/com/neuedu/his/service/PatientService.java`
- `Project2/src/main/java/com/neuedu/his/service/impl/AuthServiceImpl.java`
- `Project2/src/main/java/com/neuedu/his/service/impl/PatientServiceImpl.java`
- `Project2/src/main/java/com/neuedu/his/mapper/EmployeeMapper.java`
- `Project2/src/main/java/com/neuedu/his/mapper/PatientMapper.java`
- `Project2/src/main/java/com/neuedu/his/model/vo/LoginResponseVO.java`
- `Project2/src/main/java/com/neuedu/his/util/JwtUtil.java`

## 验证记录

### 1. TDD 红灯

先新增 `AuthPatientContractTest`，测试缺口接口。

初次运行结果：

```text
AuthService 缺少 loginByCode(LoginRequestDTO)
AuthService 缺少 patientAuthRegister(...)
```

说明测试确实覆盖了前端缺失接口。

### 2. 契约测试

```powershell
cd D:\exam\Project2
$env:MAVEN_USER_HOME='D:\exam\.maven'
.\mvnw.cmd "-Dmaven.repo.local=D:\exam\.m2\repository" -q "-Dtest=AuthPatientContractTest" test
```

结果：通过。

### 3. Project2 全量测试

```powershell
cd D:\exam\Project2
$env:MAVEN_USER_HOME='D:\exam\.maven'
.\mvnw.cmd "-Dmaven.repo.local=D:\exam\.m2\repository" -q test
```

结果：通过。

### 4. 临时 OpenAPI 检查

启动临时 Project2 实例到 `18092` 端口，读取 `/v3/api-docs`。

缺口接口检查结果：

```json
{
  "status": "ok",
  "missing": []
}
```

### 5. 前端导出 API 到后端 OpenAPI 反向核查

核查结果：

```json
{
  "frontendExports": 41,
  "backendMapped": 41,
  "gaps": []
}
```

## 当前结论

当前前端暴露的 41 个 API 导出已经全部能映射到更新后的 Project2 后端 OpenAPI。

登录相关接口已统一返回 JWT：

- 员工密码登录
- 员工验证码登录
- 患者验证码登录
- 患者验证码注册/登录
- 患者切换就诊人重新签发 token

## 后续建议

1. 将演示验证码 `123456` 后续替换为 Redis 短期验证码缓存。
2. 增加 `JwtAuthenticationFilter`，对受保护接口做 token 解析与角色校验。
3. 增加 token 刷新接口与退出黑名单机制。
4. 将患者列表接口改为按当前登录账号关联查询，避免直接返回全部患者。
5. 前端重新运行 Orval 生成客户端，确保模型类型与最新 OpenAPI 完全一致。
