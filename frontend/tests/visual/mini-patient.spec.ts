import { expect, test, type Page } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

const screenshotDir = path.resolve('visual-results', 'mini-patient')

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
  return user
}

const assertCleanPage = async (page: Page, issues: RuntimeIssue[]) => {
  await page.waitForLoadState('domcontentloaded')
  await page.waitForTimeout(700)
  await expect(page.locator('.van-toast--fail')).toHaveCount(0)
  await expect(page.locator('.el-message--error')).toHaveCount(0)
  await expect(page.getByText(/Request failed|Internal Server Error|服务器内部错误|登录失败|加载失败/)).toHaveCount(0)
  expect(issues, JSON.stringify(issues, null, 2)).toEqual([])
}

test.describe('mini patient mobile app', () => {
  test('mirrors patient web workflows on a mobile-sized entry', async ({ page }) => {
    test.skip(test.info().project.name !== 'mobile-chrome', 'mini-patient is a mobile acceptance flow')
    const issues = attachRuntimeGuards(page)
    await loginPatient(page)

    const routes = [
      ['/mini-patient', /\/mini-patient$/],
      ['/mini-patient/ai', /\/mini-patient\/ai/],
      ['/mini-patient/appointment', /\/mini-patient\/appointment/],
      ['/mini-patient/records', /\/mini-patient\/records/],
      ['/mini-patient/orders', /\/mini-patient\/orders/],
      ['/mini-patient/profile', /\/mini-patient\/profile/],
    ] as const

    for (const [route, pattern] of routes) {
      issues.length = 0
      await page.goto(route, { waitUntil: 'domcontentloaded' })
      await expect(page).toHaveURL(pattern)
      await assertCleanPage(page, issues)
      await expect(page.locator('[data-testid="mini-patient-shell"]')).toBeVisible()
      await screenshot(page, route.replace('/mini-patient', 'home').replace(/\//g, '-'))
    }
  })
})
