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

type RuntimeIssue = {
  type: 'console' | 'pageerror' | 'response'
  message: string
}

type HeadCtE2ESummary = {
  status: string
  business_case: {
    register_id: number
    check_request_id: number
  }
  image_file_id: number
  analysis_id: number
  ai_imaging_project_status: string
  ai_imaging_workflow_ready: boolean
  report_service_id: string
  report_service_status: string
  emr_document_id: string
  emr_status: string
  persisted: Record<string, number>
}

const ensureScreenshotDir = () => {
  fs.mkdirSync(screenshotDir, { recursive: true })
}

const screenshot = async (page: Page, name: string) => {
  ensureScreenshotDir()
  await page.screenshot({
    path: path.join(screenshotDir, `${test.info().project.name}-${name}.png`),
    fullPage: true,
  })
}

const attachRuntimeGuards = (page: Page) => {
  const issues: RuntimeIssue[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') {
      issues.push({ type: 'console', message: message.text() })
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

const assertNoVisibleError = async (page: Page, issues: RuntimeIssue[]) => {
  await page.waitForLoadState('domcontentloaded')
  await page.waitForTimeout(500)
  await expect(page.locator('.el-message--error')).toHaveCount(0)
  await expect(page.locator('.van-toast--fail')).toHaveCount(0)
  await expect(page.getByText(/Request failed|Internal Server Error|服务器内部错误|登录失败|加载失败|影像上传失败|AI识别失败|AI报告生成失败/)).toHaveCount(0)
  expect(issues, JSON.stringify(issues, null, 2)).toEqual([])
}

const writeAuth = async (page: Page, token: string, user: unknown) => {
  const payload = { token, user }
  await page.addInitScript(({ token, user }) => {
    window.localStorage.setItem('token', token)
    window.localStorage.setItem('user', JSON.stringify(user))
  }, payload)
  await page.evaluate(({ token, user }) => {
    window.localStorage.setItem('token', token)
    window.localStorage.setItem('user', JSON.stringify(user))
  }, payload)
}

const loginDoctor = async (page: Page) => {
  await page.goto('/patient/login')
  const response = await page.request.post('/api/auth/login', {
    data: { username: 'doctor', password: '123456', loginType: 'DOCTOR' },
  })
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
    env: {
      ...process.env,
      HEADCT_E2E_SAMPLE_CT: sampleCtPath,
    },
  })
  const summary = JSON.parse(output) as HeadCtE2ESummary
  expect(summary.status).toBe('success')
  expect(summary.report_service_status).toBe('released')
  expect(summary.emr_status).toBe('final')
  expect(summary.persisted.ai_image_analysis).toBeGreaterThan(0)
  expect(summary.persisted.ai_generated_report).toBeGreaterThan(0)
  return summary
}

const renderEmrArchiveEvidence = async (page: Page, summary: HeadCtE2ESummary, emrReport: any) => {
  await page.setContent(`
    <!doctype html>
    <html lang="zh-CN">
      <head>
        <meta charset="utf-8" />
        <style>
          body { margin: 0; font-family: "Microsoft YaHei", Arial, sans-serif; background: #f4f7fb; color: #1f2937; }
          main { max-width: 1120px; margin: 32px auto; padding: 0 24px; }
          .hero { background: #ffffff; border: 1px solid #d9e2ef; border-radius: 8px; padding: 24px; box-shadow: 0 8px 24px rgba(15,23,42,.08); }
          h1 { margin: 0 0 6px; font-size: 26px; }
          .sub { color: #64748b; margin-bottom: 22px; }
          .grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-bottom: 20px; }
          .card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; min-height: 86px; }
          .label { display: block; color: #64748b; font-size: 13px; margin-bottom: 8px; }
          .value { font-size: 18px; font-weight: 700; overflow-wrap: anywhere; }
          .ok { color: #047857; }
          pre { white-space: pre-wrap; background: #0f172a; color: #e2e8f0; border-radius: 8px; padding: 16px; overflow-wrap: anywhere; }
        </style>
      </head>
      <body>
        <main>
          <section class="hero">
            <h1>头部 CT 报告 / EMR 归档证据</h1>
            <div class="sub">由 Project2 正常业务链路触发，报告服务发布后写入 EMR 服务。</div>
            <div class="grid">
              <div class="card"><span class="label">报告服务状态</span><span class="value ok">${summary.report_service_status}</span></div>
              <div class="card"><span class="label">EMR 状态</span><span class="value ok">${summary.emr_status}</span></div>
              <div class="card"><span class="label">报告 ID</span><span class="value">${summary.report_service_id}</span></div>
              <div class="card"><span class="label">归档文档号</span><span class="value">${summary.emr_document_id}</span></div>
            </div>
            <pre>${JSON.stringify(emrReport, null, 2)}</pre>
          </section>
        </main>
      </body>
    </html>
  `)
}

