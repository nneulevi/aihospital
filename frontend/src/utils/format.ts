// src/utils/format.ts
import dayjs from 'dayjs'

// 日期格式化
export const formatDate = (date?: string | Date, format: string = 'YYYY-MM-DD'): string => {
    if (!date) return ''
    return dayjs(date).format(format)
}

// 日期时间格式化
export const formatDateTime = (date?: string | Date, format: string = 'YYYY-MM-DD HH:mm'): string => {
    if (!date) return ''
    return dayjs(date).format(format)
}

// 金额格式化
export const formatMoney = (amount?: number, currency: string = '¥'): string => {
    if (amount === undefined || amount === null) return `${currency}0.00`
    return `${currency}${amount.toFixed(2)}`
}

// 手机号脱敏
export const maskPhone = (phone?: string): string => {
    if (!phone || phone.length !== 11) return phone || ''
    return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}

// 身份证脱敏
export const maskIdCard = (idCard?: string): string => {
    if (!idCard || idCard.length !== 18) return idCard || ''
    return idCard.replace(/(\d{4})\d{10}(\d{4})/, '$1**********$2')
}

// 姓名脱敏
export const maskName = (name?: string): string => {
    if (!name) return ''
    if (name.length === 2) {
        return name[0] + '*'
    }
    if (name.length > 2) {
        return name[0] + '*'.repeat(name.length - 2) + name[name.length - 1]
    }
    return name
}

// 根据身份证计算年龄
export const getAgeFromIdCard = (idCard?: string): number | null => {
    if (!idCard || idCard.length !== 18) return null
    const birthDate = idCard.substring(6, 14)
    const year = parseInt(birthDate.substring(0, 4))
    const month = parseInt(birthDate.substring(4, 6))
    const day = parseInt(birthDate.substring(6, 8))
    const today = new Date()
    let age = today.getFullYear() - year
    if (today.getMonth() + 1 < month || (today.getMonth() + 1 === month && today.getDate() < day)) {
        age--
    }
    return age
}

// 根据出生日期计算年龄
export const getAgeFromBirthdate = (birthdate?: string): number | null => {
    if (!birthdate) return null
    const today = new Date()
    const birth = new Date(birthdate)
    let age = today.getFullYear() - birth.getFullYear()
    if (today.getMonth() < birth.getMonth() ||
        (today.getMonth() === birth.getMonth() && today.getDate() < birth.getDate())) {
        age--
    }
    return age
}

// 午别转换
export const formatNoon = (noon?: string): string => {
    switch (noon) {
        case 'MORNING':
            return '上午'
        case 'AFTERNOON':
            return '下午'
        default:
            return noon || ''
    }
}

// 就诊状态转换
export const formatVisitState = (state?: string): string => {
    switch (state) {
        case 'REGISTERED':
            return '待就诊'
        case 'CONSULTING':
            return '就诊中'
        case 'FINISHED':
            return '已完成'
        case 'CANCELLED':
            return '已取消'
        default:
            return state || ''
    }
}

// 订单状态转换
export const formatOrderState = (state?: string): string => {
    switch (state) {
        case 'UNPAID':
            return '待缴费'
        case 'PAID':
            return '已缴费'
        case 'CANCELLED':
            return '已取消'
        default:
            return state || ''
    }
}

// 性别转换
export const formatGender = (gender?: string): string => {
    switch (gender) {
        case 'MALE':
            return '男'
        case 'FEMALE':
            return '女'
        default:
            return gender || ''
    }
}