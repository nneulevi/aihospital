// src/api/index.ts
import { request } from '@/utils/request'
import { getOpenAPIDefinition } from './client'

const api = getOpenAPIDefinition()

// 包装函数：兼容两类返回值：
// 1. 自定义 request 实例已解包后的业务对象
// 2. Orval 生成 client 直接返回的 AxiosResponse
// 让 res.data?.xxx 等价于 res.xxx，Vue 文件不用区分调用来源
const wrap = (fn: (...args: any[]) => Promise<any>) => async (...args: any[]): Promise<any> => {
    const res = await fn(...args)
    const isAxiosResponse =
        res &&
        typeof res === 'object' &&
        'data' in res &&
        'status' in res &&
        'headers' in res

    const payload = isAxiosResponse ? res.data : res

    if (!payload || typeof payload !== 'object') {
        return { data: payload, value: payload }
    }

    return new Proxy(payload, {
        get(target, prop) {
            if (prop === 'data') return target
            return target[prop]
        }
    })
}

// ========== 患者端 ==========
export const patientSendCode = wrap(api.sendCode)           // POST /api/patient/send-code
export const sendCode = patientSendCode
export const authRegister = wrap(api.register1)            // POST /api/patient/auth/register
export const patientRegister = wrap(api.register)            // POST /api/patient/register
export const patientLogout = wrap(api.logout)                // POST /api/patient/logout
export const cancelRegister = wrap(api.cancelRegister)       // PUT /api/patient/register/cancel
export const switchPatient = wrap(api.switchPatient)         // POST /api/patient/switch
export const getRecords = wrap((params: any) => request.get('/patient/records', params?.query || params))               // GET /api/patient/records
export const getRecordDetail = wrap(api.getRecordDetail)     // GET /api/patient/records/:id
export const getOrders = wrap((params: any) => request.get('/patient/orders', params?.query || params))                 // GET /api/patient/orders
export const list = wrap(api.list)                           // GET /api/patient/list
export const getDoctors = wrap((params: any) => request.get('/patient/doctors', params?.query || params))             // GET /api/patient/doctors

// ========== 医生/管理员认证（新增） ==========
export const authSendCode = wrap((data: any) => request.post('/auth/send-code', data))            // POST /api/auth/send-code
export const loginByCode = wrap((data: any) => request.post('/auth/login-by-code', data))           // POST /api/auth/login-by-code

// ========== 通用认证 ==========
export const login = wrap((data: any) => request.post('/auth/login', data))                       // POST /api/auth/login
export const authLogout = wrap(() => request.post('/auth/logout'))                // POST /api/auth/logout

// ========== 医生端 ==========
export const confirmDiagnosis = wrap(api.confirmDiagnosis)
export const createPrescription = wrap(api.createPrescription)
export const saveMedicalRecord = wrap(api.saveMedicalRecord)
export const createInspectionRequest = wrap(api.createInspectionRequest)
export const createDisposalRequest = wrap(api.createDisposalRequest)
export const createCheckRequest = wrap(api.createCheckRequest)
export const getPatients = wrap((params: any) => request.get('/doctor/patients', params?.query || params))
export const getPatientDetail = wrap(api.getPatientDetail)
export const getCheckResults = wrap(api.getCheckResults)
export const receivePatient = wrap((registerId: number) => request.put(`/doctor/patients/${registerId}/receive`))

// ========== AI 模块 ==========
export const scheduleGenerate = wrap(api.generate)
export const reportGenerate = wrap(api.generate1)
export const upload = wrap(api.upload)
export const analyze = wrap(api.analyze)
export const suggest = wrap(api.suggest)
export const triage = wrap(api.triage)
export const getResults = wrap((params: any) => request.get('/ai/schedule/result', params?.query || params))

// ========== 管理员 ==========
export const refund = wrap(api.refund)
export const charge = wrap(api.charge)
export const drugRefund = wrap(api.drugRefund)
export const dispense = wrap(api.dispense)
export const getInventory = wrap(api.getInventory)
export const getFinanceRecords = wrap((params: any) => request.get('/admin/finance/records', params?.query || params))
export const getDailySummary = wrap((params: any) => request.get('/admin/finance/daily-summary', params?.query || params))
export const getDrugInventory = wrap((params: any) => request.get('/admin/drug/inventory', params?.query || params))