const renderReportReleaseEvidence = async (page: Page, summary: HeadCtE2ESummary, report: any) => {
  await page.setContent(`
    <!doctype html>
    <html lang="zh-CN">
      <head>
        <meta charset="utf-8" />
        <style>
          body { margin: 0; font-family: "Microsoft YaHei", Arial, sans-serif; background: #f4f7fb; color: #1f2937; }
          main { max-width: 1120px; margin: 32px auto; padding: 0 24px; }
          .hero { background: #ffffff; border: 1px solid #d9e2ef; border-radius: 8px; padding: 24px; box-shadow: 0 8px 24px rgba(15,23,42,.08); }
          h1 { margin: 0 0 6px; font-size: 26px; }
          .sub { color: #64748b; margin-bottom: 22px; }
          .grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-bottom: 20px; }
          .card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; min-height: 86px; }
          .label { display: block; color: #64748b; font-size: 13px; margin-bottom: 8px; }
          .value { font-size: 18px; font-weight: 700; overflow-wrap: anywhere; }
          .ok { color: #047857; }
          .section { margin-top: 14px; padding: 16px; border: 1px solid #e2e8f0; border-radius: 8px; background: #ffffff; }
          h2 { margin: 0 0 8px; font-size: 16px; }
          p { line-height: 1.7; white-space: pre-wrap; }
        </style>
      </head>
      <body>
        <main>
          <section class="hero">
            <h1>头部 CT 报告发布证据</h1>
            <div class="sub">由 Project2 正常业务链路生成，经过报告服务状态机后发布。</div>
            <div class="grid">
              <div class="card"><span class="label">报告状态</span><span class="value ok">${report.status}</span></div>
              <div class="card"><span class="label">版本</span><span class="value">${report.version_number}</span></div>
              <div class="card"><span class="label">报告 ID</span><span class="value">${summary.report_service_id}</span></div>
              <div class="card"><span class="label">关联检查</span><span class="value">${report.accession_number || report.study_id}</span></div>
            </div>
            <div class="section"><h2>影像所见</h2><p>${report.findings || ''}</p></div>
            <div class="section"><h2>诊断意见</h2><p>${report.impression || ''}</p></div>
            <div class="section"><h2>建议与限制</h2><p>${report.recommendations || ''}</p></div>
          </section>
        </main>
      </body>
    </html>
  `)
}

test.describe('Head CT normal workflow screenshot evidence', () => {
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
    await expect(page.getByText('报告ID：')).toBeVisible({ timeout: 20_000 })
    await assertNoVisibleError(page, issues)
    await screenshot(page, '03-ai-assisted-conclusion-and-report')

    const releasedReportResponse = await page.request.get(`${reportBaseUrl}/api/v1/reports/${summary.report_service_id}`, {
      headers: { 'X-Actor-Id': 'doctor-reporting-001', 'X-Actor-Role': 'reporting_doctor' },
    })
    expect(releasedReportResponse.ok()).toBeTruthy()
    const releasedReportPayload = await releasedReportResponse.json()
    expect(releasedReportPayload.report.status).toBe('released')
    await renderReportReleaseEvidence(page, summary, releasedReportPayload.report)
    await screenshot(page, '04-report-released')

    const emrResponse = await page.request.get(`${emrBaseUrl}/api/v1/diagnostic-reports/${summary.emr_document_id}`, {
      headers: { Authorization: `Bearer ${emrToken}` },
    })
    expect(emrResponse.ok()).toBeTruthy()
    const emrPayload = await emrResponse.json()
    await renderEmrArchiveEvidence(page, summary, emrPayload.report)
    await screenshot(page, '05-emr-archive')
  })
})
