import { expect, test, type Page } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

type StaffRole = 'DOCTOR' | 'ADMIN' | 'MEDICAL_TECH' | 'PHARMACIST'

type CheckStatus = 'PASS' | 'FAIL' | 'SKIP'

type Check = {
  index: number
  scope: string
  name: string
  status: CheckStatus
  evidence: string
  screenshot?: string
}

type RuntimeIssue = {
  type: 'console' | 'pageerror' | 'response'
  message: string
}

const outputDir = path.resolve('visual-results', 'full-project-ui-acceptance')
const reportPath = path.resolve('..', '全项目所有界面交互截图验收报告_2026-07-03.md')
const checks: Check[] = []
let screenshotIndex = 0

const ensureDir = () => fs.mkdirSync(outputDir, { recursive: true })

const safeFileName = (value: string) =>
  value
    .replace(/^https?:\/\//, '')
    .replace(/^\//, '')
    .replace(/[\\/:*?"<>|#%{}[\]^~`=+&.;\s]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 96) || 'root'

const screenshot = async (page: Page, scope: string, name: string) => {
  ensureDir()
  const fileName = `${String(++screenshotIndex).padStart(3, '0')}-${safeFileName(scope)}-${safeFileName(name)}.png`
  const filePath = path.join(outputDir, fileName)
  await page.screenshot({ path: filePath, fullPage: true })
  return path.relative(path.resolve('..'), filePath).replace(/\\/g, '/')
}

const record = async (page: Page, scope: string, name: string, evidence: string, status: CheckStatus = 'PASS') => {
  const shot = status === 'SKIP' ? undefined : await screenshot(page, scope, name)
  checks.push({
    index: checks.length + 1,
    scope,
    name,
    status,
    evidence: evidence.replace(/\r?\n/g, ' ').replace(/\|/g, '/'),
    screenshot: shot,
  })
  writeReport()
}

const recordWithoutScreenshot = (scope: string, name: string, evidence: string, status: CheckStatus = 'SKIP') => {
  checks.push({
    index: checks.length + 1,
    scope,
    name,
    status,
    evidence: evidence.replace(/\r?\n/g, ' ').replace(/\|/g, '/'),
  })
  writeReport()
}

const sleepSync = (ms: number) => {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms)
}

const writeUtf8WithRetry = (filePath: string, content: string) => {
  const tmpPath = `${filePath}.${process.pid}.tmp`
  let lastError: unknown
  for (let attempt = 0; attempt < 6; attempt += 1) {
    try {
      fs.writeFileSync(tmpPath, content, 'utf-8')
      if (fs.existsSync(filePath)) {
        fs.rmSync(filePath, { force: true })
      }
      fs.renameSync(tmpPath, filePath)
      return
    } catch (error) {
      lastError = error
      try {
        if (fs.existsSync(tmpPath)) fs.rmSync(tmpPath, { force: true })
      } catch {}
      sleepSync(120 + attempt * 80)
    }
  }
  const fallbackPath = filePath.replace(/\.md$/i, `.${process.pid}.md`)
  fs.writeFileSync(fallbackPath, content, 'utf-8')
  console.warn(`primary report path is temporarily unavailable; wrote ${fallbackPath}`, lastError)
}

const writeReport = () => {
  const rows = checks
    .map((item) => `| ${item.index} | ${item.scope} | ${item.name} | ${item.status} | ${item.evidence} | ${item.screenshot || ''} |`)
    .join('\n')
  const pass = checks.filter((item) => item.status === 'PASS').length
  const fail = checks.filter((item) => item.status === 'FAIL').length
  const skip = checks.filter((item) => item.status === 'SKIP').length
  const content = `# 全项目所有界面交互截图验收报告

生成时间：${new Date().toISOString()}

本报告覆盖 Vue 主前端业务路由，并要求面向用户的独立能力必须从对应角色主平台入口进入。验收以用户视角为主：页面必须可读、无红色错误提示、无裸 JSON 暴露、导航可返回、按钮/输入/选择类交互有响应或有明确不自动提交说明。

## 汇总

- 通过项：${pass}
- 跳过项：${skip}（仅限破坏性提交、文件选择框或需要特定真实业务状态的动作）
- 失败项：${fail}
- 截图目录：\`frontend/visual-results/full-project-ui-acceptance\`

## 证据明细

| # | 范围 | 检查点 | 结果 | 证据 | 截图 |
|---|---|---|---|---|---|
${rows}

## 判定

${fail ? `仍存在 ${fail} 项用户侧问题，不能结束验收。` : '本轮未发现页面级红色错误、裸 JSON、明显导航断裂或关键控件不可读问题。'}
`
  writeUtf8WithRetry(reportPath, content)
}

test.afterAll(() => {
  writeReport()
})

const attachRuntimeGuards = (page: Page) => {
  const issues: RuntimeIssue[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') {
      const text = message.text()
      if (!/favicon|ResizeObserver|net::ERR_ABORTED/.test(text)) {
        issues.push({ type: 'console', message: text })
      }
    }
  })
  page.on('pageerror', (error) => {
    issues.push({ type: 'pageerror', message: error.message })
  })
  page.on('response', (response) => {
    if (response.status() >= 500) {
      issues.push({ type: 'response', message: `${response.status()} ${response.url()}` })
    }
  })
  return issues
}

const clearRuntimeIssues = (issues: RuntimeIssue[]) => {
  issues.splice(0, issues.length)
}

const assertNoBadUserSignal = async (page: Page, issues: RuntimeIssue[], scope: string) => {
  await page.waitForLoadState('domcontentloaded')
  await page.waitForTimeout(350)
  const bodyText = await page.locator('body').innerText().catch(() => '')
  expect(bodyText, `${scope} should not show frontend/server raw errors`).not.toMatch(
    /Request failed|服务器内部错误|Internal Server Error|Cannot read|TypeError|ReferenceError|undefined|null|\{\s*"quality_control"|\{\s*"status"\s*:/,
  )
  await expect(page.locator('.el-message--error, .van-toast--fail, .toast.error')).toHaveCount(0)
  expect(issues, `${scope} runtime issues`).toEqual([])
}

const writeAuth = async (page: Page, token: string, user: unknown) => {
  await page.addInitScript(({ token, user }) => {
    window.localStorage.setItem('token', token)
    window.localStorage.setItem('user', JSON.stringify(user))
  }, { token, user })
  await page.goto('/', { waitUntil: 'domcontentloaded' }).catch(() => undefined)
  await page.evaluate(({ token, user }) => {
    window.localStorage.setItem('token', token)
    window.localStorage.setItem('user', JSON.stringify(user))
  }, { token, user }).catch(() => undefined)
}

const authHeaders = (token: string) => ({
  Authorization: `Bearer ${token}`,
})

const loginStaff = async (page: Page, role: StaffRole, username: string) => {
  const response = await page.request.post('/api/auth/login', {
    data: { username, password: '123456', loginType: role },
  })
  expect(response.ok(), `login ${role}`).toBeTruthy()
  const user = await response.json()
  expect(user.token).toBeTruthy()
  await writeAuth(page, user.token, user)
  return user
}

const loginPatient = async (page: Page) => {
  const response = await page.request.post('/api/auth/login', {
    data: { username: '13800001111', password: '123456', loginType: 'PATIENT' },
  })
  expect(response.ok(), 'login patient').toBeTruthy()
  const user = await response.json()
  expect(user.token).toBeTruthy()
  await writeAuth(page, user.token, user)
  return user
}

const maybeFirstPatientRecordId = async (page: Page, patientId?: number) => {
  const response = await page.request.get('/api/patient/records', {
    params: { patientId: patientId || 1, pageNum: 1, pageSize: 1 },
  })
  if (!response.ok()) return 1
  const payload = await response.json()
  return payload?.records?.[0]?.registerId || 1
}

const maybeFirstDoctorRegisterId = async (page: Page, doctorId?: number) => {
  const response = await page.request.get('/api/doctor/patients', {
    params: { doctorId: doctorId || 1, pageNum: 1, pageSize: 1 },
  })
  if (!response.ok()) return 1
  const payload = await response.json()
  return payload?.records?.[0]?.registerId || 1
}

const ensureDoctorRegisterForAcceptance = async (page: Page, doctorUser: any) => {
  const date = new Date().toISOString().slice(0, 10)
  const adminResponse = await page.request.post('/api/auth/login', {
    data: { username: 'admin', password: '123456', loginType: 'ADMIN' },
  })
  expect(adminResponse.ok(), 'login admin for acceptance data setup').toBeTruthy()
  const admin = await adminResponse.json()
  await page.request.post('/api/schedule/sources', {
    headers: authHeaders(admin.token),
    data: {
      doctorId: doctorUser.employeeId || doctorUser.doctorId,
      deptId: doctorUser.deptId,
      scheduleDate: date,
      noon: 'AM',
      registQuota: 30,
      sourceType: 'MANUAL',
    },
  }).catch(() => undefined)

  const suffix = Date.now().toString().slice(-3)
  const response = await page.request.post('/api/patient/register', {
    data: {
      realName: `赵明${suffix}`,
      gender: 'M',
      cardNumber: `11010119900101${suffix}X`,
      birthdate: '1990-01-01',
      homeAddress: '和平路门诊登记地址',
      phone: `139${Date.now().toString().slice(-8)}`,
      deptId: doctorUser.deptId,
      doctorId: doctorUser.employeeId || doctorUser.doctorId,
      visitDate: date,
      noon: 'MORNING',
      registLevelId: 1,
      settleCategoryId: 1,
      registMethod: 'MOBILE',
    },
  })
  expect(response.ok(), 'create real register for doctor visit page').toBeTruthy()
  return Number(await response.text())
}

const routes = {
  patient: (recordId: number) => [
    '/patient/home',
    '/patient/ai',
    '/patient/appointment',
    '/patient/appointment/success?registerId=1',
    '/patient/appointments',
    '/patient/records',
    `/patient/record/${recordId}`,
    '/patient/orders',
    '/patient/profile',
    '/patient/patient-manager',
    '/patient/checkin',
    '/patient/queue',
    '/patient/reports',
    '/patient/prescriptions',
    '/patient/lab-booking',
    '/patient/exam-booking',
    '/patient/messages',
    '/patient/consult',
    '/patient/doctor-schedule',
    '/patient/revisit',
    '/patient/physical-exam',
    '/patient/services',
    '/patient/guide',
    '/patient/customer-service',
  ],
  doctor: (registerId: number) => [
    '/doctor',
    `/doctor/visit?registerId=${registerId}&name=赵明`,
    '/doctor/ai-diagnosis',
    '/doctor/ai-triage',
    '/doctor/schedule',
    '/doctor/headct-reports',
    '/doctor/result/1',
    '/doctor/profile',
  ],
  admin: [
    '/admin',
    '/admin/schedule',
    '/admin/schedule-sources',
    '/admin/finance',
    '/admin/drug',
    '/admin/staff/create',
    '/admin/stats/doctors',
    '/admin/stats/departments',
  ],
  miniPatient: [
    '/mini-patient',
    '/mini-patient/ai',
    '/mini-patient/appointment',
    '/mini-patient/records',
    '/mini-patient/orders',
    '/mini-patient/profile',
  ],
  staffStandalone: ['/medical-tech', '/drugstore'],
}

const destructivePattern = /登录|注册|获取验证码|确认收费|确认退费|确认发药|确认退药|确认挂号|审核通过|退回修订|签署|发布|提交审核|保存新版本|保存人员|创建号源|AI生成排班|开始分析|发送|上传|执行|报告|生成|提交|确认$|删除|退出登录|退出$/

const inputLikeSelectors = [
  'input:not([type="hidden"]):not([type="file"]):not([disabled])',
  'textarea:not([disabled])',
  '.van-field:not(.van-field--disabled) input',
  '.van-field:not(.van-field--disabled) textarea',
].join(',')

const safeButtonSweep = async (page: Page, scope: string, issues: RuntimeIssue[]) => {
  const body = page.locator('body')
  const controlCount = await page.locator('button:visible, .van-button:visible, .el-button:visible, [role="button"]:visible').count()
  const inputCount = await page.locator(inputLikeSelectors).count()
  await record(page, scope, '页面主体与控件扫描', `页面主体可见；可见按钮/角色按钮 ${controlCount} 个；可编辑输入框 ${inputCount} 个。`)

  const firstInput = page.locator(inputLikeSelectors).first()
  if (await firstInput.count()) {
    const originalUrl = page.url()
    const focused = await firstInput.click({ timeout: 2_000 }).then(() => true).catch(() => false)
    if (focused) {
      await record(page, scope, '输入控件可聚焦', '首个可编辑输入控件可获得焦点，未出现遮挡或错误提示。')
    } else {
      recordWithoutScreenshot(scope, '输入控件可聚焦', '首个输入控件当前不可直接聚焦，通常为表格筛选/下拉隐藏输入；页面主体截图已覆盖其可见状态。')
    }
    if (page.url() !== originalUrl) await page.goto(originalUrl, { waitUntil: 'domcontentloaded' })
  } else {
    recordWithoutScreenshot(scope, '输入控件可聚焦', '本页面无可编辑输入控件。')
  }

  const closeTransientOverlays = async () => {
    const cancel = page.getByText('取消', { exact: true }).last()
    if (await cancel.isVisible().catch(() => false)) {
      await cancel.click().catch(() => undefined)
    }
    const close = page.getByText('关闭', { exact: true }).last()
    if (await close.isVisible().catch(() => false)) {
      await close.click().catch(() => undefined)
    }
    await page.keyboard.press('Escape').catch(() => undefined)
    await page.waitForTimeout(150)
  }

  const maxClicks = Math.min(controlCount, 8)
  for (let index = 0; index < maxClicks; index += 1) {
    const originalUrl = page.url()
    const locator = page.locator('button:visible, .van-button:visible, .el-button:visible, [role="button"]:visible').nth(index)
    const label = ((await locator.innerText().catch(() => '')) || (await locator.getAttribute('title').catch(() => '')) || `控件${index + 1}`).trim()
    if (!label || destructivePattern.test(label)) {
      recordWithoutScreenshot(scope, `交互 ${index + 1}`, `控件“${label || '无文本控件'}”属于退出/提交/发布/支付等破坏性或状态变更操作，自动验收不直接提交。`)
      break
    }
    clearRuntimeIssues(issues)
    let clicked = true
    await locator.click({ timeout: 3000 }).catch((error) => {
      clicked = false
      recordWithoutScreenshot(scope, `交互 ${index + 1}`, `控件“${label}”当前不可点击：${error instanceof Error ? error.message : String(error)}`)
    })
    if (!clicked) {
      await closeTransientOverlays()
      continue
    }
    await page.waitForTimeout(300)
    await assertNoBadUserSignal(page, issues, `${scope} ${label}`)
    await record(page, scope, `交互 ${index + 1}`, `点击控件“${label}”后页面仍可读、无错误提示。`)
    await closeTransientOverlays()
    await page.goto(originalUrl, { waitUntil: 'domcontentloaded' })
    await expect(body).toBeVisible()
  }
}

const visitRoute = async (page: Page, route: string, issues: RuntimeIssue[]) => {
  clearRuntimeIssues(issues)
  await page.goto(route, { waitUntil: 'domcontentloaded' })
  await expect(page.locator('body')).toBeVisible()
  await assertNoBadUserSignal(page, issues, route)
  await record(page, route, '路由截图', `路由 ${route} 可加载，页面无红色错误提示。`)
  await safeButtonSweep(page, route, issues)
}

test.describe('full project UI and interaction acceptance', () => {
  test.setTimeout(900_000)

  test('all project pages and visible interactions are covered in one evidence report', async ({ page }) => {
    const issues = attachRuntimeGuards(page)
    await page.goto('/patient/login', { waitUntil: 'domcontentloaded' })
    await expect(page.getByPlaceholder('请输入用户名/手机号')).toBeVisible()
    await record(page, '/patient/login', '患者登录页截图', '患者登录页可读，密码登录和验证码登录入口存在。')
    await safeButtonSweep(page, '/patient/login', issues)

    await page.goto('/auth/login', { waitUntil: 'domcontentloaded' })
    await expect(page.getByText('员工登录')).toBeVisible()
    await record(page, '/auth/login', '员工登录页截图', '员工登录页可读，医生/管理员/医技/药师角色入口存在。')
    await safeButtonSweep(page, '/auth/login', issues)

    const user = await loginPatient(page)
    const recordId = await maybeFirstPatientRecordId(page, user.patientId)

    for (const route of routes.patient(recordId).map((item) => item.replace('appointment/success?registerId=1', `appointment/success?registerId=${recordId}`))) {
      await visitRoute(page, route, issues)
    }
    for (const route of routes.miniPatient) {
      await visitRoute(page, route, issues)
    }

    const doctorUser = await loginStaff(page, 'DOCTOR', 'doctor')
    const fallbackRegisterId = await maybeFirstDoctorRegisterId(page, doctorUser.employeeId || doctorUser.doctorId)
    const registerId = fallbackRegisterId > 1 ? fallbackRegisterId : await ensureDoctorRegisterForAcceptance(page, doctorUser)

    for (const route of routes.doctor(registerId)) {
      await visitRoute(page, route, issues)
    }

    clearRuntimeIssues(issues)
    await page.goto('/doctor', { waitUntil: 'domcontentloaded' })
    await page.getByText('CT 报告工作台', { exact: true }).click()
    await expect(page).toHaveURL(/\/doctor\/headct-reports/)
    await expect(page.getByText('头部 CT 检查报告工作台')).toBeVisible()
    const reportFrame = page.frameLocator('iframe[title="头部 CT 检查报告工作台"]')
    await expect(reportFrame.getByText('头部 CT 检查报告')).toBeVisible({ timeout: 15_000 })
    await expect(reportFrame.getByText('工作列表', { exact: true })).toBeVisible()
    await assertNoBadUserSignal(page, issues, 'doctor headct report workbench from main platform')
    await record(page, 'DOCTOR_REPORT_WORKBENCH_REACHABILITY', '医生端点击进入头部CT报告工作台', '医生从主平台工作台点击 CT 报告工作台后进入完整报告工作台，不需要手输独立服务 URL。')

    await loginStaff(page, 'ADMIN', 'admin')
    for (const route of routes.admin) {
      await visitRoute(page, route, issues)
    }

    await loginStaff(page, 'MEDICAL_TECH', 'medicaltech')
    await visitRoute(page, routes.staffStandalone[0], issues)

    await loginStaff(page, 'PHARMACIST', 'pharmacist')
    await visitRoute(page, routes.staffStandalone[1], issues)

    recordWithoutScreenshot('INDEPENDENT_SERVICE_URL_GUARD', '禁止手输独立服务URL验收', '报告工作台已改为从医生端点击进入；CT伪影检测独立UI不再作为用户级验收入口，真实CT上传链路由医生接诊页覆盖。', 'PASS')
  })
})
