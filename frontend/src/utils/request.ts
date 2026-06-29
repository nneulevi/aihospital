// src/utils/request.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { getToken, removeToken, removeUser } from './auth'
import { showToast } from 'vant'
import { ElMessage } from 'element-plus'

// 判断是否为移动端环境（用于选择不同的提示组件）
const isMobile = () => {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
}

// 显示提示信息
const showMessage = (message: string, type: 'success' | 'error' | 'warning' = 'error') => {
    if (isMobile()) {
        showToast(message)
    } else {
        ElMessage[type](message)
    }
}

// 创建 axios 实例
const createInstance = (baseURL: string = '/api'): AxiosInstance => {
    const instance = axios.create({
        baseURL,
        timeout: 30000,
        headers: {
            'Content-Type': 'application/json'
        }
    })

    // 请求拦截�?
    instance.interceptors.request.use(
        (config: InternalAxiosRequestConfig) => {
            const token = getToken()
            if (token) {
                config.headers.Authorization = `Bearer ${token}`
            }
            return config
        },
        (error) => {
            return Promise.reject(error)
        }
    )

    // 响应拦截�?
    instance.interceptors.response.use(
        (response: AxiosResponse) => {
            // 直接返回 data
            return response.data
        },
        (error) => {
            if (error.response) {
                const { status, data } = error.response

                switch (status) {
                    case 401:
                        // 未授权，清除登录信息
                        removeToken()
                        removeUser()
                        showMessage('登录已过期，请重新登�?)
                        // 跳转到登录页
                        if (!isMobile()) {
                            window.location.href = '/patient/login'
                        } else {
                            window.location.href = '/patient/login'
                        }
                        break
                    case 403:
                        showMessage('没有权限访问该资�?)
                        break
                    case 404:
                        showMessage('请求的资源不存在')
                        break
                    case 500:
                        showMessage(data?.message || '服务器内部错�?)
                        break
                    default:
                        showMessage(data?.message || '请求失败，请稍后重试')
                }
            } else if (error.request) {
                showMessage('网络连接失败，请检查网�?)
            } else {
                showMessage(error.message || '请求失败')
            }

            return Promise.reject(error)
        }
    )

    return instance
}

// 各模块的 API 实例
export const outpatientInstance = createInstance('/api')
export const aiInstance = createInstance('/api')
export const drugstoreInstance = createInstance('/api')

// 通用请求方法
export const request = {
    get: <T = any>(url: string, params?: any, config?: AxiosRequestConfig): Promise<T> => {
        return outpatientInstance.get(url, { params, ...config })
    },
    post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
        return outpatientInstance.post(url, data, config)
    },
    put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
        return outpatientInstance.put(url, data, config)
    },
    delete: <T = any>(url: string, params?: any, config?: AxiosRequestConfig): Promise<T> => {
        return outpatientInstance.delete(url, { params, ...config })
    }
}

export default outpatientInstance