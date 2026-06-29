// src/utils/instance.mjs
import axios from 'axios';

const hisAxios = axios.create({
    baseURL: '/api',
    timeout: 30000,
    headers: { 'Content-Type': 'application/json' }
});

hisAxios.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

hisAxios.interceptors.response.use(
    (response) => response.data,
    (error) => Promise.reject(error)
);

export const hisInstance = hisAxios;