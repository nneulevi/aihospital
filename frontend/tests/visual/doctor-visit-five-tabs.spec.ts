import { expect, test, type Page } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

const outputDir = path.resolve('visual-results', 'doctor-visit-five-tabs')
const project2BaseUrl = process.env.PROJECT2_BASE_URL || 'http://127.0.0.1:8092'

const ensureOutputDir = () => fs.mkdirSync(outputDir, { recursive: true })

const screenshot = async (page: Page, name: string) => {
  ensureOutputDir()
  await page.screenshot({ path: path.join(outputDir, `${name}.png`), fullPage: true })
}

const today = () => {
  const d = new Date()
  const m = `${d.getMonth() + 1}`.padStart(2, '0')
  const day = `${d.getDate()}`.padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

const apiFetch = async (url: string, init?: RequestInit) => fetch(`${project2BaseUrl}${url}`, {
  headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
  ...init,
})

const unwrap = async (response: Response) => {
  const text = await response.text()
  if (!response.ok) {
    throw new Error(`${response.status} ${response.url} ${text}`)
  }
  return text ? JSON.parse(text) : undefined
}

const cancelDemoActiveRegisters = async (visitDate: string) => {
  void visitDate
  for (const visitState of ['REGISTERED', 'DOCTOR_RECEIVED']) {
      const params = new URLSearchParams({
        doctorId: '17',
        visitState,
        pageNum: '1',
        pageSize: '50'
      })
      const page = await unwrap(await apiFetch(`/api/doctor/patients?${params}`))
      const rows = (page.records || []).filter((item: any) => item.patientName === 'Project2独立验收患者')
      for (const row of rows) {
        await apiFetch('/api/patient/register/cancel', {
          method: 'PUT',
          body: JSON.stringify({ registerId: row.registerId, cancelReason: '医生五部分截图验收前清理重复活跃记录' }),
        }).catch(() => undefined)
      }
  }
}

type TestRegister = {
  registerId: number
  patientName: string
  visitState: string
}

const findDoctorRegister = async (registerId?: number): Promise<TestRegister | undefined> => {
  for (const visitState of ['REGISTERED', 'DOCTOR_RECEIVED']) {
    const params = new URLSearchParams({
      doctorId: '17',
      visitState,
      pageNum: '1',
      pageSize: '50'
    })
    const page = await unwrap(await apiFetch(`/api/doctor/patients?${params}`))
    const row = (page.records || []).find((item: any) => {
      if (registerId) return Number(item.registerId) === registerId
      return item.patientName === 'Project2独立验收患者'
    })
    if (row?.registerId) {
      return {
        registerId: Number(row.registerId),
        patientName: row.patientName || 'Project2独立验收患者',
        visitState: row.visitState || visitState
      }
    }
  }
  return undefined
}

const createTodayDemoRegister = async (page: Page) => {
  const visitDate = today()
  await cancelDemoActiveRegisters(visitDate)
  await unwrap(await apiFetch('/api/schedule/sources', {
    method: 'POST',
    body: JSON.stringify({
      deptId: 13,
      doctorId: 17,
      scheduleDate: visitDate,
      noon: 'AM',
      registQuota: 30,
      registLevelId: 13,
      active: true,
    }),
  }))
  const response = await apiFetch('/api/patient/register', {
    method: 'POST',
    body: JSON.stringify({
      realName: 'Project2独立验收患者',
      gender: 'M',
      cardNumber: '11010119700149547X',
      birthdate: '1970-01-01',
      homeAddress: 'Project2 E2E',
      phone: '13800001111',
      deptId: 13,
      doctorId: 17,
      visitDate,
      noon: 'AM',
      registLevelId: 13,
      settleCategoryId: 1,
      registMethod: 'MOBILE',
    }),
  })
  if (response.ok) {
    const registerId = Number(await response.json())
    const created = await findDoctorRegister(registerId)
    if (created) return created
    return { registerId, patientName: 'Project2独立验收患者', visitState: 'REGISTERED' }
  }
  const existing = await findDoctorRegister()
  if (existing) {
    return existing
  }
  throw new Error(`cannot create or find demo register: ${response.status} ${await response.text()}`)
}

const loginDoctor = async (page: Page) => {
  await page.goto('/auth/login')
  await page.evaluate(() => {
    localStorage.clear()
    sessionStorage.clear()
  })
  await page.goto('/auth/login')
  await page.getByRole('button', { name: '医生', exact: true }).click()
  await page.getByPlaceholder('用户名').fill('doctor')
  await page.getByPlaceholder('密码').fill('123456')
  await page.getByRole('button', { name: /^登录$/ }).click()
  await expect(page).toHaveURL(/\/doctor/)
}

const fillVisible = async (page: Page, placeholder: string, value: string) => {
  await page.getByPlaceholder(placeholder).fill(value)
}

const fillByName = async (page: Page, name: string, value: string) => {
  await page.getByRole('textbox', { name }).fill(value)
}

test('医生接诊页五个部分必须有填写和交互截图', async ({ page }) => {
  const demoRegister = await createTodayDemoRegister(page)
  await loginDoctor(page)

  if (demoRegister.visitState === 'DOCTOR_RECEIVED') {
    await page.getByRole('tab', { name: '就诊中' }).click()
  }
  const patientCard = page.getByText(demoRegister.patientName).first()
  await patientCard.scrollIntoViewIfNeeded()
  await patientCard.click()
  await expect(page).toHaveURL(/\/doctor\/visit/)
  await expect(page.getByText(`挂号ID: ${demoRegister.registerId}`)).toBeVisible({ timeout: 10_000 })

  await fillVisible(page, '患者主要不适...', '头部外伤后头痛伴恶心，需结合头部 CT 复核。')
  await fillVisible(page, '现病史描述...', '今日摔倒后头痛，无明显意识障碍，既往高血压。')
  await fillVisible(page, '已做治疗', '暂未特殊处理')
  await fillVisible(page, '既往病史', '高血压 5 年')
  await fillVisible(page, '过敏史', '无明确药物过敏史')
  await fillVisible(page, '体格检查结果...', '神志清楚，颈抵抗阴性，四肢活动可。')
  await fillVisible(page, '建议检查项目...', '建议头颅 CT 平扫，必要时复查。')
  await fillVisible(page, '注意事项', '观察头痛、呕吐、意识变化。')
  await fillVisible(page, '初步诊断...', '头部外伤待查')
  await screenshot(page, '01-record-tab-filled')
  await page.getByRole('button', { name: '保存病历' }).click()
  await expect(page.getByText('病历保存成功')).toBeVisible()
  await screenshot(page, '01b-record-save-feedback')

  await page.getByRole('tab', { name: '检查检验' }).click()
  await page.getByRole('button', { name: '提交申请' }).click()
  await expect(page.getByText('请先添加检查、检验或处置项目')).toBeVisible()
  await screenshot(page, '02-check-tab-empty-submit-blocked')
  await fillVisible(page, '如：头颅CT平扫', '头颅CT平扫')
  await fillByName(page, '检查部位', '头部')
  await page.getByRole('button', { name: '添加检查' }).click()
  await fillVisible(page, '如：血常规检查', '血常规检查')
  await fillVisible(page, '如：静脉血', '静脉血')
  await page.getByRole('button', { name: '添加检验' }).click()
  await fillVisible(page, '如：换药处理', '创面换药')
  await fillByName(page, '处置部位', '额部')
  await page.getByRole('button', { name: '添加处置' }).click()
  await screenshot(page, '03-check-tab-all-items-filled')
  await page.getByRole('button', { name: '提交申请' }).click()
  await expect(page.getByText('申请提交成功')).toBeVisible()
  await screenshot(page, '03b-check-tab-submit-feedback')

  await page.getByRole('tab', { name: '结果' }).click()
  await screenshot(page, '04-result-tab-ai-image-fields')

  await page.getByRole('tab', { name: '处方' }).click()
  await page.getByPlaceholder('搜索药品...').click()
  await expect(page.getByText('选择药品')).toBeVisible()
  await screenshot(page, '06b-prescription-drug-picker-visible')
  await page.getByText('布洛芬缓释胶囊 0.3g×20粒').click()
  await expect(page.getByPlaceholder('搜索药品...')).toHaveValue('布洛芬缓释胶囊 0.3g×20粒')
  await fillVisible(page, '如：口服', '静滴')
  await fillVisible(page, '如：每日三次', '每日一次')
  await fillVisible(page, '如：100mg', '250ml')
  await fillVisible(page, '如：1片', '250ml')
  await fillVisible(page, '1-90', '1')
  await fillVisible(page, '1-999', '1')
  await screenshot(page, '06-prescription-tab-fields-filled')
  await page.getByRole('button', { name: '加入处方' }).click()
  await expect(page.getByText('已添加')).toBeVisible()
  await expect(page.locator('.drug-item .drug-name').filter({ hasText: '布洛芬缓释胶囊 0.3g×20粒' })).toBeVisible()
  await screenshot(page, '06c-prescription-add-drug-feedback')
  await page.getByRole('button', { name: '提交处方' }).click()
  await expect(page.getByText('处方提交成功')).toBeVisible()
  await screenshot(page, '06d-prescription-submit-feedback')

  await page.getByRole('tab', { name: '确诊' }).click()
  await fillVisible(page, '最终诊断结果...', '头部外伤；颅内急性出血待排')
  await fillVisible(page, '治疗及处理意见...', '完善头颅 CT，观察神经系统体征，必要时复诊。')
  await fillVisible(page, '如：1,2,3（逗号分隔）', '1')
  await screenshot(page, '05-confirm-tab-filled')
  await page.getByRole('button', { name: '确认确诊' }).click()
  await expect(page.getByText('确诊成功')).toBeVisible()
  await screenshot(page, '05b-confirm-submit-feedback')

  await apiFetch('/api/patient/register/cancel', {
    method: 'PUT',
    body: JSON.stringify({ registerId: demoRegister.registerId, cancelReason: '医生五部分截图验收清理' }),
  }).catch(() => undefined)
})
