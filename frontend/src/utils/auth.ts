// src/utils/auth.ts

const TOKEN_KEY = 'token'
const USER_KEY = 'user'

// ===== 统一用户信息类型（兼容员工和患者） =====
export interface UserInfo {
    // ===== 通用字段 =====
    realName?: string      // 患者端用
    realname?: string      // 员工端用，兼容大小写

    // ===== 患者端字段 =====
    patientId?: number
    caseNumber?: string
    isNewPatient?: boolean
    gender?: string
    age?: number
    phone?: string
    cardNumber?: string
    birthdate?: string
    homeAddress?: string
    relation?: string

    // ===== 员工端字段 =====
    employeeId?: number
    roleType?: string
    deptId?: number
    deptmentId?: number
    titleLevel?: string
    delmark?: boolean | string
    createTime?: string
    updateTime?: string
    enabled?: boolean

    // ===== 兼容其他字段 =====
    [key: string]: any
}

// ===== Token 操作 =====
export const getToken = (): string | null => {
    return localStorage.getItem(TOKEN_KEY)
}

export const setToken = (token: string): void => {
    localStorage.setItem(TOKEN_KEY, token)
}

export const removeToken = (): void => {
    localStorage.removeItem(TOKEN_KEY)
}

// ===== 用户信息操作 =====
export const getUser = (): UserInfo | null => {
    const userStr = localStorage.getItem(USER_KEY)
    if (!userStr) return null
    try {
        return JSON.parse(userStr)
    } catch {
        return null
    }
}

export const setUser = (user: UserInfo): void => {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export const removeUser = (): void => {
    localStorage.removeItem(USER_KEY)
}

// ===== 角色判断 =====
export const getUserRole = (): string | null => {
    const user = getUser()
    if (user?.patientId) return 'PATIENT'
    return user?.roleType || null
}

export const isPatient = (): boolean => {
    return getUserRole() === 'PATIENT'
}

export const isDoctor = (): boolean => {
    return getUserRole() === 'DOCTOR'
}

export const isAdmin = (): boolean => {
    return getUserRole() === 'ADMIN'
}

// ===== ID 获取 =====
export const getPatientId = (): number | null => {
    const user = getUser()
    return user?.patientId || null
}

export const getDoctorId = (): number | null => {
    const user = getUser()
    return user?.employeeId || null
}

export const getUserId = (): number | null => {
    const user = getUser()
    return user?.patientId || user?.employeeId || null
}

// ===== 用户名获取（兼容大小写） =====
export const getUserName = (): string => {
    const user = getUser()
    return user?.realName || user?.realname || ''
}

// ===== 设置患者ID（切换就诊人） =====
export const setPatientId = (patientId: number): void => {
    const user = getUser()
    if (user) {
        user.patientId = patientId
        setUser(user)
    }
}

// ===== 更新用户信息 =====
export const updateUser = (partial: Partial<UserInfo>): void => {
    const user = getUser()
    if (user) {
        Object.assign(user, partial)
        setUser(user)
    }
}

// ===== 退出登录 =====
export const logout = (): void => {
    removeToken()
    removeUser()
}