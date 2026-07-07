import { expect, test, type Page } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

const screenshotDir = path.resolve('visual-results', 'toast-contrast')

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
}

const parseRgb = (value: string) => {
  const match = value.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([0-9.]+))?\)/)
  if (!match) return null
  return {
    r: Number(match[1]),
    g: Number(match[2]),
    b: Number(match[3]),
    a: match[4] === undefined ? 1 : Number(match[4]),
  }
}

const relativeLuminance = (rgb: { r: number; g: number; b: number }) => {
  const channel = [rgb.r, rgb.g, rgb.b].map((value) => {
    const normalized = value / 255
    return normalized <= 0.03928 ? normalized / 12.92 : ((normalized + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * channel[0] + 0.7152 * channel[1] + 0.0722 * channel[2]
}

const contrastRatio = (fg: { r: number; g: number; b: number }, bg: { r: number; g: number; b: number }) => {
  const foreground = relativeLuminance(fg)
  const background = relativeLuminance(bg)
  const lighter = Math.max(foreground, background)
  const darker = Math.min(foreground, background)
  return (lighter + 0.05) / (darker + 0.05)
}

const assertFloatingNoticeReadable = async (page: Page, locatorSelector: string, label: string) => {
  const locator = page.locator(locatorSelector).first()
  await expect(locator, `${label} should be visible`).toBeVisible()
  const style = await locator.evaluate((element) => {
    const computed = window.getComputedStyle(element)
    const textElement = element.querySelector('.van-toast__text, .el-message__content') || element
    const textStyle = window.getComputedStyle(textElement)
    return {
      color: textStyle.color,
      backgroundColor: computed.backgroundColor,
      opacity: computed.opacity,
      text: element.textContent?.trim() || '',
    }
  })
  const fg = parseRgb(style.color)
  const bg = parseRgb(style.backgroundColor)
  expect(fg, `${label} text color should be rgb`).toBeTruthy()
  expect(bg, `${label} background color should be rgb`).toBeTruthy()
  expect(bg!.a, `${label} background must not be transparent`).toBeGreaterThan(0.8)
  expect(style.backgroundColor, `${label} background must not be white`).not.toBe('rgb(255, 255, 255)')
  expect(contrastRatio(fg!, bg!), `${label} contrast`).toBeGreaterThanOrEqual(4.5)
}

test.describe('floating notice contrast', () => {
  test('Vant toast uses readable floating style', async ({ page }) => {
    await loginAs(page, 'admin', 'ADMIN')
    await page.goto('/admin/drug', { waitUntil: 'domcontentloaded' })
    await page.getByRole('tab', { name: '发药' }).click()
    await page.getByRole('button', { name: '确认发药' }).click()
    await assertFloatingNoticeReadable(page, '.van-toast', 'Vant toast')
    await screenshot(page, 'vant-toast-readable')
  })

  test('Element message uses readable floating style', async ({ page }) => {
    await loginAs(page, 'pharmacist', 'PHARMACIST')
    await page.goto('/drugstore', { waitUntil: 'domcontentloaded' })
    await page.getByRole('button', { name: '低库存预警' }).click()
    await assertFloatingNoticeReadable(page, '.el-message', 'Element message')
    await screenshot(page, 'element-message-readable')
  })
})
