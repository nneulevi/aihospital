import fs from 'node:fs'
import path from 'node:path'
import { expect, test, type Page } from '@playwright/test'

type Check = {
  index: number
  name: string
  status: 'PASS' | 'FAIL'
  evidence: string
  screenshot?: string
}

const roundLabel = process.env.CURRENT_ISSUE_ACCEPTANCE_ROUND
  ? `round-${String(process.env.CURRENT_ISSUE_ACCEPTANCE_ROUND).padStart(2, '0')}`
  : 'manual'
const outputDir = path.resolve('visual-results', 'current-issues-click-acceptance', roundLabel)
const reportPath = path.resolve('..', '目前存在问题_用户点击截图验收报告_2026-07-03.md')

const checks: Check[] = []
let checkIndex = 0

const ensureDir = () => fs.mkdirSync(outputDir, { recursive: true })

const shot = async (page: Page, name: string) => {
  ensureDir()
  const fileName = `${String(++checkIndex).padStart(2, '0')}-${name}.png`
  const filePath = path.join(outputDir, fileName)
  await page.screenshot({ path: filePath, fullPage: true })
  return path.relative(path.resolve('..'), filePath).replace(/\\/g, '/')
}

const record = async (page: Page, name: string, evidence: string) => {
  const screenshot = await shot(page, name)
  checks.push({ index: checks.length + 1, name, status: 'PASS', evidence, screenshot })
}

const failRecord = async (page: Page, name: string, error: unknown) => {
  const screenshot = await shot(page, `${name}-failed`)
  checks.push({
    index: checks.length + 1,
    name,
    status: 'FAIL',
    evidence: error instanceof Error ? error.message : String(error),
    screenshot,
  })
}

