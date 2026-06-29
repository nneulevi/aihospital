// src/utils/auth.ts

const TOKEN_KEY = 'token'
const USER_KEY = 'user'

// 统一用户信息类型（兼容员工和患者）
export interface UserInfo {
    // 通用
    realName?: string
    realname?: string  // 兼容大小写
    phone?: string

    // 员工字段
    employeeId?: number
    roleType?: string
    deptId?: number

    // 患者字段
    patientId?: number
    caseNumber?: string
    isNewPatient?: boolean
}

// 获取 token
export const getToken = (): string | null => {
    return localStorage.getItem(TOKEN_KEY)
}

// 设置 token
export const setToken = (token: string): void => {
    localStorage.setItem(TOKEN_KEY, token)
}

// 移除 token
export const removeToken = (): void => {
    localStorage.removeItem(TOKEN_KEY)
}

// 获取用户信息
export const getUser = (): UserInfo | null => {
    const userStr = localStorage.getItem(USER_KEY)
    if (!userStr) return null
    try {
        return JSON.parse(userStr)
    } catch {
        return null
    }
}

// 设置用户信息
export const setUser = (user: UserInfo): void => {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
}

// 移除用户信息
export const removeUser = (): void => {
    localStorage.removeItem(USER_KEY)
}

// 获取用户角色（兼容患者无 roleType）
export const getUserRole = (): string | null => {
    const user = getUser()
    if (user?.patientId) return 'PATIENT'
    return user?.roleType || null
}

// 获取患者ID
export const getPatientId = (): number | null => {
    const user = getUser()
    return user?.patientId || null
}

// 设置患者ID
export const setPatientId = (patientId: number): void => {
    const user = getUser()
    if (user) {
        user.patientId = patientId
        setUser(user)
    }
}

// 获取医生ID
export const getDoctorId = (): number | null => {
    const user = getUser()
    return user?.employeeId || null
}

// 获取用户名（兼容大小写）
export const getUserName = (): string => {
    const user = getUser()
    return user?.realName || user?.realname || ''
}

// 退出登录
export const logout = (): void => {
    removeToken()
    removeUser()
}
