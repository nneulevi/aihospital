import { expect, test, type Page } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

const outputDir = path.resolve('visual-results', 'fill-and-disabled-coverage')

const ensureOutputDir = () => fs.mkdirSync(outputDir, { recursive: true })

const screenshot = async (page: Page, name: string) => {
  ensureOutputDir()
  await page.screenshot({
    path: path.join(outputDir, `${name}.png`),
    fullPage: true,
  })
}

const resetBrowserState = async (page: Page, entry: string) => {
  await page.goto(entry)
  await page.evaluate(() => {
    localStorage.clear()
    sessionStorage.clear()
  })
  await page.goto(entry)
}

const expectNoUserFacingError = async (page: Page) => {
  const bodyText = await page.locator('body').innerText()
  expect(bodyText).not.toMatch(/Request failed|服务器内部错误|undefined|null|\{[\s\S]*"status"[\s\S]*\}/)
}

const staffLogin = async (page: Page, roleText: string, username: string) => {
  await resetBrowserState(page, '/auth/login')
  await page.getByRole('button', { name: roleText, exact: true }).click()
  await page.getByPlaceholder('用户名').fill(username)
  await page.getByPlaceholder('密码').fill('123456')
}

const patientLogin = async (page: Page) => {
  await resetBrowserState(page, '/patient/login')
  await page.getByPlaceholder('请输入用户名/手机号').fill('13800001111')
  await page.getByPlaceholder('请输入密码').fill('123456')
}

test('填写态、禁用态和筛选态截图补强必须来自正常入口', async ({ page }) => {
  await staffLogin(page, '管理员', 'admin')
  await screenshot(page, '01-staff-login-admin-filled')
  await page.getByRole('button', { name: /^登录$/ }).click()
  await expect(page).toHaveURL(/\/admin/)
  await expectNoUserFacingError(page)
  await page.getByRole('button', { name: /退出/ }).first().click()
  await expect(page.getByText('确定退出管理员工作台吗？')).toBeVisible()
  await screenshot(page, '01b-admin-logout-confirm-dialog')
  await page.getByRole('button', { name: '取消' }).click()

  await patientLogin(page)
  await screenshot(page, '02-patient-login-filled')
  await page.getByRole('button', { name: /^登录$/ }).click()
  await expect(page).toHaveURL(/\/patient\/home/)
  await expectNoUserFacingError(page)

  await page.getByText('预约挂号', { exact: true }).click()
  await expect(page).toHaveURL(/\/patient\/appointment/)
  await page.getByPlaceholder('搜索科室名称').fill('神经外科')
  await expect(page.getByText('神经外科').first()).toBeVisible()
  await screenshot(page, '02b-patient-appointment-search-filled')
  await page.goto('/patient/appointment?deptId=13&deptName=%E7%A5%9E%E7%BB%8F%E5%A4%96%E7%A7%91&doctorId=17&visitDate=2026-07-08&noon=PM')
  await expect(page.getByText('患者信息')).toBeVisible({ timeout: 10_000 })
  await page.getByRole('button', { name: /确认挂号/ }).click()
  await expect(page.getByText('请填写完整患者信息')).toBeVisible()
  await screenshot(page, '02c-patient-register-empty-form-feedback')
  await page.goto('/patient/home')

  await page.getByText('AI 问诊', { exact: true }).click()
  await expect(page).toHaveURL(/\/patient\/ai/)
  const analyzeButton = page.getByRole('button', { name: /开始智能分析/ })
  await expect(analyzeButton).toBeDisabled()
  await screenshot(page, '03-patient-ai-empty-disabled')
  await page.getByPlaceholder('例如：头痛、发热、胸闷、咳嗽...').fill('突发头痛伴恶心，无发热，既往高血压')
  await expect(analyzeButton).toBeEnabled()
  await screenshot(page, '04-patient-ai-filled-enabled')
  await analyzeButton.click()
  await expect(page.getByText('AI 分析建议')).toBeVisible({ timeout: 90_000 })
  await expect(page.getByText('您的症状：')).toBeVisible()
  await expect(page.locator('.review-content')).toContainText('突发头痛伴恶心')
  await screenshot(page, '04b-patient-ai-analysis-feedback')

  await page.goto('/patient/home')
  await page.getByText('检验预约', { exact: true }).click()
  await expect(page).toHaveURL(/\/patient\/lab-booking/)
  await expect(page.getByRole('button', { name: /提交预约申请/ })).toBeDisabled()
  await screenshot(page, '05-patient-lab-booking-empty-disabled')
  await page.getByRole('button', { name: /没有就诊记录，先去挂号/ }).click()
  await expect(page).toHaveURL(/\/patient\/appointment/)
  await screenshot(page, '06-patient-lab-booking-normal-entry-to-register')

  await page.goto('/mini-patient')
  await expect(page.getByText(/您好/)).toBeVisible({ timeout: 10_000 })
  await screenshot(page, '06b-mini-patient-home-entry')
  await page.getByText('预约挂号', { exact: true }).click()
  await screenshot(page, '06c-mini-patient-appointment-entry')

  await staffLogin(page, '医技', 'medicaltech')
  await screenshot(page, '07-staff-login-medicaltech-filled')
  await page.getByRole('button', { name: /^登录$/ }).click()
  await expect(page).toHaveURL(/\/medical-tech/)
  await page.getByPlaceholder('挂号ID').fill('318')
  await page.getByRole('button', { name: /刷新/ }).click()
  await expectNoUserFacingError(page)
  await screenshot(page, '08-medical-tech-filter-register-id-filled')
  await expect(page.locator('th').filter({ hasText: '挂号ID' })).toBeVisible()
  await expect(page.getByText(/No Data|待执行|执行中|已完成/).first()).toBeVisible()
  await screenshot(page, '08b-medical-tech-filter-result-feedback')

  await staffLogin(page, '药师', 'pharmacist')
  await page.getByRole('button', { name: /^登录$/ }).click()
  await expect(page).toHaveURL(/\/drugstore/)
  await expectNoUserFacingError(page)
  await screenshot(page, '09-drugstore-logout-entry-visible')
})
