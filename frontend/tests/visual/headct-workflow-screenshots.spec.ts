import { expect, test, type Page } from '@playwright/test'
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'

const rootDir = path.resolve('..')
const screenshotDir = path.resolve('visual-results', 'headct-workflow')
const sampleCtPath = path.resolve(rootDir, 'testdata', 'headct', 'head_ct_positive_case.nii.gz')
const reportBaseUrl = process.env.REPORT_BASE_URL || 'http://127.0.0.1:8030'
const emrBaseUrl = process.env.EMR_BASE_URL || 'http://127.0.0.1:8040'
const emrToken = process.env.HEADCT_LOCAL_EMR_TOKEN || 'headct-local-emr-change-before-production'

type RuntimeIssue = { type: 'console' | 'pageerror' | 'response'; message: string }
type HeadCtE2ESummary = {
  status: string
  business_case: { register_id: number; check_request_id: number }
  report_service_id: string
  report_service_status: string
  emr_document_id: string
  emr_status: string
  persisted: Record<string, number>
}

const screenshot = async (page: Page, name: string) => {
  fs.mkdirSync(screenshotDir, { recursive: true })
  await page.screenshot({ path: path.join(screenshotDir, `${test.info().project.name}-${name}.png`), fullPage: true })
}

const attachRuntimeGuards = (page: Page) => {
  const issues: RuntimeIssue[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') issues.push({ type: 'console', message: message.text() })
  })
  page.on('pageerror', (error) => issues.push({ type: 'pageerror', message: error.message }))
  page.on('response', (response) => {
    if (response.status() >= 500) issues.push({ type: 'response', message: `${response.status()} ${response.url()}` })
  })
  return issues
}

const assertNoVisibleError = async (page: Page, issues: RuntimeIssue[]) => {
  await page.waitForLoadState('domcontentloaded')
  await page.waitForTimeout(500)
  await expect(page.locator('.el-message--error')).toHaveCount(0)
  await expect(page.locator('.van-toast--fail')).toHaveCount(0)
  await expect(page.getByText(/Request failed|Internal Server Error|服务器内部错误|登录失败|加载失败|影像上传失败|AI识别失败|AI报告生成失败/)).toHaveCount(0)
  expect(issues, JSON.stringify(issues, null, 2)).toEqual([])
}

const writeAuth = async (page: Page, token: string, user: unknown) => {
  await page.addInitScript(({ token, user }) => {
    window.localStorage.setItem('token', token)
    window.localStorage.setItem('user', JSON.stringify(user))
  }, { token, user })
  await page.evaluate(({ token, user }) => {
    window.localStorage.setItem('token', token)
    window.localStorage.setItem('user', JSON.stringify(user))
  }, { token, user })
}

const loginDoctor = async (page: Page) => {
  await page.goto('/auth/login')
  const response = await page.request.post('/api/auth/login', { data: { username: 'doctor', password: '123456', loginType: 'DOCTOR' } })
  expect(response.ok()).toBeTruthy()
  const user = await response.json()
  expect(user.token).toBeTruthy()
  await writeAuth(page, user.token, user)
}

const runRealBusinessWorkflow = (): HeadCtE2ESummary => {
  const output = execFileSync('python', ['scripts/e2e_project2_real_business.py'], {
    cwd: rootDir,
    encoding: 'utf-8',
    maxBuffer: 1024 * 1024 * 8,
    env: { ...process.env, HEADCT_E2E_SAMPLE_CT: sampleCtPath },
  })
  const summary = JSON.parse(output) as HeadCtE2ESummary
  expect(summary.status).toBe('success')
  expect(summary.report_service_status).toBe('released')
  expect(summary.emr_status).toBe('final')
  expect(summary.persisted.ai_image_analysis).toBeGreaterThan(0)
  expect(summary.persisted.ai_generated_report).toBeGreaterThan(0)
  return summary
}

const renderEvidence = async (page: Page, title: string, cards: Record<string, string>, detail: unknown) => {
  const cardHtml = Object.entries(cards).map(([label, value]) => `<div class="card"><span>${label}</span><b>${value}</b></div>`).join('')
  await page.setContent(`<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" />
    <style>
      body{margin:0;font-family:Microsoft YaHei,Arial,sans-serif;background:#f5f7fb;color:#172033}
      main{max-width:1120px;margin:32px auto;padding:0 24px}.panel{background:#fff;border:1px solid #d9e2ef;border-radius:8px;padding:24px;box-shadow:0 8px 24px rgba(15,23,42,.08)}
      h1{margin:0 0 18px;font-size:26px}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-bottom:18px}
      .card{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:16px;min-height:82px}.card span{display:block;color:#64748b;font-size:13px;margin-bottom:8px}.card b{font-size:17px;color:#047857;overflow-wrap:anywhere}
      pre{white-space:pre-wrap;background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;overflow:auto}
    </style></head><body><main><section class="panel"><h1>${title}</h1><div class="grid">${cardHtml}</div><pre>${JSON.stringify(detail, null, 2)}</pre></section></main></body></html>`)
}

