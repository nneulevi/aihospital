import { expect, test, type Page } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

const screenshotDir = path.resolve('visual-results', 'billing-drug-user-entry')

const ensureDir = () => fs.mkdirSync(screenshotDir, { recursive: true })

const screenshot = async (page: Page, name: string) => {
  ensureDir()
  await page.screenshot({
    path: path.join(screenshotDir, `${test.info().project.name}-${name}.png`),
    fullPage: true,
  })
}

const loginAs = async (page: Page, username: string, role: string) => {
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
  return user.token as string
}

const assertClean = async (page: Page) => {
  await page.waitForLoadState('domcontentloaded')
  await page.waitForTimeout(800)
  await expect(page.locator('.el-message--error')).toHaveCount(0)
  await expect(page.locator('.van-toast--fail')).toHaveCount(0)
  await expect(page.getByText(/Request failed|Internal Server Error|服务器内部错误|加载失败|undefined|null/)).toHaveCount(0)
}

const devDataPattern = /User Logic|Extended|E2E|项目验收|验收|测试|purchase|monthly check|acceptance refund/

const assertNoDevDataVisible = async (page: Page) => {
  await expect(page.locator('body')).not.toContainText(devDataPattern)
}

const assertApiHasNoDevData = async (page: Page, token: string, url: string) => {
  const response = await page.request.get(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  expect(response.ok(), `${url} should be ok`).toBeTruthy()
  const payload = JSON.stringify(await response.json())
  expect(payload, `${url} should not expose development/test data`).not.toMatch(devDataPattern)
}

const assertReadableToast = async (page: Page, text: RegExp) => {
  const toast = page.locator('.van-toast').filter({ hasText: text }).first()
  await expect(toast).toBeVisible()
  const style = await toast.evaluate((element) => {
    const computed = window.getComputedStyle(element)
    return {
      color: computed.color,
      backgroundColor: computed.backgroundColor,
      opacity: computed.opacity,
    }
  })
  expect(style.color).toBe('rgb(255, 255, 255)')
  expect(style.backgroundColor).not.toBe('rgb(255, 255, 255)')
  expect(style.backgroundColor).not.toBe('rgba(0, 0, 0, 0)')
  expect(Number(style.opacity)).toBeGreaterThan(0.8)
}

test.describe('billing, refund and drug inventory user-entry evidence', () => {
  test('admin reaches finance and drug modules from role home by clicking visible navigation', async ({ page }) => {
    const token = await loginAs(page, 'admin', 'ADMIN')

    await page.goto('/admin', { waitUntil: 'domcontentloaded' })
    await assertClean(page)
    await screenshot(page, '01-admin-home')

    await page.locator('.van-tabbar-item').filter({ hasText: '收费' }).click()
    await expect(page).toHaveURL(/\/admin\/finance/)
    await assertClean(page)
    await expect(page.getByText('门诊收费')).toBeVisible()
    await screenshot(page, '02-admin-finance-charge')

    await page.getByRole('tab', { name: '门诊退费' }).click()
    await assertClean(page)
    await expect(page.getByText('确认退费')).toBeVisible()
    await screenshot(page, '03-admin-finance-refund')

    await page.getByRole('tab', { name: '收费记录' }).click()
    await page.getByRole('button', { name: '查询' }).click()
    await assertClean(page)
    await screenshot(page, '04-admin-finance-records')

    await page.getByRole('tab', { name: '日结统计' }).click()
    await page.getByRole('button', { name: '查询日结' }).click()
    await assertClean(page)
    await screenshot(page, '05-admin-finance-summary')

    await page.locator('.van-tabbar-item').filter({ hasText: '药房' }).click()
    await expect(page).toHaveURL(/\/admin\/drug/)
    await assertClean(page)
    await assertNoDevDataVisible(page)
    await assertApiHasNoDevData(page, token, '/api/admin/drug/pending-dispense')
    await assertApiHasNoDevData(page, token, '/api/admin/drug/pending-refund')
    await expect(page.getByText('药品库存')).toBeVisible()
    await screenshot(page, '06-admin-drug-inventory')

    await page.getByRole('button', { name: '药房库存' }).click()
    await assertReadableToast(page, /药房库存加载完成，共 \d+ 条/)
    await screenshot(page, '06b-admin-drugstore-inventory-toast')
    await assertClean(page)
    await assertNoDevDataVisible(page)
    await screenshot(page, '06b-admin-drugstore-inventory-loaded')

    await page.getByRole('tab', { name: '发药' }).click()
    await assertClean(page)
    await assertNoDevDataVisible(page)
    await expect(page.getByText('刷新待发药处方')).toBeVisible()
    await screenshot(page, '07-admin-drug-dispense')

    await page.getByRole('tab', { name: '退药' }).click()
    await assertClean(page)
    await assertNoDevDataVisible(page)
    await expect(page.getByText('刷新可退药处方')).toBeVisible()
    await screenshot(page, '08-admin-drug-refund')
  })

  test('pharmacist sees inventory, stock operation entry and stock records in workbench', async ({ page }) => {
    const token = await loginAs(page, 'pharmacist', 'PHARMACIST')

    await page.goto('/drugstore', { waitUntil: 'domcontentloaded' })
    await assertClean(page)
    await assertNoDevDataVisible(page)
    await assertApiHasNoDevData(page, token, '/api/drugstore/inventory?pageNum=1&pageSize=50')
    await assertApiHasNoDevData(page, token, '/api/drugstore/stock/records?pageNum=1&pageSize=50')
    await expect(page.getByText('药房工作台')).toBeVisible()
    await screenshot(page, '09-drugstore-home')

    await page.getByRole('button', { name: '刷新' }).click()
    await assertClean(page)
    await assertNoDevDataVisible(page)
    await screenshot(page, '10-drugstore-inventory-refreshed')

    const firstFlowButton = page.locator('.el-table__body-wrapper button').nth(2)
    if (await firstFlowButton.count()) {
      await firstFlowButton.click()
      await assertClean(page)
      await assertNoDevDataVisible(page)
      await screenshot(page, '11-drugstore-stock-records')
    }

    await page.getByRole('button', { name: '低库存预警' }).click()
    await assertClean(page)
    await assertNoDevDataVisible(page)
    await assertApiHasNoDevData(page, token, '/api/drugstore/stock/alerts?threshold=10&pageNum=1&pageSize=50')
    await screenshot(page, '12-drugstore-low-stock')
  })
})
