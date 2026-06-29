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

    const login = (newToken: string, user: UserInfo) => {
        token.value = newToken
        userInfo.value = user
        setToken(newToken)
        setUser(user)
    }

    const logout = () => {
        token.value = null
        userInfo.value = null
        removeToken()
        removeUser()
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
        logout
    }
})