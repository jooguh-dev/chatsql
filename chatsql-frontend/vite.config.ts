import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3002,  // 改为3002以匹配实际运行端口
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        // 确保cookie正确传递
        cookieDomainRewrite: '',
        cookiePathRewrite: '/',
      },
    },
  },
})
