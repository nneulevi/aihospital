import { expect, test, type Page } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

type StaffRole = 'DOCTOR' | 'ADMIN' | 'MEDICAL_TECH' | 'PHARMACIST'

const screenshotDir = path.resolve('visual-results')
const text = {
  mine: '\u6211\u7684',
  records: '\u5c31\u8bca\u8bb0\u5f55',
  unpaid: '\u5f85\u7f34\u8d39',
  pending: '\u5f85\u8bca',
  consulting: '\u5c31\u8bca\u4e2d',
  todayFinished: '\u4eca\u65e5\u5df2\u63a5\u8bca',
  pendingCheck: '\u5f85\u5904\u7406\u68c0\u67e5',
  todayRegistration: '\u4eca\u65e5\u6302\u53f7',
  stockAlert: '\u5e93\u5b58\u9884\u8b66',
  pharmacyManage: '\u836f\u623f\u7ba1\u7406',
  addSource: '\u65b0\u589e\u53f7\u6e90',
  sourceId: '\u53f7\u6e90ID',
  medicalTechWorkbench: '\u533b\u6280\u5de5\u4f5c\u53f0',
  reportEntry: '\u62a5\u544a\u5f55\u5165',
  aiInterpret: 'AI\u89e3\u8bfb',
  drugstoreWorkbench: '\u836f\u623f\u5de5\u4f5c\u53f0',
  drugId: '\u836f\u54c1ID',
  lowStock: '\u4f4e\u5e93\u5b58\u9884\u8b66',
  aiInquiry: 'AI \u667a\u80fd\u95ee\u8bca',
  startAnalysis: '\u5f00\u59cb\u5206\u6790',
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

const waitForPage = async (page: Page) => {
  await page.waitForLoadState('domcontentloaded')
  await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => undefined)
}

const expectNoVisibleError = async (page: Page) => {
  const errorPattern = /\u670d\u52a1\u5668\u5185\u90e8\u9519\u8bef|Request failed|status 500|\u767b\u5f55\u5931\u8d25|\u52a0\u8f7d\u5931\u8d25|\u83b7\u53d6\u5931\u8d25|AI\u5206\u6790\u5931\u8d25|AI\u5efa\u8bae\u83b7\u53d6\u5931\u8d25/
  await expect(page.getByText(errorPattern)).toHaveCount(0)
}

const loginStaff = async (page: Page, role: StaffRole, username: string) => {
  const response = await page.request.post('/api/auth/login', {
    data: { username, password: '123456', loginType: role },
  })
  expect(response.ok()).toBeTruthy()
  const user = await response.json()
  expect(user.token).toBeTruthy()
  expect(user.roleType || user.loginType || role).toBeTruthy()
  await page.addInitScript(({ token, user }) => {
    window.localStorage.setItem('token', token)
    window.localStorage.setItem('user', JSON.stringify(user))
  }, { token: user.token, user })
}

const loginPatient = async (page: Page) => {
  const response = await page.request.post('/api/auth/login', {
    data: { username: '13800001111', password: '123456', loginType: 'PATIENT' },
  })
  expect(response.ok()).toBeTruthy()
  const user = await response.json()
  expect(user.token).toBeTruthy()
  expect(user.patientId).toBeTruthy()
  await page.addInitScript(({ token, user }) => {
    window.localStorage.setItem('token', token)
    window.localStorage.setItem('user', JSON.stringify(user))
  }, { token: user.token, user })
}

test.describe('Project2 visual business acceptance', () => {
  test('patient profile maps dashboard data and navigation', async ({ page }) => {
    await loginPatient(page)
    await page.goto('/patient/profile')
    await waitForPage(page)
    await expect(page.getByText(text.mine).first()).toBeVisible()
    await expect(page.getByText(text.records)).toBeVisible()
    await expect(page.getByText(text.unpaid).first()).toBeVisible()
    await expect(page.locator('.summary-value').first()).not.toHaveText('--')
    await expectNoVisibleError(page)
    await screenshot(page, 'patient-profile')
  })

  test('patient mini app exposes appointment, records and AI inquiry', async ({ page }) => {
    await loginPatient(page)
    await page.goto('/mini-patient')
    await waitForPage(page)
    await expect(page.getByText(text.records)).toBeVisible()
    await expect(page.getByText(text.unpaid)).toBeVisible()
    await page.goto('/mini-patient/ai')
    await waitForPage(page)
    await expect(page.getByText(text.aiInquiry).first()).toBeVisible()
    await expect(page.getByRole('button', { name: text.startAnalysis })).toBeVisible()
    await expectNoVisibleError(page)
    await screenshot(page, 'mini-patient-ai')
  })

  test('doctor dashboard shows queues and clinical workbench entry', async ({ page }) => {
    await loginStaff(page, 'DOCTOR', 'doctor')
    await page.goto('/doctor')
    await waitForPage(page)
    await expect(page.getByText(text.pending, { exact: true }).first()).toBeVisible()
    await expect(page.getByText(text.consulting, { exact: true }).first()).toBeVisible()
    await expect(page.getByText(text.todayFinished).first()).toBeVisible()
    await expect(page.getByText(text.pendingCheck).first()).toBeVisible()
    await expectNoVisibleError(page)
    await screenshot(page, 'doctor-dashboard')
  })

  test('admin dashboard exposes finance, pharmacy and schedule source modules', async ({ page }) => {
    await loginStaff(page, 'ADMIN', 'admin')
    await page.goto('/admin')
    await waitForPage(page)
    await expect(page.getByText(text.todayRegistration)).toBeVisible()
    await expect(page.getByText(text.stockAlert)).toBeVisible()
    await expect(page.getByText(text.pharmacyManage)).toBeVisible()
    await page.goto('/admin/schedule-sources')
    await waitForPage(page)
    await expect(page.getByText(text.addSource)).toBeVisible()
    await expect(page.getByText(text.sourceId)).toBeVisible()
    await expectNoVisibleError(page)
    await screenshot(page, 'admin-schedule-sources')
  })

  test('medical tech workbench displays executable task workflow', async ({ page }) => {
    await loginStaff(page, 'MEDICAL_TECH', 'medicaltech')
    await page.goto('/medical-tech')
    await waitForPage(page)
    await expect(page.getByText(text.medicalTechWorkbench)).toBeVisible()
    await expect(page.getByText(text.reportEntry)).toBeVisible()
    await expect(page.getByRole('button', { name: text.aiInterpret }).first()).toBeVisible()
    await expectNoVisibleError(page)
    await screenshot(page, 'medical-tech-workbench')
  })

  test('drugstore workbench displays inventory and stock operations', async ({ page }) => {
    await loginStaff(page, 'PHARMACIST', 'pharmacist')
    await page.goto('/drugstore')
    await waitForPage(page)
    await expect(page.getByText(text.drugstoreWorkbench)).toBeVisible()
    await expect(page.getByText(text.drugId)).toBeVisible()
    await expect(page.getByText(text.lowStock)).toBeVisible()
    await expectNoVisibleError(page)
    await screenshot(page, 'drugstore-workbench')
  })
})
