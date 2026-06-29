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
            if (error.response) {
                const { status, data } = error.response

                switch (status) {
                    case 401:
                        removeToken()
                        removeUser()
                        showMessage('登录已过期，请重新登录')
                        window.location.href = window.location.pathname.startsWith('/admin') ||
                            window.location.pathname.startsWith('/doctor') ||
                            window.location.pathname.startsWith('/medical-tech') ||
                            window.location.pathname.startsWith('/drugstore')
                            ? '/auth/login'
                            : '/patient/login'
                        break
                    case 403:
                        showMessage('没有权限访问该资源')
                        break
                    case 404:
                        showMessage('请求的资源不存在')
                        break
                    case 500:
                        showMessage(data?.message || '服务器内部错误')
                        break
                    default:
                        showMessage(data?.message || '请求失败，请稍后重试')
                }
            } else if (error.request) {
                showMessage('网络连接失败，请检查网络')
            } else {
                showMessage(error.message || '请求失败')
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
