import { expect, test, type Page } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

type StaffRole = 'DOCTOR' | 'ADMIN' | 'MEDICAL_TECH' | 'PHARMACIST'

const screenshotDir = path.resolve('visual-results')

type RuntimeIssue = {
  type: 'console' | 'pageerror' | 'response'
  message: string
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

const writeAuth = async (page: Page, token: string, user: unknown) => {
  const payload = { token, user }
  await page.addInitScript(({ token, user }) => {
    window.localStorage.setItem('token', token)
    window.localStorage.setItem('user', JSON.stringify(user))
  }, payload)
  try {
    await page.evaluate(({ token, user }) => {
      window.localStorage.setItem('token', token)
      window.localStorage.setItem('user', JSON.stringify(user))
    }, payload)
  } catch {
    // The first navigation may not have an origin yet; addInitScript covers it.
  }
}

const loginStaff = async (page: Page, role: StaffRole, username: string) => {
  const response = await page.request.post('/api/auth/login', {
    data: { username, password: '123456', loginType: role },
  })
  expect(response.ok()).toBeTruthy()
  const user = await response.json()
  expect(user.token).toBeTruthy()
  await writeAuth(page, user.token, user)
  return user
}

const loginPatient = async (page: Page) => {
  const response = await page.request.post('/api/auth/login', {
    data: { username: '13800001111', password: '123456', loginType: 'PATIENT' },
  })
  expect(response.ok()).toBeTruthy()
  const user = await response.json()
  expect(user.token).toBeTruthy()
  await writeAuth(page, user.token, user)
  return user
}

const firstRecordIdForPatient = async (page: Page, patientId?: number) => {
  const response = await page.request.get('/api/patient/records', {
    params: { patientId, pageNum: 1, pageSize: 1 },
  })
  if (!response.ok()) return undefined
  const payload = await response.json()
  return payload?.records?.[0]?.registerId as number | undefined
}

const firstRegisterIdForDoctor = async (page: Page, doctorId?: number) => {
  const response = await page.request.get('/api/doctor/patients', {
    params: { doctorId: doctorId || 1, pageNum: 1, pageSize: 1 },
  })
  if (!response.ok()) return undefined
  const payload = await response.json()
  return payload?.records?.[0]?.registerId as number | undefined
}

const routeScreenshotName = (route: string) =>
  route.replace(/^\//, '').replace(/[/?=&:]+/g, '-').replace(/-$/, '') || 'root'

const assertNoVisibleError = async (page: Page, issues: RuntimeIssue[]) => {
  await page.waitForLoadState('domcontentloaded')
  await page.waitForTimeout(600)
  await expect(page.locator('.el-message--error')).toHaveCount(0)
  await expect(page.locator('.van-toast--fail')).toHaveCount(0)
  await expect(page.getByText(/Request failed|Internal Server Error|服务器内部错误|登录失败|加载失败/)).toHaveCount(0)
  expect(issues, JSON.stringify(issues, null, 2)).toEqual([])
}

const visitAndAccept = async (
  page: Page,
  route: string,
  expectedPath: RegExp,
  issues: RuntimeIssue[],
) => {
  issues.length = 0
  await page.goto(route, { waitUntil: 'domcontentloaded' })
  await expect(page).toHaveURL(expectedPath)
  await assertNoVisibleError(page, issues)
  await expect(page.locator('body')).toBeVisible()
  await screenshot(page, routeScreenshotName(route))
}

test.describe('Project2 full screenshot-level acceptance', () => {
  test('login entry pages are clean and visually stable', async ({ page }) => {
    const issues = attachRuntimeGuards(page)
    await visitAndAccept(page, '/patient/login', /\/patient\/login/, issues)
    await visitAndAccept(page, '/auth/login', /\/auth\/login/, issues)
  })

  test('patient routes are reachable, clean, and visually captured', async ({ page }) => {
    const issues = attachRuntimeGuards(page)
    const user = await loginPatient(page)
    const recordId = await firstRecordIdForPatient(page, user.patientId)
    const routes = [
      '/patient/ai',
      '/patient/appointment',
      '/patient/appointment/success?registerId=1',
      '/patient/records',
      '/patient/orders',
      '/patient/profile',
    ]
    if (recordId) {
      routes.splice(4, 0, `/patient/record/${recordId}`)
    }
    for (const route of routes) {
      await visitAndAccept(page, route, new RegExp(route.split('?')[0].replace(/\//g, '\\/')), issues)
    }
  })

  test('doctor routes are reachable, clean, and visually captured', async ({ page }) => {
    const issues = attachRuntimeGuards(page)
    const user = await loginStaff(page, 'DOCTOR', 'doctor')
    const registerId = await firstRegisterIdForDoctor(page, user.doctorId)
    const routes = ['/doctor', '/doctor/profile']
    if (registerId) {
      routes.push(`/doctor/visit?registerId=${registerId}&name=VisualPatient`)
    }
    for (const route of routes) {
      await visitAndAccept(page, route, new RegExp(route.split('?')[0].replace(/\//g, '\\/')), issues)
    }
  })

  test('admin routes are reachable, clean, and visually captured', async ({ page }) => {
    const issues = attachRuntimeGuards(page)
    await loginStaff(page, 'ADMIN', 'admin')
    const routes = ['/admin', '/admin/schedule', '/admin/schedule-sources', '/admin/finance', '/admin/drug']
    for (const route of routes) {
      await visitAndAccept(page, route, new RegExp(route.replace(/\//g, '\\/')), issues)
    }
  })

  test('medical tech and drugstore routes are reachable, clean, and visually captured', async ({ page }) => {
    const issues = attachRuntimeGuards(page)
    await loginStaff(page, 'MEDICAL_TECH', 'medicaltech')
    await visitAndAccept(page, '/medical-tech', /\/medical-tech/, issues)

    await loginStaff(page, 'PHARMACIST', 'pharmacist')
    await visitAndAccept(page, '/drugstore', /\/drugstore/, issues)
  })
})
