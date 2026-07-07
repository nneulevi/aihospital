// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import Components from 'unplugin-vue-components/vite'
import { VantResolver } from '@vant/auto-import-resolver'

export default defineConfig({
    cacheDir: path.resolve(__dirname, '../.tmp/vite-cache/frontend'),
    plugins: [
        vue(),
        Components({
            resolvers: [VantResolver()],
            dts: true, // 生成类型声明文件
        }),
    ],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src')
        }
    },
    css: {
        preprocessorOptions: {
            scss: {
                // 注意：Vite 6 中 additionalData 的写法
                additionalData: `@use "@/styles/variables.scss" as *;`
            }
        }
    },
    server: {
        host: '0.0.0.0',
        port: 5173,
        proxy: {
            '/api': {
                target: 'http://localhost:8092',  // 后端地址，根据实际情况修改
                changeOrigin: true,
            }
        }
    }
})
