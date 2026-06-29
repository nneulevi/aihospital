// src/api/index.ts
import { getOpenAPIDefinition } from './client'

const api = getOpenAPIDefinition()

// 包装函数
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
export const listDepartments = wrap(api.listDepartments)           // 患者端科室列表
export const getTodayRegisters = wrap(api.getTodayRegisters)       // 今日可报到列表
export const submitCheckin = wrap(api.submitCheckin)               // 报到提交
export const getQueueStatus = wrap(api.getQueueStatus)             // 候诊状态
export const getQueueDepts = wrap(api.getQueueDepts)               // 候诊科室列表
export const getQueueCount = wrap(api.getQueueCount)               // 候诊角标
export const getInspectionList = wrap(api.getInspectionList)       // 检验项目列表
export const getCheckList = wrap(api.getCheckList)                 // 检查项目列表
export const patientCreateInspectionRequest = wrap(api.createInspectionRequest)  // 检验预约（患者端）
export const patientCreateCheckRequest = wrap(api.createCheckRequest)            // 检查预约（患者端）
export const getPrescriptions = wrap(api.getPrescriptions)         // 处方列表
export const getPrescriptionDetail = wrap(api.getPrescriptionDetail) // 处方详情
export const getReports = wrap(api.getReports)                     // 报告列表
export const getReportDetail = wrap(api.getReportDetail)           // 报告详情
export const markReportRead = wrap(api.markReportRead)             // 标记报告已读
export const getCurrentPatient = wrap(api.getCurrentPatient)       // 当前患者信息

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
export const getCheckResultDetail = wrap(api.getCheckResultDetail) // 检查结果详情
export const getStatistics = wrap(api.getStatistics)               // 医生统计数据
export const getProfile = wrap(api.getProfile)                     // 医生个人信息

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
export const getDrugInventory = wrap(api.getDrugInventory)
export const createEmployee = wrap(api.createEmployee)
export const getDoctorStats = wrap(api.getDoctorStats)
export const getDeptStats = wrap(api.getDeptStats)
export const listEmployees = wrap(api.listEmployees)
export const listDoctors = wrap(api.listDoctors)
export const listDepartmentsAdmin = wrap(api.listDepartments1)     // 管理员端科室列表

// ========== 导出类型 ==========
export type * from './model'