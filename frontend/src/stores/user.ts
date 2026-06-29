// src/stores/user.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
    getToken, setToken, removeToken,
    getUser, setUser, removeUser,
    type UserInfo
} from '@/utils/auth'

export const useUserStore = defineStore('user', () => {
    const token = ref<string | null>(getToken())
    const userInfo = ref<UserInfo | null>(getUser())

    const isLoggedIn = computed(() => !!token.value && !!userInfo.value)

    // 角色判断
    const userRole = computed(() => {
        if (userInfo.value?.patientId) return 'PATIENT'
        return userInfo.value?.roleType || null
    })

    const isPatient = computed(() => userRole.value === 'PATIENT')
    const isDoctor = computed(() => userRole.value === 'DOCTOR')
    const isAdmin = computed(() => userRole.value === 'ADMIN')

    // 用户名
    const userName = computed(() => {
        return userInfo.value?.realName || userInfo.value?.realname || ''
    })

    // ID
    const userId = computed(() => {
        return userInfo.value?.patientId || userInfo.value?.employeeId || null
    })
    const doctorId = computed(() => userInfo.value?.employeeId || null)
    const patientId = computed(() => userInfo.value?.patientId || null)

    // ===== 登录 =====
    const login = (newToken: string, user: UserInfo) => {
        token.value = newToken
        userInfo.value = user
        setToken(newToken)
        setUser(user)
    }

    // ===== 退出登录 =====
    const logout = () => {
        token.value = null
        userInfo.value = null
        removeToken()
        removeUser()
    }

    // ===== 切换就诊人（更新当前患者信息） =====
    const setCurrentPatient = (patient: {
        patientId: number
        realName?: string
        caseNumber?: string
        gender?: string
        age?: number
        phone?: string
        cardNumber?: string
        birthdate?: string
        homeAddress?: string
        relation?: string
    }) => {
        if (userInfo.value) {
            userInfo.value = {
                ...userInfo.value,
                patientId: patient.patientId,
                realName: patient.realName || userInfo.value.realName,
                caseNumber: patient.caseNumber || userInfo.value.caseNumber,
                gender: patient.gender || userInfo.value.gender,
                age: patient.age !== undefined ? patient.age : userInfo.value.age,
                phone: patient.phone || userInfo.value.phone,
                cardNumber: patient.cardNumber || userInfo.value.cardNumber,
                birthdate: patient.birthdate || userInfo.value.birthdate,
                homeAddress: patient.homeAddress || userInfo.value.homeAddress,
                relation: patient.relation || userInfo.value.relation,
            }
            setUser(userInfo.value)
        }
    }

    // ===== 更新用户信息（用于补充从接口获取的额外字段） =====
    const updateUserInfo = (partial: Partial<UserInfo>) => {
        if (userInfo.value) {
            userInfo.value = {
                ...userInfo.value,
                ...partial
            }
            setUser(userInfo.value)
        }
    }

    return {
        token,
        userInfo,
        isLoggedIn,
        userRole,
        isPatient,
        isDoctor,
        isAdmin,
        userName,
        userId,
        doctorId,
        patientId,
        login,
        logout,
        setCurrentPatient,
        updateUserInfo
    }
})