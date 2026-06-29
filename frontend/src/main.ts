// src/main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import axios from 'axios'
import App from './App.vue'
import router from './router'

// Element Plus（PC端）
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// Vant（移动端）- 按需加载由 unplugin-vue-components 处理
import 'vant/lib/index.css'

// 全局样式
import './styles/main.scss'

// 全局 axios 拦截器（Orval 生成的代码用 axios.default，会自动走这里）
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

axios.interceptors.response.use(
    (response) => response.data,
    (error) => Promise.reject(error)
)

const app = createApp(App)

// 注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')