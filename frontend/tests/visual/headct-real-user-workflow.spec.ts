import { expect, test, type Page } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

const rootDir = path.resolve('..')
const screenshotDir = path.resolve('visual-results', 'headct-real-user-workflow')
const sampleCtPath = path.resolve(rootDir, 'testdata', 'headct', 'head_ct_positive_case.nii.gz')
const reportBaseUrl = process.env.REPORT_BASE_URL || 'http://127.0.0.1:8030'
const emrBaseUrl = process.env.EMR_BASE_URL || 'http://127.0.0.1:8040'
const emrToken = process.env.HEADCT_LOCAL_EMR_TOKEN || 'headct-local-emr-change-before-production'

type RuntimeIssue = { type: 'console' | 'pageerror' | 'response'; message: string }

const screenshot = async (page: Page, name: string) => {
  fs.mkdirSync(screenshotDir, { recursive: true })
  await page.locator('.van-toast, .el-message, #toast:not(.hidden)').waitFor({ state: 'detached', timeout: 5_000 }).catch(() => {})
  await page.waitForTimeout(300)
  await page.screenshot({ path: path.join(screenshotDir, `${test.info().project.name}-${name}.png`), fullPage: true })
}

const attachRuntimeGuards = (page: Page) => {
  const issues: RuntimeIssue[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') issues.push({ type: 'console', message: message.text() })
  })
  page.on('pageerror', (error) => issues.push({ type: 'pageerror', message: error.message }))
  page.on('response', (response) => {
    const url = response.url()
    if (response.status() >= 500 && !url.includes('/favicon')) {
      issues.push({ type: 'response', message: `${response.status()} ${url}` })
    }
  })
  return issues
}

const assertCleanPage = async (page: Page, issues: RuntimeIssue[]) => {
  await page.waitForLoadState('domcontentloaded')
  await page.waitForTimeout(700)
  await expect(page.locator('.el-message--error')).toHaveCount(0)
  await expect(page.locator('.van-toast--fail')).toHaveCount(0)
  await expect(page.getByText(/Request failed|Internal Server Error|服务器内部错误|登录失败|加载失败|影像上传失败|AI识别失败|AI报告生成失败|请求失败/)).toHaveCount(0)
  expect(issues, JSON.stringify(issues, null, 2)).toEqual([])
}

const writeAuth = async (page: Page, token: string, user: unknown) => {
  await page.addInitScript(({ token, user }) => {
    window.localStorage.setItem('token', token)
    window.localStorage.setItem('user', JSON.stringify(user))
  }, { token, user })
}

const loginDoctor = async (page: Page) => {
  const response = await page.request.post('/api/auth/login', {
    data: { username: 'doctor', password: '123456', loginType: 'DOCTOR' },
  })
  expect(response.ok()).toBeTruthy()
  const user = await response.json()
  expect(user.token).toBeTruthy()
  await writeAuth(page, user.token, user)
  return user
}

const findOrReceivePatient = async (page: Page, doctorId: number) => {
  const active = await page.request.get('/api/doctor/patients', {
    params: { doctorId, visitState: 'DOCTOR_RECEIVED', pageNum: 1, pageSize: 1 },
  })
  expect(active.ok()).toBeTruthy()
  let payload = await active.json()
  if (payload.records?.[0]?.registerId) return payload.records[0]

  const pending = await page.request.get('/api/doctor/patients', {
    params: { doctorId, visitState: 'REGISTERED', pageNum: 1, pageSize: 1 },
  })
  expect(pending.ok()).toBeTruthy()
  payload = await pending.json()
  const patient = payload.records?.[0]
  if (!patient?.registerId) {
    throw new Error('没有可用于用户视角验收的待诊或就诊中患者，请先在患者端完成一次真实挂号。')
  }
  const receive = await page.request.put(`/api/doctor/patients/${patient.registerId}/receive`)
  expect(receive.ok()).toBeTruthy()
  return patient
}

const createHeadCtCheckRequest = async (page: Page, registerId: number) => {
  const checkInfo = `头颅CT真实上传验收-${Date.now()}`
  const create = await page.request.post('/api/doctor/check-request', {
    data: {
      registerId,
      items: [{ medicalTechnologyId: 1, checkInfo, checkPosition: '头部' }],
    },
  })
  expect(create.ok()).toBeTruthy()

  const results = await page.request.get(`/api/doctor/check-results/${registerId}`)
  expect(results.ok()).toBeTruthy()
  const payload = await results.json()
  const check = (payload.checkRequests || []).find((item: any) => item.checkInfo === checkInfo)
  if (!check?.id) throw new Error(`检查申请创建后未能在结果列表中找到: ${checkInfo}`)
  return { checkRequestId: check.id as number, checkInfo }
}

