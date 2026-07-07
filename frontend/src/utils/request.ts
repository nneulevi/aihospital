// src/utils/request.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { getToken, removeToken, removeUser } from './auth'
import { showToast } from 'vant'
import { ElMessage } from 'element-plus'

const isMobile = () => {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
}

const showMessage = (message: string, type: 'success' | 'error' | 'warning' = 'error') => {
    if (isMobile()) {
        showToast(message)
    } else {
        ElMessage[type](message)
    }
}

const createInstance = (baseURL: string = '/api'): AxiosInstance => {
    const instance = axios.create({
        baseURL,
        timeout: 30000,
        headers: {
            'Content-Type': 'application/json'
        }
    })

    instance.interceptors.request.use(
        (config: InternalAxiosRequestConfig) => {
            const token = getToken()
            if (token) {
                config.headers.Authorization = `Bearer ${token}`
            }
            return config
        },
        (error) => Promise.reject(error)
    )

    instance.interceptors.response.use(
        (response: AxiosResponse) => response.data,
        (error) => {
            let userMessage = ''
            if (error.response) {
                const { status, data } = error.response

                switch (status) {
                    case 401:
                        removeToken()
                        removeUser()
                        userMessage = '登录已过期，请重新登录'
                        showMessage(userMessage)
                        window.location.href = window.location.pathname.startsWith('/admin') ||
                            window.location.pathname.startsWith('/doctor') ||
                            window.location.pathname.startsWith('/medical-tech') ||
                            window.location.pathname.startsWith('/drugstore')
                            ? '/auth/login'
                            : '/patient/login'
                        break
                    case 403:
                        userMessage = '没有权限访问该资源'
                        showMessage(userMessage)
                        break
                    case 404:
                        userMessage = '请求的资源不存在'
                        showMessage(userMessage)
                        break
                    case 500:
                        userMessage = data?.message || '服务器内部错误'
                        showMessage(userMessage)
                        break
                    default:
                        userMessage = data?.message || '请求失败，请稍后重试'
                        showMessage(userMessage)
                }
            } else if (error.request) {
                userMessage = '网络连接失败，请检查网络'
                showMessage(userMessage)
            } else {
                userMessage = error.message || '请求失败'
                showMessage(userMessage)
            }

            if (userMessage) {
                error.userMessage = userMessage
            }
            return Promise.reject(error)
        }
    )

    return instance
}

export const outpatientInstance = createInstance('/api')
export const aiInstance = createInstance('/api')
export const drugstoreInstance = createInstance('/api')

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
