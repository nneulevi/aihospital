// src/api/index.ts
import { request } from '@/utils/request'
import { postJsonSse, type SseJsonHandlers } from '@/utils/sseJson'
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
export const getPatientDepartments = wrap(() => request.get<PatientDepartmentVO[]>('/patient/department/list'))
export const getTodayRegister = wrap((patientId: number) => request.get<PatientTodayRegisterVO>('/patient/register/today', { patientId }))
export const submitPatientCheckin = wrap((patientId: number, registerId?: number) =>
    request.post<PatientCheckinResultVO>('/patient/checkin/submit', undefined, { params: { patientId, registerId } })
)
export const getPatientQueueStatus = wrap((patientId: number, registerId?: number) =>
    request.get<PatientQueueStatusVO>('/patient/queue/status', { patientId, registerId })
)
export const getPatientInspectionCatalog = wrap((params?: any) =>
    request.get<PatientMedicalTechnologyVO[]>('/patient/medical-technology/inspection', params?.query || params)
)
export const getPatientCheckCatalog = wrap((params?: any) =>
    request.get<PatientMedicalTechnologyVO[]>('/patient/medical-technology/check', params?.query || params)
)
export const getPatientInspectionRequests = wrap((params: any) =>
    request.get('/patient/inspection-requests', params?.query || params)
)
export const getPatientCheckRequests = wrap((params: any) =>
    request.get('/patient/check-requests', params?.query || params)
)
export const getPatientPrescriptions = wrap((params: any) =>
    request.get('/patient/prescriptions', params?.query || params)
)
export const getPatientReports = wrap((params: any) =>
    request.get('/patient/reports', params?.query || params)
)
export const getPatientQueueDepts = wrap((patientId: number) =>
    request.get('/patient/queue/depts', { patientId })
)
export const getPatientQueueCount = wrap((patientId: number) =>
    request.get('/patient/queue/count', { patientId })
)
export const createPatientCheckRequest = wrap((data: any) =>
    request.post('/patient/check-request', data)
)
export const createPatientInspectionRequest = wrap((data: any) =>
    request.post('/patient/inspection-request', data)
)
export const getPatientPrescriptionDetail = wrap((prescriptionId: number) =>
    request.get(`/patient/prescriptions/${prescriptionId}`)
)
export const getPatientReportDetail = wrap((reportId: string) =>
    request.get(`/patient/reports/${reportId}`)
)
export const markPatientReportRead = wrap((reportId: string) =>
    request.put(`/patient/reports/${reportId}/read`)
)
export const getCurrentPatient = wrap((patientId: number) =>
    request.get('/patient/current', { patientId })
)

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
export const returnPatientToWaiting = wrap((registerId: number) => request.put(`/doctor/patients/${registerId}/return-waiting`))
export const getMedicalRecord = wrap((registerId: number) =>
    request.get(`/doctor/medical-record/${registerId}`)
)
export const getOrdersByRegisterId = wrap((registerId: number) =>
    request.get(`/doctor/orders/${registerId}`)
)
export const getPrescriptionsByRegisterId = wrap((registerId: number) =>
    request.get(`/doctor/prescriptions/${registerId}`)
)
export const getDiagnosis = wrap((registerId: number) =>
    request.get(`/doctor/diagnosis/${registerId}`)
)
export const getDoctorProfile = wrap((doctorId: number) =>
    request.get<DoctorProfileVO>('/doctor/profile', { doctorId })
)
export const getDoctorStatistics = wrap((doctorId: number) =>
    request.get<DoctorStatisticsVO>('/doctor/statistics', { doctorId })
)
export const getCheckResultDetail = wrap((itemId: number) =>
    request.get(`/doctor/check-result/${itemId}`)
)

// ========== AI 模块 ==========
export const scheduleGenerate = wrap(api.generate)
export const reportGenerate = wrap(api.generate1)
export const upload = wrap(api.upload)
export const analyze = wrap(api.analyze)
export const suggest = wrap(api.suggest)
export const triage = wrap(api.triage)
export const triageStream = (data: any, handlers: SseJsonHandlers = {}) =>
    postJsonSse('/ai/consultation/triage/stream', data, handlers)
export const diagnosisSuggestStream = (data: any, handlers: SseJsonHandlers = {}) =>
    postJsonSse('/ai/diagnosis/suggest/stream', data, handlers)
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
export const getAdminPendingItems = wrap((registerId: number) =>
    request.get<ChargeItemVO[]>('/admin/finance/pending-items', { registerId })
)
export const getAdminPaidItems = wrap((registerId: number) =>
    request.get<ChargeItemVO[]>('/admin/finance/paid-items', { registerId })
)
export const getAdminPendingDispense = wrap(() =>
    request.get<PrescriptionWorkItemVO[]>('/admin/drug/pending-dispense')
)
export const getAdminPendingRefund = wrap(() =>
    request.get<PrescriptionWorkItemVO[]>('/admin/drug/pending-refund')
)
export const getAdminEmployees = wrap(() =>
    request.get<EmployeeListItemVO[]>('/admin/employee/list')
)
export const getAdminDoctors = wrap(() =>
    request.get<EmployeeListItemVO[]>('/admin/employee/doctors')
)
export const getAdminDepartments = wrap(() =>
    request.get<PatientDepartmentVO[]>('/admin/department/list')
)

