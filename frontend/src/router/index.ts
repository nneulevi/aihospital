// src/router/index.ts
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { getToken, getUserRole } from '@/utils/auth'

const roleHome: Record<string, string> = {
    PATIENT: '/patient/home',
    DOCTOR: '/doctor',
    ADMIN: '/admin',
    MEDICAL_TECH: '/medical-tech',
    PHARMACIST: '/drugstore'
}

const loginPathByRole = (role?: string) => role === 'PATIENT' ? '/patient/login' : '/auth/login'

const checkAuth = (to: any, from: any, next: any) => {
    if (to.meta?.noAuth) {
        const role = getUserRole()
        if (getToken() && role && roleHome[role]) {
            next(roleHome[role])
            return
        }
        next()
        return
    }

    const requiredRole = to.matched.find((record: any) => record.meta?.role)?.meta?.role as string | undefined
    const token = getToken()
    const currentRole = getUserRole()

    if (!token || !currentRole) {
        next({ path: loginPathByRole(requiredRole), query: { redirect: to.fullPath } })
        return
    }

    if (requiredRole && currentRole !== requiredRole) {
        next(roleHome[currentRole] || loginPathByRole())
        return
    }

    next()
}

// ========== 独立页面（无布局） ==========
const independentRoutes: RouteRecordRaw[] = [
    {
        path: '/patient/login',
        name: 'PatientLogin',
        component: () => import('@/views/patient/Login.vue'),
        meta: { noAuth: true }
    },
    {
        path: '/auth/login',
        name: 'StaffLogin',
        component: () => import('@/views/auth/StaffRoleLogin.vue'),
        meta: { noAuth: true }
    }
]

// ========== 患者端路由（带布局） ==========
const patientRoutes: RouteRecordRaw[] = [
    {
        path: '/patient',
        component: () => import('@/views/layouts/PatientLayout.vue'),
        meta: { role: 'PATIENT' },
        children: [
            { path: '', redirect: '/patient/home' },
            { path: 'home', name: 'PatientHome', component: () => import('@/views/patient/Home.vue') },
            { path: 'ai', name: 'AIInquiry', component: () => import('@/views/patient/AIInquiry.vue') },
            { path: 'appointment', name: 'Appointment', component: () => import('@/views/patient/Appointment.vue') },
            { path: 'appointment/success', name: 'AppointmentSuccess', component: () => import('@/views/patient/AppointmentSuccess.vue') },
            { path: 'appointment-success', redirect: '/patient/appointment/success' },
            { path: 'appointments', name: 'AppointmentRecords', component: () => import('@/views/patient/AppointmentRecords.vue') },
            { path: 'records', name: 'Records', component: () => import('@/views/patient/Records.vue') },
            { path: 'record/:id', name: 'RecordDetail', component: () => import('@/views/patient/RecordDetail.vue') },
            { path: 'orders', name: 'Orders', component: () => import('@/views/patient/Orders.vue') },
            { path: 'profile', name: 'Profile', component: () => import('@/views/patient/Profile.vue') },
            { path: 'patient-manager', name: 'PatientManager', component: () => import('@/views/patient/PatientManager.vue') },
            { path: 'checkin', name: 'Checkin', component: () => import('@/views/patient/Checkin.vue') },
            { path: 'queue', name: 'QueueQuery', component: () => import('@/views/patient/QueueQuery.vue') },
            { path: 'reports', name: 'Reports', component: () => import('@/views/patient/Reports.vue') },
            { path: 'prescriptions', name: 'Prescriptions', component: () => import('@/views/patient/Prescriptions.vue') },
            { path: 'lab-booking', name: 'LabBooking', component: () => import('@/views/patient/LabBooking.vue') },
            { path: 'exam-booking', name: 'ExamBooking', component: () => import('@/views/patient/ExamBooking.vue') },
            { path: 'messages', name: 'Messages', component: () => import('@/views/patient/Messages.vue') },
            { path: 'consult', name: 'Consult', component: () => import('@/views/patient/Consult.vue') },
            { path: 'doctor-schedule', name: 'PatientDoctorSchedule', component: () => import('@/views/patient/DoctorSchedule.vue') },
            { path: 'revisit', name: 'Revisit', component: () => import('@/views/patient/Revisit.vue') },
            { path: 'physical-exam', name: 'PhysicalExam', component: () => import('@/views/patient/PhysicalExam.vue') },
            { path: 'services', name: 'Services', component: () => import('@/views/patient/Services.vue') },
            { path: 'guide', name: 'Guide', component: () => import('@/views/patient/Guide.vue') },
            { path: 'customer-service', name: 'CustomerService', component: () => import('@/views/patient/CustomerService.vue') },
        ]
    }
]

