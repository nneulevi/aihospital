import { expect, test, type Page } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

const screenshotDir = path.resolve('visual-results', 'patient-medical-booking-catalog')
const devDataPattern = /User Logic|Extended|E2E|项目验收|验收|测试/

const ensureDir = () => fs.mkdirSync(screenshotDir, { recursive: true })

const screenshot = async (page: Page, name: string) => {
  ensureDir()
  await page.screenshot({
    path: path.join(screenshotDir, `${test.info().project.name}-${name}.png`),
    fullPage: true,
  })
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

const assertBookingCatalog = async (page: Page, url: string, title: string, expectedItem: string, screenshotName: string) => {
  await page.goto(url, { waitUntil: 'domcontentloaded' })
  await expect(page.getByText(title).first()).toBeVisible()
  await expect(page.locator('body')).not.toContainText(devDataPattern)
  const itemButtons = page.locator('.item-grid button')
  await expect(itemButtons).toHaveCount(1)
  await expect(itemButtons.first()).toContainText(expectedItem)
  await screenshot(page, screenshotName)
}

test.describe('patient medical booking catalog', () => {
  test('exam and lab booking pages expose concise non-duplicated catalogs', async ({ page }) => {
    await loginPatient(page)
    await assertBookingCatalog(page, '/patient/exam-booking', '检查预约', '头颅CT平扫', 'exam-booking-catalog')
    await assertBookingCatalog(page, '/patient/lab-booking', '检验预约', '血常规', 'lab-booking-catalog')
  })
})
