// src/router/index.ts
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

// ========== 导入布局 ==========
import PatientLayout from '@/views/layouts/PatientLayout.vue'

// ========== 导入患者端组件 ==========
import Home from '@/views/patient/Home.vue'
import AppointmentRecords from '@/views/patient/AppointmentRecords.vue'
import Profile from '@/views/patient/Profile.vue'
import PatientManager from '@/views/patient/PatientManager.vue'
import Appointment from '@/views/patient/Appointment.vue'
import AppointmentSuccess from '@/views/patient/AppointmentSuccess.vue'
import Orders from '@/views/patient/Orders.vue'
import AIInquiry from '@/views/patient/AIInquiry.vue'
import RecordDetail from '@/views/patient/RecordDetail.vue'

// ========== 导入新建的患者端组件 ==========
import Checkin from '@/views/patient/Checkin.vue'
import QueueQuery from '@/views/patient/QueueQuery.vue'
import Reports from '@/views/patient/Reports.vue'
import Prescriptions from '@/views/patient/Prescriptions.vue'
import LabBooking from '@/views/patient/LabBooking.vue'
import ExamBooking from '@/views/patient/ExamBooking.vue'

// ========== ✅ 新增：导入新创建的页面组件 ==========
import Messages from '@/views/patient/Messages.vue'
import Consult from '@/views/patient/Consult.vue'
import DoctorSchedule from '@/views/patient/DoctorSchedule.vue'
import Revisit from '@/views/patient/Revisit.vue'
import PhysicalExam from '@/views/patient/PhysicalExam.vue'
import Services from '@/views/patient/Services.vue'
import Guide from '@/views/patient/Guide.vue'
import CustomerService from '@/views/patient/CustomerService.vue'

// ========== 路由守卫 ==========
const checkAuth = (to: any, from: any, next: any) => {
    // 获取用户 store
    const userStore = useUserStore()

    // 判断是否需要认证（noAuth 路由不需要登录）
    const requiresAuth = !to.meta.noAuth

    // 如果是不需要认证的路由，直接放行
    if (!requiresAuth) {
        // 如果已经登录，访问登录页跳转到对应的首页
        if (userStore.isLoggedIn) {
            if (userStore.isPatient) {
                next('/patient/home')
                return
            } else if (userStore.isDoctor) {
                next('/doctor')
                return
            } else if (userStore.isAdmin) {
                next('/admin')
                return
            }
        }
        next()
        return
    }

    // 需要认证的路由
    if (!userStore.isLoggedIn) {
        // 根据访问路径跳转到对应的登录页
        if (to.path.startsWith('/patient') && !to.path.includes('/login')) {
            next('/patient/login')
        } else if (to.path.startsWith('/doctor')) {
            next('/auth/login')
        } else if (to.path.startsWith('/admin')) {
            next('/auth/login')
        } else {
            next('/patient/login')
        }
        return
    }

    // 已登录，检查角色权限
    const requiredRole = to.meta.role
    if (requiredRole) {
        // 检查当前用户角色是否匹配
        let hasRole = false
        if (requiredRole === 'PATIENT' && userStore.isPatient) hasRole = true
        else if (requiredRole === 'DOCTOR' && userStore.isDoctor) hasRole = true
        else if (requiredRole === 'ADMIN' && userStore.isAdmin) hasRole = true

        if (!hasRole) {
            // 角色不匹配，跳转到对应的首页
            if (userStore.isPatient) {
                next('/patient/home')
            } else if (userStore.isDoctor) {
                next('/doctor')
            } else if (userStore.isAdmin) {
                next('/admin')
            } else {
                next('/auth/login')
            }
            return
        }
    }

    // 验证通过，放行
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
        component: () => import('@/views/auth/StaffLogin.vue'),
        meta: { noAuth: true }
    }
]