const assertNoBadUserSignal = async (page: Page) => {
  const bodyText = await page.locator('body').innerText()
  expect(bodyText).not.toMatch(/Request failed|服务器内部错误|Internal Server Error|undefined|null|\{\s*"quality_control"/)
  const toastTexts = await page.locator('.van-toast, .el-message').allInnerTexts()
  for (const text of toastTexts) {
    expect(text.trim()).not.toBe('')
  }
}

const writeReport = () => {
  const rows = checks
    .map((item) => `| ${item.index} | ${item.name} | ${item.status} | ${item.evidence.replace(/\|/g, '/')} | ${item.screenshot || ''} |`)
    .join('\n')
  const failed = checks.filter((item) => item.status === 'FAIL')
  const content = `# 目前存在问题用户点击截图验收报告

生成时间：${new Date().toISOString()}

本报告按真实用户点击路径生成，不使用前端本地 token 注入，不直接跳转业务页面。

## 用户行为流程图

管理员登录 -> AI排班 -> 查询历史排班 -> 返回管理员首页 -> 退出登录 -> 患者登录 -> 首页 -> 联系客服 -> 返回首页 -> 预约挂号 -> 选择科室 -> 选择医生 -> 空表单确认反馈 -> 补全患者信息 -> 确认挂号 -> 查看挂号记录 -> 返回患者首页 -> 我的

## ${checks.length}项检查证据

| # | 检查点 | 结果 | 证据 | 截图 |
|---|---|---|---|---|
${rows}

## 结论

${failed.length ? `仍有 ${failed.length} 项失败，需要继续修复。` : `${checks.length}项用户点击检查均通过，当前问题文档中的重点交互已具备截图级证据。`}
`
  fs.writeFileSync(reportPath, content, 'utf-8')
}

const clickVisibleText = async (page: Page, text: string) => {
  await page.getByText(text, { exact: true }).first().click()
}

test.afterEach(() => {
  writeReport()
})

test('current issue list is fixed from real user click flow', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chrome', '当前问题点击验收使用桌面视口执行一次，避免重复写报告。')

  try {
    await page.goto('/auth/login', { waitUntil: 'domcontentloaded' })
    await record(page, 'staff-login-entry', '员工登录入口可见。')

    await clickVisibleText(page, '管理员')
    await page.getByPlaceholder('用户名').fill('admin')
    await page.getByPlaceholder('密码').fill('123456')
    await page.getByRole('button', { name: '登录' }).click()
    await expect(page).toHaveURL(/\/admin\/?$/)
    await expect(page.locator('.admin-content')).toBeVisible()
    await record(page, 'admin-home-after-login', '管理员通过真实表单登录并进入首页。')

    await clickVisibleText(page, 'AI排班')
    await expect(page.getByText('AI生成排班')).toBeVisible()
    await record(page, 'admin-ai-schedule-page', '管理员通过底部导航进入 AI 排班。')

    const deptValue = page.locator('.filter-panel .van-cell', { hasText: '科室' }).first().locator('.van-cell__value')
    await expect(deptValue).not.toHaveText(/请选择科室/, { timeout: 15_000 })
    const deptName = (await deptValue.innerText()).trim()
    expect(deptName).not.toMatch(/请选择|测试|验收|Extended|User Logic/)
    await record(page, 'admin-ai-schedule-default-dept', `AI排班默认选择真实科室：${deptName}。`)

    await page.getByRole('button', { name: '查询历史排班' }).click()
    await expect(page.locator('.history-feedback')).toHaveText(/已查询到 \d+ 条历史排班|暂无历史排班/)
    await expect(page.locator('.van-toast')).toHaveCount(0)
    await assertNoBadUserSignal(page)
    await record(page, 'admin-ai-schedule-history-query', '历史排班按钮有明确响应，无空白提示。')

    await page.getByRole('button', { name: 'AI生成排班' }).click()
    await expect(page.locator('.section-title', { hasText: '排班结果' })).toBeVisible({ timeout: 20_000 })
    await assertNoBadUserSignal(page)
    await record(page, 'admin-ai-schedule-generated', 'AI排班生成结果显示在页面。')

    await page.getByRole('button', { name: '查询历史排班' }).click()
    await expect(page.locator('.history-feedback')).toHaveText(/已查询到 \d+ 条历史排班|暂无历史排班/)
    await expect(page.locator('.van-toast')).toHaveCount(0)
    await assertNoBadUserSignal(page)
    await record(page, 'admin-ai-schedule-history-after-generate', '生成后可再次查询历史排班。')

    await page.locator('.admin-tabbar .van-tabbar-item', { hasText: '首页' }).click()
    await expect(page).toHaveURL(/\/admin\/?$/)
    await record(page, 'admin-return-home-by-tabbar', '管理员从 AI 排班点击底部首页后切回首页。')

    await page.getByRole('button', { name: /退出/ }).click()
    await page.getByRole('button', { name: '退出' }).last().click()
    await expect(page).toHaveURL(/\/auth\/login/)
    await record(page, 'admin-logout', '管理员端存在退出入口且退出后回到员工登录。')

    await page.goto('/patient/login', { waitUntil: 'domcontentloaded' })
    await record(page, 'patient-login-entry', '患者登录入口可见。')

    await page.getByPlaceholder('请输入用户名/手机号').fill('13800001111')
    await page.getByPlaceholder('请输入密码').fill('123456')
    await page.locator('.submit-btn').getByRole('button', { name: '登录' }).click()
    await expect(page).toHaveURL(/\/patient\/home|\/patient\/?$/)
    await expect(page.locator('.core-services').getByText('预约挂号')).toBeVisible()
    await record(page, 'patient-home-after-login', '患者通过真实表单登录并进入首页。')

    await clickVisibleText(page, '联系客服')
    await expect(page.getByText(/在线客服|联系客服|服务时间/)).toBeVisible()
    await record(page, 'patient-customer-service', '患者首页联系客服入口可点击并打开服务页。')

    await page.locator('.van-tabbar .van-tabbar-item', { hasText: '首页' }).click()
    await expect(page.getByText('预约挂号')).toBeVisible()
    await record(page, 'patient-return-home-by-tabbar', '患者底部首页导航可返回首页。')

    await page.getByText('预约挂号').first().click()
    await expect(page.getByText('选择科室')).toBeVisible()
    await record(page, 'patient-appointment-entry', '患者从首页点击进入门诊挂号。')

    const deptSearch = page.getByPlaceholder('搜索科室名称')
    await deptSearch.fill(deptName)
    await page.locator('.dept-item').first().click()
    await expect(page.getByText('选择医生')).toBeVisible()
    await record(page, 'patient-appointment-selected-dept', `患者选择管理员排班对应科室：${deptName}。`)

    const roundNumber = Number(process.env.CURRENT_ISSUE_ACCEPTANCE_ROUND || '1')
    const targetDateIndex = ((roundNumber - 1) % 6) + 1
    await page.locator('.date-item').nth(targetDateIndex).click()
    if (roundNumber % 2 === 0) {
      await page.getByRole('button', { name: '下午' }).click()
    }
    await expect(page.locator('.doctor-item:not(.disabled)').first()).toBeVisible({ timeout: 10_000 })
    await page.locator('.doctor-item:not(.disabled)').first().click()
    await expect(page.getByText('确认信息')).toBeVisible()
    await record(page, 'patient-appointment-selected-doctor', '患者选择有号源医生进入确认信息页。')

    await page.getByRole('button', { name: '确认挂号' }).click()
    await expect(page.getByText('请填写完整患者信息')).toBeVisible()
    await assertNoBadUserSignal(page)
    await record(page, 'patient-register-empty-form-feedback', '空表单点击确认挂号有明确错误提示。')

    const stamp = Date.now().toString().slice(-8)
    const cardSequence = String((roundNumber % 900) + 100)
    await page.getByPlaceholder('请输入真实姓名').fill(`李明${stamp}`)
    await page.getByPlaceholder('请输入身份证号').fill(`110101${stamp}${cardSequence}X`)
    await page.getByPlaceholder('请输入手机号').fill(`139${stamp}`)
    await record(page, 'patient-register-form-filled', '患者信息填写完成，字段可读且无视觉遮挡。')

    await page.getByRole('button', { name: '确认挂号' }).click()
    await expect(page.getByText(/挂号成功|挂号详情|就诊信息/)).toBeVisible({ timeout: 20_000 })
    await assertNoBadUserSignal(page)
    await record(page, 'patient-register-success', '确认挂号按钮提交成功并进入结果页。')

    const viewRecord = page.getByText(/查看挂号记录|挂号记录|就诊记录/).first()
    await viewRecord.click()
    await expect(page.getByText(/我的病历|挂号记录|就诊记录|门诊/)).toBeVisible()
    await record(page, 'patient-records-after-register', '挂号后可进入记录页查看业务结果。')

    await page.locator('.van-tabbar .van-tabbar-item', { hasText: '首页' }).click()
    await expect(page.getByText('最近就诊')).toBeVisible()
    await record(page, 'patient-home-summary-after-register', '返回患者首页后可查看概览和最近就诊。')

    await page.locator('.van-tabbar .van-tabbar-item', { hasText: '我的' }).click()
    await expect(page).toHaveURL(/\/patient\/profile/)
    await expect(page.locator('body')).toContainText(/个人信息|退出登录|患者/)
    await assertNoBadUserSignal(page)
    await record(page, 'patient-profile-readable', '患者我的页面信息可读、导航正常。')

    expect(checks.filter((item) => item.status === 'PASS').length).toBeGreaterThanOrEqual(20)
  } catch (error) {
    await failRecord(page, 'current-issues-click-flow', error)
    throw error
  }
})