// ========== 医生端路由 ==========
const doctorRoutes: RouteRecordRaw[] = [
    {
        path: '/doctor',
        component: () => import('@/views/layouts/DoctorLayout.vue'),
        meta: { role: 'DOCTOR' },
        children: [
            { path: '', name: 'DoctorDashboard', component: () => import('@/views/doctor/DoctorDashboard.vue') },
            { path: 'visit', name: 'PatientVisit', component: () => import('@/views/doctor/PatientVisit.vue') },
            { path: 'ai-diagnosis', name: 'DoctorAIDiagnosis', component: () => import('@/views/doctor/AIDiagnosis.vue') },
            { path: 'ai-triage', name: 'DoctorAITriage', component: () => import('@/views/doctor/AITriage.vue') },
            { path: 'schedule', name: 'DoctorSchedule', component: () => import('@/views/doctor/DoctorSchedule.vue') },
            { path: 'headct-reports', name: 'DoctorHeadCtReportWorkbench', component: () => import('@/views/doctor/HeadCtReportWorkbench.vue') },
            { path: 'result/:id', name: 'DoctorResultDetail', component: () => import('@/views/doctor/ResultDetail.vue') },
            { path: 'result-detail/:type/:id', redirect: to => ({ path: `/doctor/result/${to.params.id}` }) },
            { path: 'profile', name: 'DoctorProfile', component: () => import('@/views/doctor/DoctorProfile.vue') },
        ]
    }
]

// ========== 管理员端路由 ==========
const adminRoutes: RouteRecordRaw[] = [
    {
        path: '/admin',
        component: () => import('@/views/layouts/AdminBusinessLayout.vue'),
        meta: { role: 'ADMIN' },
        children: [
            { path: '', name: 'AdminHome', component: () => import('@/views/admin/AdminHome.vue') },
            { path: 'schedule', name: 'AISchedule', component: () => import('@/views/admin/AISchedule.vue') },
            { path: 'schedule-sources', name: 'ScheduleSourceManage', component: () => import('@/views/admin/ScheduleSourceManage.vue') },
            { path: 'finance', name: 'FinanceManage', component: () => import('@/views/admin/FinanceManage.vue') },
            { path: 'drug', name: 'DrugManage', component: () => import('@/views/admin/DrugManage.vue') },
            { path: 'staff/create', name: 'AdminStaffCreate', component: () => import('@/views/admin/StaffCreate.vue') },
            { path: 'stats/doctors', name: 'AdminDoctorStats', component: () => import('@/views/admin/DoctorStats.vue') },
            { path: 'stats/departments', name: 'AdminDeptStats', component: () => import('@/views/admin/DeptStats.vue') },
            { path: 'doctor-stats', redirect: '/admin/stats/doctors' },
            { path: 'dept-stats', redirect: '/admin/stats/departments' },
        ]
    }
]

const miniPatientRoutes: RouteRecordRaw[] = [
    {
        path: '/mini-patient',
        component: () => import('@/views/mini-patient/MiniPatientLayout.vue'),
        meta: { role: 'PATIENT' },
        children: [
            { path: '', name: 'MiniPatientHome', component: () => import('@/views/mini-patient/Home.vue') },
            { path: 'ai', name: 'MiniPatientAI', component: () => import('@/views/mini-patient/AI.vue') },
            { path: 'appointment', name: 'MiniPatientAppointment', component: () => import('@/views/mini-patient/Appointment.vue') },
            { path: 'records', name: 'MiniPatientRecords', component: () => import('@/views/mini-patient/Records.vue') },
            { path: 'orders', name: 'MiniPatientOrders', component: () => import('@/views/mini-patient/Orders.vue') },
            { path: 'profile', name: 'MiniPatientProfile', component: () => import('@/views/mini-patient/Profile.vue') },
        ]
    }
]

// ========== 医技人员端 ==========
const medicalTechRoutes: RouteRecordRaw[] = [
    {
        path: '/medical-tech',
        component: () => import('@/views/layouts/MedicalTechLayout.vue'),
        meta: { role: 'MEDICAL_TECH' },
        children: [
            { path: '', name: 'MedicalTechWorkbench', component: () => import('@/views/medical-tech/MedicalTechWorkbench.vue') },
        ]
    }
]

// ========== 药房端 ==========
const drugstoreRoutes: RouteRecordRaw[] = [
    {
        path: '/drugstore',
        component: () => import('@/views/layouts/DrugstoreLayout.vue'),
        meta: { role: 'PHARMACIST' },
        children: [
            { path: '', name: 'DrugstoreWorkbench', component: () => import('@/views/drugstore/DrugstoreWorkbench.vue') },
        ]
    }
]

const fallbackRoute: RouteRecordRaw = {
    path: '/:pathMatch(.*)*',
    redirect: '/patient/home'
}

const routes: RouteRecordRaw[] = [
    { path: '/', redirect: '/patient/home' },
    ...independentRoutes,
    ...patientRoutes,
    ...miniPatientRoutes,
    ...doctorRoutes,
    ...adminRoutes,
    ...medicalTechRoutes,
    ...drugstoreRoutes,
    fallbackRoute
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach(checkAuth)

export default router