// ========== 患者端路由 ==========
const patientRoutes: RouteRecordRaw[] = [
    {
        path: '/patient',
        component: PatientLayout,
        redirect: '/patient/home',
        meta: { role: 'PATIENT' },
        children: [
            // ===== 底部Tabbar页面 =====
            { path: 'home', name: 'PatientHome', component: Home, meta: { role: 'PATIENT' } },
            { path: 'appointments', name: 'AppointmentRecords', component: AppointmentRecords, meta: { role: 'PATIENT' } },
            { path: 'profile', name: 'PatientProfile', component: Profile, meta: { role: 'PATIENT' } },

            // ===== 功能页面 =====
            { path: 'patient-manager', name: 'PatientManager', component: PatientManager, meta: { role: 'PATIENT' } },
            { path: 'appointment', name: 'Appointment', component: Appointment, meta: { role: 'PATIENT' } },
            { path: 'appointment-success', name: 'AppointmentSuccess', component: AppointmentSuccess, meta: { role: 'PATIENT' } },
            { path: 'orders', name: 'Orders', component: Orders, meta: { role: 'PATIENT' } },
            { path: 'ai', name: 'AIInquiry', component: AIInquiry, meta: { role: 'PATIENT' } },
            { path: 'record/:id', name: 'RecordDetail', component: RecordDetail, meta: { role: 'PATIENT' } },

            // ===== 新建页面（完整功能） =====
            { path: 'checkin', name: 'Checkin', component: Checkin, meta: { role: 'PATIENT' } },
            { path: 'queue', name: 'QueueQuery', component: QueueQuery, meta: { role: 'PATIENT' } },
            { path: 'reports', name: 'Reports', component: Reports, meta: { role: 'PATIENT' } },
            { path: 'prescriptions', name: 'Prescriptions', component: Prescriptions, meta: { role: 'PATIENT' } },
            { path: 'lab-booking', name: 'LabBooking', component: LabBooking, meta: { role: 'PATIENT' } },
            { path: 'exam-booking', name: 'ExamBooking', component: ExamBooking, meta: { role: 'PATIENT' } },

            // ===== ✅ 新增：新创建的页面路由 =====
            { path: 'messages', name: 'Messages', component: Messages, meta: { role: 'PATIENT' } },
            { path: 'consult', name: 'Consult', component: Consult, meta: { role: 'PATIENT' } },
            { path: 'doctor-schedule', name: 'PatientDoctorSchedule', component: DoctorSchedule, meta: { role: 'PATIENT' } },
            { path: 'revisit', name: 'Revisit', component: Revisit, meta: { role: 'PATIENT' } },
            { path: 'physical-exam', name: 'PhysicalExam', component: PhysicalExam, meta: { role: 'PATIENT' } },
            { path: 'services', name: 'Services', component: Services, meta: { role: 'PATIENT' } },
            { path: 'guide', name: 'Guide', component: Guide, meta: { role: 'PATIENT' } },
            { path: 'customer-service', name: 'CustomerService', component: CustomerService, meta: { role: 'PATIENT' } },

            // ===== 旧路由兼容（重定向） =====
            { path: 'records', redirect: '/patient/appointments' },
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
            { path: '', name: 'DoctorDashboard', component: () => import('@/views/doctor/DoctorDashboard.vue'), meta: { role: 'DOCTOR' } },
            { path: 'visit', name: 'PatientVisit', component: () => import('@/views/doctor/PatientVisit.vue'), meta: { role: 'DOCTOR' } },
            { path: 'profile', name: 'DoctorProfile', component: () => import('@/views/doctor/DoctorProfile.vue'), meta: { role: 'DOCTOR' } },
            { path: 'schedule', name: 'DoctorSchedule', component: () => import('@/views/doctor/DoctorSchedule.vue'), meta: { role: 'DOCTOR' } },
            { path: 'ai-diagnosis', name: 'AIDiagnosis', component: () => import('@/views/doctor/AIDiagnosis.vue'), meta: { role: 'DOCTOR' } },
            { path: 'result-detail/:type/:id', name: 'ResultDetail', component: () => import('@/views/doctor/ResultDetail.vue'), meta: { role: 'DOCTOR' } },
            { path: 'ai-triage', name: 'AITriage', component: () => import('@/views/doctor/AITriage.vue'), meta: { role: 'DOCTOR' } },
        ]
    }
]

// ========== 管理员端路由 ==========
const adminRoutes: RouteRecordRaw[] = [
    {
        path: '/admin',
        component: () => import('@/views/layouts/AdminLayout.vue'),
        meta: { role: 'ADMIN' },
        children: [
            { path: '', name: 'AdminHome', component: () => import('@/views/admin/AdminHome.vue'), meta: { role: 'ADMIN' } },
            { path: 'schedule', name: 'AISchedule', component: () => import('@/views/admin/AISchedule.vue'), meta: { role: 'ADMIN' } },
            { path: 'finance', name: 'FinanceManage', component: () => import('@/views/admin/FinanceManage.vue'), meta: { role: 'ADMIN' } },
            { path: 'drug', name: 'DrugManage', component: () => import('@/views/admin/DrugManage.vue'), meta: { role: 'ADMIN' } },
            { path: 'staff/create', name: 'StaffCreate', component: () => import('@/views/admin/StaffCreate.vue'), meta: { role: 'ADMIN' } },
            { path: 'doctor-stats', name: 'DoctorStats', component: () => import('@/views/admin/DoctorStats.vue'), meta: { role: 'ADMIN' } },
            { path: 'dept-stats', name: 'DeptStats', component: () => import('@/views/admin/DeptStats.vue'), meta: { role: 'ADMIN' } },
        ]
    }
]

// ========== 根路径和404 ==========
const fallbackRoute: RouteRecordRaw = {
    path: '/:pathMatch(.*)*',
    redirect: '/patient/home'
}

// ========== 路由汇总 ==========
const routes: RouteRecordRaw[] = [
    ...independentRoutes,
    ...patientRoutes,
    ...doctorRoutes,
    ...adminRoutes,
    {
        path: '/',
        redirect: '/patient/home'
    },
    fallbackRoute
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// 使用路由守卫
router.beforeEach(checkAuth)

export default router