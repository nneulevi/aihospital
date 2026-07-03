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

    // ID - 兼容多种字段名
    const userId = computed(() => {
        return userInfo.value?.patientId || userInfo.value?.employeeId || null
    })

    const doctorId = computed(() => {
        // 兼容 employeeId 和 id 两种字段
        const id = userInfo.value?.employeeId || userInfo.value?.id || null
        console.log('[userStore] doctorId computed:', id, 'userInfo:', userInfo.value)
        return id
    })

    const patientId = computed(() => userInfo.value?.patientId || null)

    // ===== 登录 =====
    const login = (newToken: string, user: UserInfo) => {
        console.log('[userStore] login called with:', { newToken, user })
        token.value = newToken
        userInfo.value = user
        setToken(newToken)
        setUser(user)
        console.log('[userStore] after login - doctorId:', doctorId.value)
    }

    // ===== 退出登录 =====
    const logout = () => {
        token.value = null
        userInfo.value = null
        removeToken()
        removeUser()
    }

    // ===== 切换就诊人 =====
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

    // ===== 更新用户信息 =====
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