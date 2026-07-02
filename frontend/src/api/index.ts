// src/api/index.ts
import { getOpenAPIDefinition } from './client'
import { request } from '@/utils/request'

const api = getOpenAPIDefinition()

// 原有的 wrap 函数保持不变
const wrap = (fn: Function) => async (...args: any[]) => {
    const res = await fn(...args)
    if (!res || typeof res !== 'object' || Array.isArray(res)) return res

    return new Proxy(res, {
        get(target, prop) {
            if (prop === 'data') return target
            return target[prop]
        }
    })
}

// ========== 患者端 ==========
export const patientSendCode = wrap(api.sendCode)
export const authRegister = wrap(api.register1)
export const patientRegister = wrap(api.register)
export const patientLogout = wrap(api.logout)
export const cancelRegister = wrap(api.cancelRegister)
export const switchPatient = wrap(api.switchPatient)
export const getRecords = wrap(api.getRecords)
export const getRecordDetail = wrap(api.getRecordDetail)
export const getOrders = wrap(api.getOrders)
export const list = wrap(api.list)
export const getDoctors = wrap(api.getDoctors)
export const listDepartments = wrap(api.listDepartments)
export const getTodayRegisters = wrap(api.getTodayRegisters)
export const submitCheckin = (data: { registerId: number }) =>
    request.post<import('./model').CheckinResultVO>('/patient/checkin/submit', data)
export const getQueueStatus = wrap(api.getQueueStatus)
export const getQueueDepts = wrap(api.getQueueDepts)
export const getQueueCount = wrap(api.getQueueCount)
export const getInspectionList = wrap(api.getInspectionList)
export const getCheckList = wrap(api.getCheckList)
export const patientCreateInspectionRequest = wrap(api.createInspectionRequest)
export const patientCreateCheckRequest = wrap(api.createCheckRequest)
export const getPrescriptions = wrap(api.getPrescriptions)
export const getPrescriptionDetail = wrap(api.getPrescriptionDetail)
export const getReports = wrap(api.getReports)
export const getReportDetail = wrap(api.getReportDetail)
export const markReportRead = wrap(api.markReportRead)
export const getCurrentPatient = wrap(api.getCurrentPatient)

// ========== 患者端 - 新增 4 个预约相关 API ==========
// 查询待预约检验列表（医生开的、未预约的、状态为 CREATED）
export const getPendingInspectionRequests = wrap(api.getPendingInspectionRequests)
// 查询待预约检查列表（医生开的、未预约的、状态为 CREATED）
export const getPendingCheckRequests = wrap(api.getPendingCheckRequests)
// 患者预约检验（更新 booked_time + 状态改为 BOOKED）
export const bookInspectionRequest = wrap(api.bookInspectionRequest)
// 患者预约检查（更新 booked_time + 状态改为 BOOKED）
export const bookCheckRequest = wrap(api.bookCheckRequest)

// ========== 医生/管理员认证 ==========
export const authSendCode = wrap(api.sendCode1)
export const loginByCode = wrap(api.loginByCode)

// ========== 通用认证 ==========
export const login = wrap(api.login)
export const authLogout = wrap(api.logout1)

// ========== 医生端 ==========
export const confirmDiagnosis = wrap(api.confirmDiagnosis)
export const createPrescription = wrap(api.createPrescription)
export const saveMedicalRecord = wrap(api.saveMedicalRecord)
export const createInspectionRequest = wrap(api.createInspectionRequest1)
export const createDisposalRequest = wrap(api.createDisposalRequest)
export const createCheckRequest = wrap(api.createCheckRequest1)
export const getPatients = wrap(api.getPatients)
export const getPatientDetail = wrap(api.getPatientDetail)
export const getCheckResults = wrap(api.getCheckResults)
export const getCheckResultDetail = wrap(api.getCheckResultDetail)
export const getStatistics = wrap(api.getStatistics)
export const getProfile = wrap(api.getProfile)

// ========== AI 模块 ==========
export const scheduleGenerate = wrap(api.generate)
export const reportGenerate = wrap(api.generate1)
export const upload = wrap(api.upload)
export const analyze = wrap(api.analyze)
export const suggest = wrap(api.suggest)
export const triage = wrap(api.triage)
export const getResults = wrap(api.getResults)

// ========== 管理员端 ==========
export const refund = wrap(api.refund)
export const charge = wrap(api.charge)
export const drugRefund = wrap(api.drugRefund)
export const dispense = wrap(api.dispense)
export const getInventory = wrap(api.getInventory)
export const getFinanceRecords = wrap(api.getFinanceRecords)
export const getDailySummary = wrap(api.getDailySummary)
export const getPendingItems = wrap(api.getPendingItems)
export const getPaidItems = wrap(api.getPaidItems)
export const getDrugInventory = wrap(api.getDrugInventory)
export const createEmployee = wrap(api.createEmployee)
export const getDoctorStats = wrap(api.getDoctorStats)
export const getDeptStats = wrap(api.getDeptStats)
export const listEmployees = wrap(api.listEmployees)
export const listDoctors = wrap(api.listDoctors)
export const listDepartmentsAdmin = wrap(api.listDepartments1)
export const getPendingDispense = wrap(api.getPendingDispense)
export const getPendingRefund = wrap(api.getPendingRefund)

// ========== 导出类型 ==========
export type * from './model'