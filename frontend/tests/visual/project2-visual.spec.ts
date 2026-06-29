import { expect, test, type Page } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

type StaffRole = 'DOCTOR' | 'ADMIN' | 'MEDICAL_TECH' | 'PHARMACIST'

const screenshotDir = path.resolve('visual-results')

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

const loginStaff = async (page: Page, role: StaffRole, username: string) => {
  const response = await page.request.post('/api/auth/login', {
    data: { username, password: '123456', loginType: role },
  })
  expect(response.ok()).toBeTruthy()
  const user = await response.json()
  expect(user.token).toBeTruthy()
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
  await page.addInitScript(({ token, user }) => {
    window.localStorage.setItem('token', token)
    window.localStorage.setItem('user', JSON.stringify(user))
  }, { token: user.token, user })
}

test.describe('Project2 visual business acceptance', () => {
  test('patient profile maps dashboard data and navigation', async ({ page }) => {
    await loginPatient(page)
    await page.goto('/patient/profile')
    await expect(page.getByText('我的').first()).toBeVisible()
    await expect(page.getByText('就诊记录')).toBeVisible()
    await expect(page.getByText('待缴费')).toBeVisible()
    await expect(page.getByText('待缴金额')).toBeVisible()
    await screenshot(page, 'patient-profile')
  })

  test('doctor dashboard shows queues and clinical workbench entry', async ({ page }) => {
    await loginStaff(page, 'DOCTOR', 'doctor')
    await page.goto('/doctor')
    await expect(page.getByText('待诊', { exact: true }).first()).toBeVisible()
    await expect(page.getByText('就诊中', { exact: true }).first()).toBeVisible()
    await expect(page.getByText('今日已接诊')).toBeVisible()
    await expect(page.getByText('待处理检查')).toBeVisible()
    await screenshot(page, 'doctor-dashboard')
  })

  test('admin dashboard exposes finance, pharmacy and schedule source modules', async ({ page }) => {
    await loginStaff(page, 'ADMIN', 'admin')
    await page.goto('/admin')
    await expect(page.getByText('今日挂号')).toBeVisible()
    await expect(page.getByText('待收费金额')).toBeVisible()
    await expect(page.getByText('药房管理')).toBeVisible()
    await page.goto('/admin/schedule-sources')
    await expect(page.getByText('新增号源')).toBeVisible()
    await expect(page.getByText('号源ID')).toBeVisible()
    await screenshot(page, 'admin-schedule-sources')
  })

  test('medical tech workbench displays executable task workflow', async ({ page }) => {
    await loginStaff(page, 'MEDICAL_TECH', 'medicaltech')
    await page.goto('/medical-tech')
    await expect(page.getByText('医技工作台')).toBeVisible()
    await expect(page.getByText('待执行', { exact: true }).first()).toBeVisible()
    await expect(page.getByText('报告录入')).toBeVisible()
    await expect(page.getByRole('button', { name: 'AI解读' }).first()).toBeVisible()
    await screenshot(page, 'medical-tech-workbench')
  })

  test('drugstore workbench displays inventory and stock operations', async ({ page }) => {
    await loginStaff(page, 'PHARMACIST', 'pharmacist')
    await page.goto('/drugstore')
    await expect(page.getByText('药房工作台')).toBeVisible()
    await expect(page.getByText('处方发药/退药')).toBeVisible()
    await expect(page.getByText('药品ID')).toBeVisible()
    await expect(page.getByText('低库存预警')).toBeVisible()
    await screenshot(page, 'drugstore-workbench')
  })
})