export interface StaffCreateRequest {
    deptId?: number
    registLevelId?: number
    name: string
    account: string
    role: string
    titleLevel?: string
    phone?: string
    note?: string
}

export interface StaffCreateResponse {
    staffId: number
    account: string
    name: string
    role: string
    status: string
}

export interface DoctorStatsVO {
    doctorId: number
    doctorName: string
    deptName?: string
    titleLevel?: string
    todayRegistrations: number
    activePatients: number
    finishedToday: number
    pendingChecks: number
}

export interface DepartmentStatsVO {
    deptId: number
    deptName: string
    deptType?: string
    doctorCount: number
    todayRegistrations: number
    activePatients: number
    scheduleQuota: number
    pendingChecks: number
}

export const createStaff = wrap((data: StaffCreateRequest) =>
    request.post<StaffCreateResponse>('/admin/staff', data)
)
export const getAdminDoctorStats = wrap(() =>
    request.get<DoctorStatsVO[]>('/admin/stats/doctors')
)
export const getAdminDepartmentStats = wrap(() =>
    request.get<DepartmentStatsVO[]>('/admin/stats/departments')
)

// ========== 三端首页统计 ==========
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

export interface PatientDepartmentVO {
    deptId: number
    deptName: string
    deptType?: string
    description?: string
}

export interface PatientTodayRegisterVO {
    registerId?: number
    visitNo?: string
    patientId?: number
    visitDate?: string
    noon?: string
    queueNo?: number
    visitState?: string
    visitStateName?: string
    deptName?: string
    doctorName?: string
    createTime?: string
}

export interface PatientCheckinResultVO {
    registerId?: number
    visitState?: string
    visitStateName?: string
    queueNo?: number
    deptName?: string
    doctorName?: string
    message?: string
}

export interface PatientQueueStatusVO extends PatientCheckinResultVO {
    patientId?: number
    visitDate?: string
    noon?: string
    waitingAhead?: number
}

export interface PatientMedicalTechnologyVO {
    techId?: number
    techCode?: string
    techName?: string
    techFormat?: string
    techPrice?: number
    techType?: string
    priceType?: string
    deptId?: number
    deptName?: string
}

export interface PatientMedicalRequestVO {
    requestId?: number
    registerId?: number
    itemType?: string
    itemName?: string
    itemPosition?: string
    state?: string
    stateName?: string
    result?: string
    price?: number
    creationTime?: string
}

export interface PatientPrescriptionVO {
    prescriptionId?: number
    registerId?: number
    prescriptionNo?: string
    status?: string
    statusName?: string
    totalAmount?: number
    doctorName?: string
    creationTime?: string
    dispenseTime?: string
    drugNames?: string[]
    drugSummary?: string
}

export interface PatientReportVO {
    reportId?: string
    registerId?: number
    itemType?: string
    itemId?: number
    itemName?: string
    itemPosition?: string
    status?: string
    statusName?: string
    result?: string
    deptName?: string
    doctorName?: string
    reportTime?: string
    creationTime?: string
}

export interface DoctorProfileVO {
    doctorId?: number
    doctorName?: string
    titleLevel?: string
    phone?: string
    roleType?: string
    deptId?: number
    deptName?: string
    active?: boolean
    createTime?: string
}

export interface DoctorStatisticsVO {
    todayVisits?: number
    monthVisits?: number
    totalVisits?: number
    pendingCount?: number
    consultingCount?: number
    finishedCount?: number
    pendingCheckCount?: number
}

export interface ChargeItemVO {
    itemId?: number
    itemType?: string
    itemName?: string
    registerId?: number
    patientName?: string
    amount?: number
    state?: string
    stateName?: string
    creationTime?: string
}

export interface PrescriptionWorkItemVO {
    prescriptionId?: number
    registerId?: number
    prescriptionNo?: string
    patientName?: string
    doctorName?: string
    status?: string
    statusName?: string
    totalAmount?: number
    drugSummary?: string
    creationTime?: string
    dispenseTime?: string
}

export interface EmployeeListItemVO {
    employeeId?: number
    realname?: string
    roleType?: string
    titleLevel?: string
    phone?: string
    deptId?: number
    deptName?: string
    active?: boolean
    createTime?: string
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