// ========== 涓夌棣栭〉缁熻 ==========
export interface AdminDashboardSummary {
    todayRegistrations: number
    activePatients: number
    pendingChargeAmount: number
    stockAlertCount: number
    todayAiAnalysisCount: number
    pendingReportCount: number
}

export interface DoctorDashboardSummary {
    doctorId: number
    pendingCount: number
    consultingCount: number
    finishedToday: number
    pendingCheckCount: number
}

export interface PatientDashboardSummary {
    patientId: number
    recordCount: number
    unpaidOrderCount: number
    unpaidAmount: number
    latestVisitState?: string
}

export const getAdminDashboardSummary = wrap(() =>
    request.get<AdminDashboardSummary>('/admin/dashboard/summary')
)

export const getDoctorDashboardSummary = wrap((doctorId: number) =>
    request.get<DoctorDashboardSummary>('/doctor/dashboard/summary', { doctorId })
)

export const getPatientDashboardSummary = wrap((patientId: number) =>
    request.get<PatientDashboardSummary>('/patient/dashboard/summary', { patientId })
)

// ========== Medical technology workbench ==========
export interface MedicalTechTaskVO {
    itemType?: string
    itemId?: number
    registerId?: number
    patientName?: string
    projectName?: string
    projectPosition?: string
    state?: string
    result?: string
    price?: number
    creationTime?: string
}

export interface MedicalTechInterpretationVO {
    itemType?: string
    itemId?: number
    summary?: string
    suggestion?: string
}

export const getMedicalTechTasks = wrap((params: any) =>
    request.get('/medical-tech/tasks', params?.query || params)
)
export const executeMedicalTechTask = wrap((itemType: string, itemId: number, data: any) =>
    request.post(`/medical-tech/tasks/${itemType}/${itemId}/execute`, data)
)
export const reportMedicalTechTask = wrap((itemType: string, itemId: number, data: any) =>
    request.post(`/medical-tech/tasks/${itemType}/${itemId}/report`, data)
)
export const interpretMedicalTechTask = wrap((itemType: string, itemId: number) =>
    request.post(`/medical-tech/tasks/${itemType}/${itemId}/ai-interpret`)
)

// ========== Drugstore workbench ==========
export interface DrugStockRecordVO {
    id?: number
    drugId?: number
    drugName?: string
    recordType?: string
    quantity?: number
    beforeStock?: number
    afterStock?: number
    operatorId?: number
    operatorName?: string
    relatedPrescriptionId?: number
    reason?: string
    createTime?: string
}

export const getDrugstoreInventory = wrap((params: any) =>
    request.get('/drugstore/inventory', params?.query || params)
)
export const stockIn = wrap((data: any) =>
    request.post('/drugstore/stock/in', data)
)
export const stockCheck = wrap((data: any) =>
    request.post('/drugstore/stock/check', data)
)
export const getStockAlerts = wrap((params: any) =>
    request.get('/drugstore/stock/alerts', params?.query || params)
)
export const getStockRecords = wrap((params: any) =>
    request.get('/drugstore/stock/records', params?.query || params)
)
export const drugstoreDispense = wrap((data: any) =>
    request.post('/drugstore/dispense', data)
)
export const drugstoreRefund = wrap((data: any) =>
    request.post('/drugstore/refund', data)
)

// ========== Schedule source management ==========
export interface ScheduleSourceVO {
    scheduleId?: number
    doctorId?: number
    doctorName?: string
    deptId?: number
    deptName?: string
    scheduleDate?: string
    noon?: string
    registQuota?: number
    scheduleStatus?: string
    sourceType?: string
}

export const getScheduleSources = wrap((params: any) =>
    request.get('/schedule/sources', params?.query || params)
)
export const createScheduleSource = wrap((data: any) =>
    request.post('/schedule/sources', data)
)
export const updateScheduleQuota = wrap((scheduleId: number, data: any) =>
    request.put(`/schedule/sources/${scheduleId}/quota`, data)
)
export const suspendScheduleSource = wrap((scheduleId: number, data?: any) =>
    request.put(`/schedule/sources/${scheduleId}/suspend`, data || {})
)
export const resumeScheduleSource = wrap((scheduleId: number, data?: any) =>
    request.put(`/schedule/sources/${scheduleId}/resume`, data || {})
)

export type * from './model'