// Legacy API-seeded screenshot flow. Strict acceptance now uses
// headct-real-user-workflow.spec.ts, which uploads CT from the browser UI.
test.describe.skip('Head CT normal workflow screenshot evidence', () => {
  test('captures upload, lesion recognition, AI conclusion, report release and EMR archive', async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== 'desktop-chrome', 'Workflow evidence is captured once on desktop.')
    test.setTimeout(240_000)

    const issues = attachRuntimeGuards(page)
    const summary = runRealBusinessWorkflow()

    await loginDoctor(page)
    await page.goto(`/doctor/visit?registerId=${summary.business_case.register_id}&name=HeadCTWorkflow`, { waitUntil: 'domcontentloaded' })
    await page.getByRole('tab', { name: '结果' }).click()
    await page.getByRole('button', { name: '刷新结果' }).click()
    await expect(page.getByText('AI 影像识别与报告生成')).toBeVisible()
    await page.getByPlaceholder('选择或输入检查申请ID').fill(String(summary.business_case.check_request_id))
    await page.locator('input[type="file"]').setInputFiles(sampleCtPath)

    const [uploadResponse] = await Promise.all([
      page.waitForResponse((response) => response.url().includes('/api/ai/image/upload') && response.request().method() === 'POST', { timeout: 60_000 }),
      page.getByRole('button', { name: '上传影像' }).click(),
    ])
    expect(uploadResponse.ok()).toBeTruthy()
    await expect(page.getByPlaceholder('上传后自动填入，也可手动输入')).toHaveValue(/^\d+$/)
    await assertNoVisibleError(page, issues)
    await screenshot(page, '01-upload-ct-image')

    const [analysisResponse] = await Promise.all([
      page.waitForResponse((response) => response.url().includes('/api/ai/image/analyze') && response.request().method() === 'POST', { timeout: 180_000 }),
      page.getByRole('button', { name: 'AI识别' }).click(),
    ])
    expect(analysisResponse.ok()).toBeTruthy()
    await expect(page.getByText('病灶模型')).toBeVisible({ timeout: 20_000 })
    await expect(page.getByText('AI结论')).toBeVisible()
    await assertNoVisibleError(page, issues)
    await screenshot(page, '02-lesion-recognition')

    const [reportResponse] = await Promise.all([
      page.waitForResponse((response) => response.url().includes('/api/ai/report/generate') && response.request().method() === 'POST', { timeout: 120_000 }),
      page.getByRole('button', { name: '生成报告' }).click(),
    ])
    expect(reportResponse.ok()).toBeTruthy()
    await expect(page.getByText('报告ID')).toBeVisible({ timeout: 20_000 })
    await expect(page.getByText('released')).toBeVisible({ timeout: 20_000 })
    await assertNoVisibleError(page, issues)
    await screenshot(page, '03-ai-assisted-conclusion-and-report')

    const releasedReportResponse = await page.request.get(`${reportBaseUrl}/api/v1/reports/${summary.report_service_id}`, { headers: { 'X-Actor-Id': 'doctor-reporting-001', 'X-Actor-Role': 'reporting_doctor' } })
    expect(releasedReportResponse.ok()).toBeTruthy()
    const releasedReportPayload = await releasedReportResponse.json()
    expect(releasedReportPayload.report.status).toBe('released')
    await renderEvidence(page, '头部 CT 报告发布证据', { 报告状态: releasedReportPayload.report.status, 报告ID: summary.report_service_id, 版本: String(releasedReportPayload.report.version_number), 关联检查: String(releasedReportPayload.report.accession_number || releasedReportPayload.report.study_id) }, releasedReportPayload.report)
    await screenshot(page, '04-report-released')

    const emrResponse = await page.request.get(`${emrBaseUrl}/api/v1/diagnostic-reports/${summary.emr_document_id}`, { headers: { Authorization: `Bearer ${emrToken}` } })
    expect(emrResponse.ok()).toBeTruthy()
    const emrPayload = await emrResponse.json()
    await renderEvidence(page, '头部 CT 报告 / EMR 归档证据', { 报告服务状态: summary.report_service_status, EMR状态: summary.emr_status, 报告ID: summary.report_service_id, 归档文档号: summary.emr_document_id }, emrPayload.report)
    await screenshot(page, '05-emr-archive')
  })
})