const reportHeaders = (role = 'reporting_doctor', actor = 'doctor-reporting-001') => ({
  'X-Actor-Id': actor,
  'X-Actor-Role': role,
})

const findReportByCheckRequest = async (page: Page, checkRequestId: number) => {
  const response = await page.request.get(`${reportBaseUrl}/api/v1/reports`, {
    headers: reportHeaders(),
  })
  expect(response.ok()).toBeTruthy()
  const payload = await response.json()
  const report = (payload.reports || []).find((item: any) =>
    item.accession_number === `ACC-CHECK-${checkRequestId}` || item.study_id === `CHECK-${checkRequestId}`,
  )
  if (!report?.id) throw new Error(`报告服务中未找到检查申请 ${checkRequestId} 对应的报告`)
  return report
}

test.describe('Head CT real user workflow', () => {
  test('doctor uploads CT, runs AI, reviews report workspace, releases and verifies EMR archive', async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== 'desktop-chrome', '真实用户 CT 流程只在桌面端执行一次。')
    test.setTimeout(420_000)
    expect(fs.existsSync(sampleCtPath)).toBeTruthy()

    const issues = attachRuntimeGuards(page)
    const doctor = await loginDoctor(page)
    const patient = await findOrReceivePatient(page, doctor.doctorId || doctor.employeeId || 1)
    const { checkRequestId } = await createHeadCtCheckRequest(page, patient.registerId)

    await page.goto(`/doctor/visit?registerId=${patient.registerId}&name=${encodeURIComponent(patient.patientName || '真实CT验收患者')}`, { waitUntil: 'domcontentloaded' })
    await page.getByRole('tab', { name: '结果' }).click()
    await page.getByRole('button', { name: '刷新结果' }).click()
    await expect(page.getByText('AI 影像识别与报告生成')).toBeVisible()
    await page.getByPlaceholder('选择或输入检查申请ID').fill(String(checkRequestId))
    await page.locator('input[type="file"]').setInputFiles(sampleCtPath)
    await screenshot(page, '01-doctor-selected-real-ct-file')

    const [uploadResponse] = await Promise.all([
      page.waitForResponse((response) => response.url().includes('/api/ai/image/upload') && response.request().method() === 'POST', { timeout: 60_000 }),
      page.getByRole('button', { name: '上传影像' }).click(),
    ])
    expect(uploadResponse.ok()).toBeTruthy()
    await expect(page.getByPlaceholder('上传后自动填入，也可手动输入')).toHaveValue(/^\d+$/)
    await assertCleanPage(page, issues)
    await screenshot(page, '02-upload-success')

    const [analysisResponse] = await Promise.all([
      page.waitForResponse((response) => response.url().includes('/api/ai/image/analyze') && response.request().method() === 'POST', { timeout: 240_000 }),
      page.getByRole('button', { name: 'AI识别' }).click(),
    ])
    expect(analysisResponse.ok()).toBeTruthy()
    const analysisPayload = await analysisResponse.json()
    expect(analysisPayload.previewUrls && Object.keys(analysisPayload.previewUrls).length).toBeGreaterThan(0)
    expect(analysisPayload.aiImagingStatus?.lesionModel?.checkpointFallbackUsed ?? analysisPayload.aiImagingStatus?.lesion_model?.checkpoint_fallback_used).not.toBeTruthy()
    const lesionModel = analysisPayload.aiImagingStatus?.lesionModel || analysisPayload.aiImagingStatus?.lesion_model || {}
    expect(lesionModel.outputsSegmentation ?? lesionModel.outputs_segmentation).toBeTruthy()
    expect(lesionModel.maskUrl || lesionModel.mask_url).toBeTruthy()
    expect(Object.keys(analysisPayload.previewUrls).some((key) => key.startsWith('lesion_'))).toBeTruthy()
    const analysisText = JSON.stringify(analysisPayload)
    expect(analysisText).not.toContain('低置信阴性')
    expect(analysisText).not.toContain('high_negative')
    await expect(page.getByText('影像可视化输出')).toBeVisible({ timeout: 20_000 })
    await expect(page.locator('.preview-item img')).toHaveCount(Object.keys(analysisPayload.previewUrls).length)
    await expect(page.getByText('病灶轴位')).toBeVisible()
    await expect(page.getByText('病灶模型', { exact: true })).toBeVisible()
    await expect(page.getByText('AI结论')).toBeVisible()
    await assertCleanPage(page, issues)
    await screenshot(page, '03-ai-recognition-with-visual-output')

    const [reportResponse] = await Promise.all([
      page.waitForResponse((response) => response.url().includes('/api/ai/report/generate') && response.request().method() === 'POST', { timeout: 120_000 }),
      page.getByRole('button', { name: '生成报告' }).click(),
    ])
    expect(reportResponse.ok()).toBeTruthy()
    await expect(page.getByText('报告ID')).toBeVisible({ timeout: 20_000 })
    await assertCleanPage(page, issues)
    await screenshot(page, '04-project2-ai-report-generated')

    const report = await findReportByCheckRequest(page, checkRequestId)
    page.on('dialog', (dialog) => dialog.accept())
    await page.goto('/doctor', { waitUntil: 'domcontentloaded' })
    await page.getByText('CT 报告工作台', { exact: true }).click()
    await expect(page).toHaveURL(/\/doctor\/headct-reports/)
    const reportWorkspace = page.frameLocator('iframe[title="头部 CT 检查报告工作台"]')
    await expect(reportWorkspace.getByText('头部 CT 检查报告')).toBeVisible({ timeout: 20_000 })
    await reportWorkspace.locator('#actorId').fill('doctor-reporting-001')
    await reportWorkspace.locator('#actorRole').selectOption('reporting_doctor')
    await reportWorkspace.getByRole('button', { name: '刷新' }).click()
    await reportWorkspace.getByText(report.accession_number || report.study_id).first().click()
    await expect(reportWorkspace.locator('#reportContent')).toBeVisible()
    await expect(reportWorkspace.locator('#findings')).not.toHaveValue('')
    await expect(reportWorkspace.getByRole('button', { name: 'AI 解读' })).toBeVisible()
    await expect(reportWorkspace.getByText('AI 辅助结论')).toBeVisible()
    await expect(reportWorkspace.getByText('病灶阳性置信度')).toBeVisible()
    await expect(reportWorkspace.getByText('技术详情：原始 AI 结果')).toHaveCount(0)
    const visibleAiText = await reportWorkspace.locator('#detailPanel').innerText()
    expect(visibleAiText).not.toContain('"quality_control"')
    expect(visibleAiText).not.toContain('"lesion_analysis"')
    expect(visibleAiText).not.toContain('checkpoint')
    expect(visibleAiText).not.toContain('fallback')
    expect(visibleAiText).not.toContain('低置信阴性')
    await screenshot(page, '05-report-workbench-draft')

    await reportWorkspace.getByRole('button', { name: '提交审核', exact: true }).click()
    await expect(reportWorkspace.locator('#statusBadge')).toHaveText('待审核', { timeout: 20_000 })
    await reportWorkspace.locator('#actorRole').selectOption('reviewing_doctor')
    await reportWorkspace.getByRole('button', { name: '审核通过', exact: true }).click()
    await expect(reportWorkspace.locator('#statusBadge')).toHaveText('已通过', { timeout: 20_000 })
    await reportWorkspace.locator('#actorRole').selectOption('signing_doctor')
    await reportWorkspace.getByRole('button', { name: '签署', exact: true }).click()
    await expect(reportWorkspace.locator('#statusBadge')).toHaveText('已签署', { timeout: 20_000 })
    await reportWorkspace.getByRole('button', { name: '发布', exact: true }).click()
    await expect(reportWorkspace.locator('#statusBadge')).toHaveText('已发布', { timeout: 20_000 })

    const dispatch = await page.request.post(`${reportBaseUrl}/api/v1/integrations/emr/dispatch`, {
      headers: reportHeaders('integration_service', 'emr-bridge'),
    })
    expect(dispatch.ok()).toBeTruthy()
    await reportWorkspace.getByRole('button', { name: '刷新' }).click()
    await reportWorkspace.locator('.report-item', { hasText: report.accession_number || report.study_id }).first().click()
    await expect(reportWorkspace.locator('#reportContent')).toBeVisible({ timeout: 20_000 })
    await expect(reportWorkspace.locator('#emptyState')).toBeHidden()
    await expect(reportWorkspace.locator('#studyMeta')).toContainText('EMR DR-', { timeout: 20_000 })
    await screenshot(page, '06-report-released-and-emr-archived')

    const refreshed = await page.request.get(`${reportBaseUrl}/api/v1/reports/${report.id}`, { headers: reportHeaders() })
    expect(refreshed.ok()).toBeTruthy()
    const refreshedPayload = await refreshed.json()
    const documentId = refreshedPayload.report.external_document_id
    expect(documentId).toBeTruthy()
    const emr = await page.request.get(`${emrBaseUrl}/api/v1/diagnostic-reports/${documentId}`, {
      headers: { Authorization: `Bearer ${emrToken}` },
    })
    expect(emr.ok()).toBeTruthy()
    const emrPayload = await emr.json()
    expect(emrPayload.report.status).toBe('final')
    await assertCleanPage(page, issues)
  })
})
